# ElasticCX Backend

Elasticsearch ingestion pipeline + review scraper for the ElasticCX hackathon project.

## Dev Commands

```bash
# Start API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Create ES indices (run once after setting up .env)
python scripts/create_indices.py

# Run review scraper
python -m scraper.runner

# Install deps
pip install -r requirements.txt
playwright install chromium
```

## Architecture

- `app/` — FastAPI server
- `app/indices/` — Elasticsearch index mappings (3 indices)
- `app/services/` — chunker, embedder (OpenAI), ES client, ingest orchestration
- `app/routers/` — POST /ingest/* endpoints
- `app/models/` — Pydantic request/response models
- `scraper/` — Playwright scrapers for Trustpilot, G2, Capterra
- `scripts/` — one-off operational scripts

## Elasticsearch Indices

- `company-knowledge-index` — internal docs, FAQs, PDFs
- `market-intelligence-index` — competitor reviews from Trustpilot/G2/Capterra
- `customer-history-index` — support emails, call transcripts, chat messages

All indices use `int8_hnsw` dense vectors (1536 dims, OpenAI text-embedding-3-small) + BM25 text fields. RRF hybrid search is supported via the ES 8.9+ `retriever` API.

## Env Vars

Copy `.env.example` → `.env` and fill in:
- `ES_CLOUD_ID` — from Elastic Cloud console
- `ES_API_KEY` — from Elastic Cloud console
- `OPENAI_API_KEY` — for embeddings
