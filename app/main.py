import logging, os, tempfile, time, uuid
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from langchain_openai import ChatOpenAI
from app.auth import create_access_token, get_current_user, verify_credentials
from app.config import OPENAI_API_KEY, OPENAI_CHAT_MODEL, TOP_K, MAX_FILE_SIZE_MB
from app.logging_config import configure_logging
from app.rag.pipeline import RAGPipeline
from app.schemas import LoginRequest, QueryRequest, QueryResponse, Source, TokenResponse

configure_logging()
logger = logging.getLogger("enterprise_rag")
app = FastAPI(title="Enterprise RAG API", version="2.0.0",
              description="Authenticated, observable RAG API with FastAPI, LangChain, ChromaDB and OpenAI.")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not configured.")

rag_pipeline = RAGPipeline()
llm = ChatOpenAI(model=OPENAI_CHAT_MODEL, temperature=0)

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()
    try:
        response = await call_next(request)
        elapsed = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info("request_id=%s method=%s path=%s status=%s latency_ms=%s",
                    request_id, request.method, request.url.path, response.status_code, elapsed)
        return response
    except Exception:
        logger.exception("request_id=%s method=%s path=%s", request_id, request.method, request.url.path)
        raise

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception("request_id=%s unhandled_exception", request_id)
    return JSONResponse(status_code=500, content={"detail": "Internal server error.", "request_id": request_id})

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "enterprise-rag-api", "version": "2.0.0"}

@app.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest):
    if not verify_credentials(request.username, request.password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return TokenResponse(access_token=create_access_token(request.username))

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...), current_user: str = Depends(get_current_user)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    max_size = MAX_FILE_SIZE_MB * 1024 * 1024
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_path, size = temp_file.name, 0
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_size:
                os.unlink(temp_path)
                raise HTTPException(status_code=413, detail=f"File exceeds {MAX_FILE_SIZE_MB} MB limit.")
            temp_file.write(chunk)
    try:
        start = time.perf_counter()
        result = rag_pipeline.ingest_pdf(temp_path, file.filename or "document.pdf")
        logger.info("user=%s event=document_ingested document=%s chunks=%s latency_ms=%s",
                    current_user, result["document_name"], result["chunks"],
                    round((time.perf_counter()-start)*1000, 2))
        return {"message": "Document indexed successfully.", **result}
    except Exception:
        logger.exception("user=%s document_ingestion_failed", current_user)
        raise HTTPException(status_code=500, detail="Document processing failed.")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/query", response_model=QueryResponse)
def query_documents(request: QueryRequest, current_user: str = Depends(get_current_user)):
    start = time.perf_counter()
    try:
        documents = rag_pipeline.retrieve(request.question, request.top_k)
        if not documents:
            return QueryResponse(answer="I could not find relevant information in the uploaded documents.",
                                 sources=[], retrieval_count=0)
        context_parts, sources = [], []
        for doc in documents:
            md = doc.metadata
            name, page, chunk_id = md.get("document_name", "Unknown document"), int(md.get("page", 0)), int(md.get("chunk_id", 0))
            context_parts.append(f"SOURCE:\nDocument: {name}\nPage: {page+1}\n\nContent:\n{doc.page_content}")
            sources.append(Source(document=name, page=page+1, chunk_id=chunk_id, content=doc.page_content[:500]))
        prompt = f"""You are an enterprise document question-answering assistant.
Answer using ONLY the supplied document context.
Do not invent facts or use outside knowledge. If the answer is not contained in the context, say it was not found.
Give a concise useful answer and mention relevant source documents/pages.

DOCUMENT CONTEXT:
{chr(10).join(context_parts)}

USER QUESTION:
{request.question}
"""
        response = llm.invoke(prompt)
        logger.info("user=%s event=rag_query retrieved=%s latency_ms=%s",
                    current_user, len(documents), round((time.perf_counter()-start)*1000, 2))
        return QueryResponse(answer=response.content, sources=sources, retrieval_count=len(documents))
    except Exception:
        logger.exception("user=%s query_failed", current_user)
        raise HTTPException(status_code=500, detail="Query failed.")
