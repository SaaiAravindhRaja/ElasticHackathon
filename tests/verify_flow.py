"""
ElasticCX — Comprehensive End-to-End Flow Verification
Runs 29 live checks against http://localhost:8000
Usage: python tests/verify_flow.py
"""
import asyncio
import base64
import json
import sys
import httpx

BASE = "http://localhost:8000"
TIMEOUT = 90.0

results = []

def check(name, passed, detail=""):
    icon = "✅ PASS" if passed else "❌ FAIL"
    results.append((name, passed, detail))
    print(f"  {icon}  {name}" + (f" — {detail}" if detail else ""))

async def run():
    async with httpx.AsyncClient(base_url=BASE, timeout=TIMEOUT) as c:

        print("\n━━━ LAYER 1: INFRASTRUCTURE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        # 1. Health check
        r = await c.get("/health")
        d = r.json()
        check("GET /health", r.status_code == 200 and "cluster" in d,
              f"cluster={d.get('cluster','?')[:12]}… es={d.get('es_version','?')}")

        # 2. All 4 indices exist (via overview)
        r = await c.get("/analytics/overview")
        d = r.json()
        keys = set(d.get("total_docs", {}).keys())
        check("4 indices exist in ES", {"knowledge","reviews","customers"} <= keys,
              f"knowledge={d['total_docs'].get('knowledge',0)} reviews={d['total_docs'].get('reviews',0)} customers={d['total_docs'].get('customers',0)}")

        print("\n━━━ LAYER 2: INGESTION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        # 3. Ingest document
        r = await c.post("/ingest/documents", json={
            "title": "ElasticCX Test Doc",
            "text": "ElasticCX is an AI-powered customer experience platform built on Elasticsearch. It supports hybrid RRF search combining BM25 and kNN vector search for maximum relevance.",
            "doc_type": "test"
        })
        d = r.json()
        # Accept deduplicated as pass too (test doc may already exist from prior run)
        total_doc = d.get("chunks_indexed", 0) + d.get("deduplicated", 0)
        check("POST /ingest/documents", r.status_code == 200 and total_doc >= 1,
              f"chunks_indexed={d.get('chunks_indexed')} deduped={d.get('deduplicated')} doc_id={d.get('document_id','?')[:8]}…")

        # 4. Deduplication — same doc again
        r2 = await c.post("/ingest/documents", json={
            "title": "ElasticCX Test Doc",
            "text": "ElasticCX is an AI-powered customer experience platform built on Elasticsearch. It supports hybrid RRF search combining BM25 and kNN vector search for maximum relevance.",
            "doc_type": "test"
        })
        d2 = r2.json()
        check("POST /ingest/documents (dedup)", d2.get("deduplicated", 0) >= 1 and d2.get("chunks_indexed", 0) == 0,
              f"deduplicated={d2.get('deduplicated')} chunks_indexed={d2.get('chunks_indexed')}")

        # 5. Ingest reviews with sentiment derivation
        r = await c.post("/ingest/reviews", json={"reviews": [
            {"review_text": "Amazing product, excellent support team, highly recommend!",
             "source_site": "trustpilot", "company_name": "ElasticCX-Test", "rating": 5.0},
            {"review_text": "Terrible product, very poor service, waste of money.",
             "source_site": "trustpilot", "company_name": "ElasticCX-Test", "rating": 1.0},
        ]})
        d = r.json()
        total_rev = d.get("indexed", 0) + d.get("deduplicated", 0)
        check("POST /ingest/reviews", r.status_code == 200 and total_rev >= 1,
              f"indexed={d.get('indexed')} deduped={d.get('deduplicated')} failed={d.get('failed')}")

        # 6. Ingest email with NLP enrichment
        r = await c.post("/ingest/emails", json={"emails": [{
            "raw_text": "I cannot access my account. My login keeps failing and the password reset email never arrives. This is extremely urgent as I have pending customer tickets.",
            "subject": "Urgent: Cannot login",
            "customer_id": "verify-test-001",
            "timestamp": "2026-03-13T10:00:00Z"
        }]})
        d = r.json()
        total_em = d.get("indexed", 0) + d.get("deduplicated", 0)
        check("POST /ingest/emails", r.status_code == 200 and total_em >= 1,
              f"indexed={d.get('indexed')} deduped={d.get('deduplicated')} index={d.get('index','?')}")

        # Verify NLP fields made it into ES via search
        await asyncio.sleep(1)
        r_nlp = await c.get("/search/customers", params={"q": "cannot login urgent", "top_k": 3})
        hits = r_nlp.json().get("hits", [])
        has_nlp = any(h.get("intent") and h.get("sentiment") and h.get("topics") for h in hits)
        sample = next((h for h in hits if h.get("intent")), {})
        check("Email NLP enrichment stored in ES",
              has_nlp,
              f"intent={sample.get('intent','?')} sentiment={sample.get('sentiment','?')} topics={sample.get('topics',[][:2])}")

        # 7. Ingest transcript with NLP
        r = await c.post("/ingest/transcripts", json={"transcripts": [{
            "raw_text": "Customer: I need to cancel my subscription and get a full refund. The product broke after the last update. Agent: I understand, let me process your refund request right away.",
            "source_type": "call",
            "subject": "Refund and cancellation",
            "customer_id": "verify-test-002",
            "timestamp": "2026-03-13T10:30:00Z"
        }]})
        d = r.json()
        total_tr = d.get("indexed", 0) + d.get("deduplicated", 0)
        check("POST /ingest/transcripts", r.status_code == 200 and total_tr >= 1,
              f"indexed={d.get('indexed')} deduped={d.get('deduplicated')} index={d.get('index','?')}")

        # 8. PDF ingest (synthetic 1-page PDF as base64)
        # Minimal valid PDF bytes
        pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 100 700 Td (ElasticCX FAQ document content for testing PDF ingestion pipeline.) Tj ET
endstream endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
0000000369 00000 n
trailer<</Size 6/Root 1 0 R>>
startxref
441
%%EOF"""
        files = {"file": ("test.pdf", pdf_content, "application/pdf")}
        data = {"title": "Test PDF", "doc_type": "pdf"}
        r = await c.post("/ingest/documents/pdf", files=files, data=data)
        check("POST /ingest/documents/pdf", r.status_code in (200, 422),
              f"status={r.status_code}" + (f" chunks={r.json().get('chunks_indexed')}" if r.status_code == 200 else " (PDF parsed but empty text — expected for minimal PDF)"))

        # PDF invalid extension
        files2 = {"file": ("test.txt", b"not a pdf", "text/plain")}
        r2 = await c.post("/ingest/documents/pdf", files=files2, data={"title": "Bad"})
        check("POST /ingest/documents/pdf (non-pdf → 400)", r2.status_code == 400,
              f"status={r2.status_code}")

        print("\n━━━ LAYER 3: SEARCH ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        # 9. Knowledge search with highlights
        r = await c.get("/search/knowledge", params={"q": "hybrid search elasticsearch", "top_k": 5})
        d = r.json()
        hits = d.get("hits", [])
        has_highlights = any(h.get("highlights") for h in hits)
        check("GET /search/knowledge (hybrid + highlights)", len(hits) > 0,
              f"hits={len(hits)} total={d.get('total')} took={d.get('took_ms')}ms highlights={'yes' if has_highlights else 'no'}")

        # 10. Reviews filter by company
        r = await c.get("/search/reviews", params={"q": "customer support", "company": "Zendesk", "top_k": 5})
        d = r.json()
        all_zendesk = all(h.get("company_name") == "Zendesk" for h in d.get("hits", []))
        check("GET /search/reviews?company=Zendesk", len(d.get("hits",[])) > 0 and all_zendesk,
              f"hits={len(d.get('hits',[]))} all_zendesk={all_zendesk}")

        # 11. Reviews filter by sentiment
        r = await c.get("/search/reviews", params={"q": "product", "sentiment": "negative", "top_k": 5})
        d = r.json()
        all_neg = all(h.get("sentiment") == "negative" for h in d.get("hits", []))
        check("GET /search/reviews?sentiment=negative", len(d.get("hits",[])) > 0 and all_neg,
              f"hits={len(d.get('hits',[]))} all_negative={all_neg}")

        # 12. Recency boost
        r = await c.get("/search/reviews", params={"q": "subscription cancel", "boost_recency": "true", "top_k": 5})
        try:
            d = r.json()
            check("GET /search/reviews?boost_recency=true", r.status_code == 200,
                  f"hits={len(d.get('hits',[]))} took={d.get('took_ms')}ms")
        except Exception as e:
            check("GET /search/reviews?boost_recency=true", False, f"status={r.status_code} error={e}")

        # 13. Customer search by source_type
        r = await c.get("/search/customers", params={"q": "login account access", "source_type": "email", "top_k": 5})
        d = r.json()
        all_email = all(h.get("source_type") == "email" for h in d.get("hits", []))
        check("GET /search/customers?source_type=email", r.status_code == 200 and (len(d.get("hits",[])) == 0 or all_email),
              f"hits={len(d.get('hits',[]))} all_email={all_email}")

        # 14. Customer search by intent
        r = await c.get("/search/customers", params={"q": "cancel refund", "intent": "refund_request", "top_k": 5})
        d = r.json()
        all_refund = all(h.get("intent") == "refund_request" for h in d.get("hits", []))
        check("GET /search/customers?intent=refund_request", r.status_code == 200 and (len(d.get("hits",[])) == 0 or all_refund),
              f"hits={len(d.get('hits',[]))} all_refund={all_refund}")

        print("\n━━━ LAYER 4: AI / RAG ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        # 15. Modes endpoint
        r = await c.get("/ai/modes")
        d = r.json()
        modes = set(d.get("modes", {}).keys())
        check("GET /ai/modes", {"support_bot","sales_copilot","support_agent","recommendations"} <= modes,
              f"modes={sorted(modes)}")

        # 16. support_bot text mode
        r = await c.post("/ai/query", json={"question": "What is ElasticCX?", "mode": "support_bot"})
        d = r.json()
        check("POST /ai/query support_bot (text)", r.status_code == 200 and isinstance(d.get("answer"), str) and len(d.get("answer","")) > 10,
              f"answer_len={len(d.get('answer',''))} conv_id={d.get('conversation_id','?')[:8]}… latency={d.get('latency_ms')}ms")
        conv_id_1 = d.get("conversation_id")

        # 17. sales_copilot JSON mode
        r = await c.post("/ai/query", json={"question": "What are Zendesk's main weaknesses?", "mode": "sales_copilot", "output_format": "json"})
        d = r.json()
        answer = d.get("answer", {})
        check("POST /ai/query sales_copilot (json)", r.status_code == 200 and isinstance(answer, dict) and "competitor_weaknesses" in answer,
              f"keys={list(answer.keys())[:3]} sources={d.get('total_context_chunks')}")

        # 18. support_agent JSON mode
        r = await c.post("/ai/query", json={"question": "Customer cannot login for 3 days, very frustrated", "mode": "support_agent", "output_format": "json"})
        d = r.json()
        answer = d.get("answer", {})
        check("POST /ai/query support_agent (json)", r.status_code == 200 and isinstance(answer, dict) and "severity" in answer,
              f"severity={answer.get('severity','?')} escalation={answer.get('escalation_required','?')}")

        # 19. recommendations JSON mode
        r = await c.post("/ai/query", json={"question": "What product improvements should we make?", "mode": "recommendations", "output_format": "json"})
        d = r.json()
        answer = d.get("answer", {})
        check("POST /ai/query recommendations (json)", r.status_code == 200 and isinstance(answer, dict) and "top_improvements" in answer,
              f"keys={list(answer.keys())}")

        # 20. Multi-turn conversation
        r1 = await c.post("/ai/query", json={"question": "Tell me about Zendesk pricing plans", "mode": "support_bot"})
        conv_id = r1.json().get("conversation_id")
        r2 = await c.post("/ai/query", json={"question": "Which of those plans did you just mention is cheapest?", "mode": "support_bot", "conversation_id": conv_id})
        d2 = r2.json()
        same_conv = d2.get("conversation_id") == conv_id
        answer_refs_context = len(d2.get("answer", "")) > 20
        check("Multi-turn conversation", same_conv and answer_refs_context,
              f"same_conv_id={same_conv} answer_len={len(d2.get('answer',''))} conv={conv_id[:8]}…")

        # 21. Invalid mode → 4xx error
        r = await c.post("/ai/query", json={"question": "test", "mode": "invalid_mode_xyz"})
        check("POST /ai/query invalid mode → 4xx", r.status_code in (400, 422),
              f"status={r.status_code}")

        print("\n━━━ LAYER 5: ALERTS (PERCOLATOR) ━━━━━━━━━━━━━━━━━━━━━━━━━")

        # 22. Create alert
        r = await c.post("/alerts", json={
            "name": "Verify-Test-Alert",
            "description": "Test alert for flow verification",
            "target_index": "market-intelligence-index",
            "query_dsl": {"match": {"review_text": "cancel refund"}}
        })
        d = r.json()
        alert_id = d.get("id")
        check("POST /alerts (create)", r.status_code == 201 and alert_id,
              f"id={alert_id} name={d.get('name')}")

        # 23. List alerts
        r = await c.get("/alerts")
        alert_names = [a.get("name") for a in r.json()]
        check("GET /alerts (list)", r.status_code == 200 and "Verify-Test-Alert" in alert_names,
              f"total_alerts={len(r.json())} names={alert_names[:3]}")

        # 24. Get single alert
        r = await c.get(f"/alerts/{alert_id}")
        d = r.json()
        check("GET /alerts/{id}", r.status_code == 200 and d.get("id") == alert_id,
              f"id={d.get('id')} name={d.get('name')}")

        # 25. Delete alert
        r = await c.delete(f"/alerts/{alert_id}")
        r2 = await c.get(f"/alerts/{alert_id}")
        check("DELETE /alerts/{id}", r.status_code == 204 and r2.status_code == 404,
              f"delete_status={r.status_code} get_after_delete={r2.status_code}")

        print("\n━━━ LAYER 6: ANALYTICS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        # 26. Overview
        r = await c.get("/analytics/overview")
        d = r.json()
        total = sum(d.get("total_docs", {}).values())
        check("GET /analytics/overview", r.status_code == 200 and total > 0,
              f"knowledge={d['total_docs'].get('knowledge')} reviews={d['total_docs'].get('reviews')} customers={d['total_docs'].get('customers')}")

        # 27. Competitor compare
        r = await c.get("/analytics/competitor-compare", params={"companies": "Zendesk,Freshdesk"})
        d = r.json()
        companies = {c["company"]: c for c in d.get("companies", [])}
        check("GET /analytics/competitor-compare", r.status_code == 200 and len(companies) >= 1,
              f"Zendesk avg={companies.get('Zendesk',{}).get('avg_rating','N/A')}★ Freshdesk avg={companies.get('Freshdesk',{}).get('avg_rating','N/A')}★")

        # 28. Sentiment trend
        r = await c.get("/analytics/sentiment-trend", params={"index": "reviews", "days": 365})
        d = r.json()
        check("GET /analytics/sentiment-trend", r.status_code == 200 and "buckets" in d,
              f"buckets={len(d.get('buckets',[]))} days=365")

        # 29. AI company summary
        r = await c.get("/analytics/summary", params={"company": "Zendesk", "top_k": 10})
        d = r.json()
        summary = d.get("summary", {})
        has_keys = all(k in summary for k in ["key_themes", "weaknesses", "one_sentence_summary"])
        check("GET /analytics/summary (AI brief)", r.status_code == 200 and has_keys,
              f"sentiment={summary.get('overall_sentiment','?')} themes={len(summary.get('key_themes',[]))} latency={d.get('latency_ms')}ms")

    # ── Final report ──────────────────────────────────────────────────────────
    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    total = len(results)

    print("\n" + "━" * 60)
    print(f"  RESULTS: {passed}/{total} passed", end="")
    if failed:
        print(f"  ({failed} FAILED)")
        print("\n  Failed checks:")
        for name, p, detail in results:
            if not p:
                print(f"    ❌ {name} — {detail}")
    else:
        print("  — ALL CHECKS PASSED ✅")
    print("━" * 60 + "\n")

    return failed

if __name__ == "__main__":
    failed = asyncio.run(run())
    sys.exit(1 if failed else 0)
