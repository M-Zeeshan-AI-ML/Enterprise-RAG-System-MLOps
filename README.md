# Enterprise RAG & MLOps System

Production-oriented RAG API for private PDF knowledge bases.

## Architecture

Client -> FastAPI -> JWT Auth
                  -> PDF -> Chunking -> Embeddings -> ChromaDB
                  -> Query -> Retrieval -> Context -> LLM -> Answer + Sources
                  -> Logging / Health
GitHub -> GitHub Actions -> Tests

## Setup

```bash
python -m venv .venv
```

Windows:
```powershell
.venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set your API key, JWT secret, username and password.

Run:
```bash
uvicorn app.main:app --reload
```

Swagger: http://localhost:8000/docs

## Authentication

Call `POST /auth/login`:

```json
{"username":"admin","password":"your-demo-password"}
```

Use the returned Bearer token in Swagger.

Protected:
- `POST /documents/upload`
- `POST /query`

The included JWT login is a portfolio/demo authentication layer. Production systems should use an identity provider, secure secret management and proper user/tenant storage.

## RAG Evaluation

Edit `evaluation/dataset.json` with real questions and expected source pages, then run:

```bash
python evaluation/evaluate_retrieval.py
```

It reports Recall@5. Extend this with Precision@K, MRR, context relevance, faithfulness, citation accuracy, latency and cost.

## CI

`.github/workflows/ci.yml` runs pytest on pushes and pull requests to `main`.

## Docker

```bash
docker compose up --build
```

Chroma persistence is mounted at `./data/chroma`.

## Project Structure

```text
enterprise-rag/
├── .github/workflows/ci.yml
├── app/
│   ├── auth.py
│   ├── config.py
│   ├── logging_config.py
│   ├── main.py
│   ├── schemas.py
│   └── rag/pipeline.py
├── evaluation/
│   ├── dataset.json
│   └── evaluate_retrieval.py
├── tests/
│   ├── test_auth.py
│   └── test_health.py
├── data/chroma/
├── uploads/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```


- Rate limiting and API gateway
