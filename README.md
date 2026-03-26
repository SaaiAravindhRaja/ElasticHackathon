# Auralytics

**AI-powered Customer Experience & Revenue Intelligence Suite**

Auralytics unifies support, sales, and product intelligence into a single platform built on Elasticsearch. It ingests unstructured data from every customer touchpoint — emails, call transcripts, reviews, and internal docs — and powers four AI-driven products through hybrid RRF search (BM25 + kNN vector) over Elastic Cloud.

---

## Products

| Product | Audience | What it does |
|---|---|---|
| **Support Chatbot** | Customer-facing | RAG-powered bot that answers support queries, surfaces upsell signals, and escalates to a human agent |
| **Pitch Assistant** | Sales reps | Live co-pilot during sales calls — streams transcription, surfaces competitor weaknesses, and suggests rebuttals in real time |
| **Agent Console** | Support agents | Real-time guidance during live calls — instant troubleshooting scripts, step-by-step action plans, and cited internal docs |
| **Recommendations Dashboard** | Product & leadership | Automated gap analysis from aggregated customer feedback — churn signals, feature requests, and competitor vulnerability reports |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Next.js UI                           │
│  Support Chatbot · Pitch Assistant · Agent Console · Dashboard│
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / WebSocket
┌────────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend (v3)                       │
│  /ingest  /search  /ai/query  /analytics  /alerts  /agent   │
└──────┬──────────────────┬──────────────────┬────────────────┘
       │                  │                  │
┌──────▼──────┐  ┌────────▼──────┐  ┌───────▼────────┐
│  Elastic    │  │  OpenAI       │  │  AWS Bedrock   │
│  Cloud      │  │  Embeddings   │  │  Nova Lite     │
│  (3 indices)│  │  text-3-small │  │  (agent)       │
└─────────────┘  └───────────────┘  └────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────┐
│                   Playwright Scrapers                        │
│       Trustpilot · G2 · Capterra · Zendesk Help Center      │
└─────────────────────────────────────────────────────────────┘
```

### Elasticsearch Indices

All indices use `int8_hnsw` dense vectors (1536 dims) with BM25 text fields. Hybrid search is performed via the ES 8.9+ `retriever` API with RRF fusion.

| Index | Contents |
|---|---|
| `company-knowledge-index` | Internal docs, FAQs, PDFs |
| `market-intelligence-index` | Competitor reviews from Trustpilot, G2, Capterra |
| `customer-history-index` | Support emails, call transcripts, chat messages |

---

## Tech Stack

- **Frontend** — Next.js 14, TypeScript, Tailwind CSS
- **Backend** — FastAPI, Python, async Elasticsearch client
- **Search** — Elastic Cloud (ES 8.9+), RRF hybrid retrieval
- **Embeddings** — OpenAI `text-embedding-3-small` (1536 dims)
- **AI / Agent** — AWS Bedrock Nova Lite, RAG via `POST /ai/query`
- **Live Transcription** — Whisper via WebSocket (`transcribe-live.mjs`)
- **Scrapers** — Playwright (Trustpilot, G2, Capterra, Zendesk Help Center)

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- An Elastic Cloud deployment (ES 8.9+)
- OpenAI API key

### 1. Clone & install dependencies

```bash
git clone https://github.com/SaaiAravindhRaja/CX.git
cd CX

# Python dependencies
pip install -r requirements.txt
playwright install chromium

# Node dependencies
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in the required values:

| Variable | Description |
|---|---|
| `ES_CLOUD_ID` | From the Elastic Cloud console |
| `ES_API_KEY` | From the Elastic Cloud console |
| `OPENAI_API_KEY` | For embeddings (`text-embedding-3-small`) |

### 3. Create Elasticsearch indices

```bash
python scripts/create_indices.py
```

### 4. Start the backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at `http://localhost:8000/docs`.

### 5. Start the frontend

```bash
npm run dev
```

Open `http://localhost:3000`.
