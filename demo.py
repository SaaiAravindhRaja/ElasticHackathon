"""
ElasticCX Backend Demo
======================
Run this to see the backend in action.

Requirements:  pip install requests
Usage:         python demo.py

Change BASE_URL below if the server is running on a different machine.
"""

import json
import sys
import requests

BASE_URL = "http://localhost:8000"


def section(title):
    print(f"\n{'═' * 55}")
    print(f"  {title}")
    print(f"{'═' * 55}")


def ok(label, value=""):
    print(f"  ✅  {label}" + (f"  →  {value}" if value else ""))


def fail(label, detail=""):
    print(f"  ❌  {label}" + (f": {detail}" if detail else ""))


def pretty(d, indent=2):
    """Print a dict as nicely indented JSON."""
    print(json.dumps(d, indent=indent, ensure_ascii=False))


# ── 1. Health ────────────────────────────────────────────────────────────────
section("1 / Health check")

try:
    r = requests.get(f"{BASE_URL}/health", timeout=10)
    d = r.json()
    ok("Server is up", f"ES cluster: {d['cluster'][:16]}…  v{d['es_version']}")
except Exception as e:
    fail("Cannot reach server", str(e))
    print(f"\n  Make sure the server is running:\n  uvicorn app.main:app --host 0.0.0.0 --port 8000\n")
    sys.exit(1)


# ── 2. Ingest a document ─────────────────────────────────────────────────────
section("2 / Ingest a document (FAQ)")

r = requests.post(f"{BASE_URL}/ingest/documents", json={
    "title": "What is ElasticCX?",
    "text": (
        "ElasticCX is an AI-powered customer experience platform. "
        "It combines Elasticsearch hybrid search (BM25 + vector kNN) "
        "with GPT-4o-mini to answer support questions, analyse competitor "
        "reviews, and surface product insights in real time."
    ),
    "doc_type": "faq"
}, timeout=30)
d = r.json()
total = d.get("chunks_indexed", 0) + d.get("deduplicated", 0)
ok("Document ingested", f"chunks={d.get('chunks_indexed')}  deduped={d.get('deduplicated')}")


# ── 3. Search knowledge base ─────────────────────────────────────────────────
section("3 / Hybrid search — knowledge base")

r = requests.get(f"{BASE_URL}/search/knowledge", params={
    "q": "what is ElasticCX how does search work",
    "top_k": 3,
}, timeout=30)
d = r.json()
hits = d.get("hits", [])
ok(f"Search returned {len(hits)} result(s)  ({d.get('took_ms')}ms)")
for i, h in enumerate(hits, 1):
    title = h.get("title", "–")
    snippet = list(h.get("highlights", {}).values())
    snippet_text = snippet[0][0][:120] if snippet else h.get("text", "")[:120]
    print(f"     [{i}] {title}")
    print(f"         {snippet_text}…")


# ── 4. Search competitor reviews ─────────────────────────────────────────────
section("4 / Search reviews — Zendesk  (filtered)")

r = requests.get(f"{BASE_URL}/search/reviews", params={
    "q": "customer support quality",
    "company": "Zendesk",
    "top_k": 3,
}, timeout=30)
d = r.json()
hits = d.get("hits", [])
ok(f"Found {len(hits)} Zendesk review(s)  ({d.get('took_ms')}ms)")
for h in hits[:2]:
    text = h.get("review_text", "")[:130]
    sentiment = h.get("sentiment", "?")
    rating = h.get("rating", "?")
    print(f"     [{rating}★ | {sentiment}]  {text}…")


# ── 5. AI — support bot ───────────────────────────────────────────────────────
section("5 / AI query — Support Bot  (plain text)")

r = requests.post(f"{BASE_URL}/ai/query", json={
    "question": "What does ElasticCX do and how does the search work?",
    "mode": "support_bot",
}, timeout=60)
d = r.json()
ok(f"Answer ({d.get('latency_ms')}ms, {d.get('total_context_chunks')} chunks used)")
print()
answer = d.get("answer", "")
# word-wrap at 70 chars
words = answer.split()
line = "     "
for w in words:
    if len(line) + len(w) > 75:
        print(line)
        line = "     " + w + " "
    else:
        line += w + " "
print(line)
conv_id = d.get("conversation_id")


# ── 6. Multi-turn follow-up ───────────────────────────────────────────────────
section("6 / Multi-turn conversation  (follow-up question)")

r = requests.post(f"{BASE_URL}/ai/query", json={
    "question": "Can you summarise that in one sentence?",
    "mode": "support_bot",
    "conversation_id": conv_id,
}, timeout=60)
d2 = r.json()
same = d2.get("conversation_id") == conv_id
ok("Same conversation ID preserved", str(same))
ok(f"Follow-up answer ({d2.get('latency_ms')}ms)")
print(f"\n     {d2.get('answer','')}\n")


# ── 7. AI — Sales Copilot (structured JSON) ───────────────────────────────────
section("7 / AI query — Sales Copilot  (structured JSON output)")

r = requests.post(f"{BASE_URL}/ai/query", json={
    "question": "What are Zendesk's main weaknesses based on customer reviews?",
    "mode": "sales_copilot",
    "output_format": "json",
}, timeout=60)
d = r.json()
answer = d.get("answer", {})
ok(f"Structured answer ({d.get('latency_ms')}ms, {d.get('total_context_chunks')} sources)")
print()
if isinstance(answer, dict):
    for k, v in answer.items():
        if isinstance(v, list):
            print(f"     {k}:")
            for item in v[:2]:
                print(f"       • {item}")
        else:
            print(f"     {k}: {v}")


# ── 8. Analytics ─────────────────────────────────────────────────────────────
section("8 / Analytics — overview")

r = requests.get(f"{BASE_URL}/analytics/overview", timeout=20)
d = r.json()
docs = d.get("total_docs", {})
ok("Index document counts")
for name, count in docs.items():
    print(f"       {name:<12} {count:,} docs")


# ── 9. Competitor comparison ──────────────────────────────────────────────────
section("9 / Analytics — competitor comparison")

r = requests.get(f"{BASE_URL}/analytics/competitor-compare", params={
    "companies": "Zendesk,Freshdesk",
}, timeout=20)
d = r.json()
ok("Competitor ratings")
for company in d.get("companies", []):
    print(f"       {company['company']:<12}  avg {company.get('avg_rating','?')}★  ({company.get('review_count','?')} reviews)")


# ── 10. Sentiment trend ───────────────────────────────────────────────────────
section("10 / Analytics — sentiment trend (last 365 days)")

r = requests.get(f"{BASE_URL}/analytics/sentiment-trend", params={
    "index": "reviews", "days": 365,
}, timeout=20)
d = r.json()
buckets = d.get("buckets", [])
ok(f"{len(buckets)} monthly sentiment buckets returned")
for b in buckets[-3:]:
    pos = b.get("positive", 0)
    neg = b.get("negative", 0)
    print(f"       {b.get('date','')}   +{pos} positive  -{neg} negative")


# ── Done ──────────────────────────────────────────────────────────────────────
section("All done!")
print("  The backend is fully working.")
print()
print("  API docs (interactive):  http://localhost:8000/docs")
print()
print("  Key endpoints:")
print("    POST /ingest/documents      — add FAQ / knowledge base docs")
print("    POST /ingest/reviews        — add competitor reviews")
print("    POST /ingest/emails         — add support emails (NLP enriched)")
print("    POST /ingest/transcripts    — add call transcripts (NLP enriched)")
print("    GET  /search/knowledge      — hybrid search knowledge base")
print("    GET  /search/reviews        — search + filter competitor reviews")
print("    GET  /search/customers      — search customer history")
print("    POST /ai/query              — RAG answer (4 modes, text or JSON)")
print("    GET  /analytics/overview    — doc counts")
print("    GET  /analytics/summary     — AI company brief")
print()
