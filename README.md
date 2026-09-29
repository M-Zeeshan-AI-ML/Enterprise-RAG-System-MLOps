# Enterprise RAG & MLOps System

Production-oriented RAG API for private PDF knowledge bases.

## Core Capabilities
This version includes:
- PDF ingestion + semantic retrieval
- Persistent ChromaDB
- Grounded LLM answers + source citations
- JWT authentication
- Structured request/event logging
- Request IDs and latency tracking
- Automated tests with pytest
- GitHub Actions CI
- Retrieval evaluation scaffold with Recall@5
- Docker + Docker Compose
- Environment-based configuration

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

Copy `.env.example` to `.env` and configure the required API key, JWT secret, username and password.

Never commit `.env` or any API keys to GitHub.

Run:
```bash
uvicorn app.main:app --reload
```

Swagger: http://localhost:8000/docs

## Authentication

Call `POST /auth/login`:

```json
{"username":"demo","password":"your-demo-password"}
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

## Security

Never commit `.env`, API keys, private PDFs, Chroma data or production credentials.

## Next Production Steps

- Multi-tenant isolation
- External identity provider
- PostgreSQL metadata
- Object storage
- Managed/distributed vector database
- OpenTelemetry + Prometheus/Grafana
- RAG evaluation regression gates
- Model/version tracking
- Container image CI/CD
- Cloud deployment
- Rate limiting and API gateway
