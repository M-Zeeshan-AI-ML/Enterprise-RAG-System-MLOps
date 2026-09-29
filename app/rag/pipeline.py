from pathlib import Path
from typing import Any
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import CHROMA_DIR, COLLECTION_NAME, OPENAI_EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP

class RAGPipeline:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self.vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=CHROMA_DIR,
        )

    def ingest_pdf(self, file_path: str, document_name: str) -> dict[str, Any]:
        documents = PyPDFLoader(file_path).load()
        if not documents:
            raise ValueError("No readable content found in PDF.")
        for doc in documents:
            doc.metadata["document_name"] = document_name
        chunks = self.text_splitter.split_documents(documents)
        if not chunks:
            raise ValueError("PDF could not be split into text chunks.")
        ids = []
        for index, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = index
            page = chunk.metadata.get("page", 0)
            ids.append(f"{Path(document_name).stem}-page-{page}-chunk-{index}")
        self.vectorstore.add_documents(documents=chunks, ids=ids)
        return {"document_name": document_name, "pages": len(documents), "chunks": len(chunks)}

    def retrieve(self, query: str, k: int = 5):
        return self.vectorstore.similarity_search(query, k=k)
