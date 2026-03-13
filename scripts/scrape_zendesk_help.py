"""
Scrape Zendesk Help Center and ingest articles into company-knowledge-index.

This gives the AI the ability to answer product support questions like:
  "Where do I reset my password?"
  "How do I create a ticket?"
  "How do I cancel my subscription?"

Usage:
    python -m scripts.scrape_zendesk_help
    python -m scripts.scrape_zendesk_help --api http://localhost:8000
"""
import asyncio
import argparse
import logging
import httpx
from scraper.zendesk_helpcenter import scrape_zendesk_help

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)


async def ingest_docs(docs, api_url: str) -> dict:
    if not docs:
        return {"docs": 0, "indexed": 0, "deduped": 0}

    indexed = 0
    deduped = 0
    failed = 0

    async with httpx.AsyncClient(timeout=120.0) as client:
        for doc in docs:
            payload = {
                "title": doc.title,
                "text": doc.text,
                "doc_type": doc.doc_type,
                "company_name": doc.company_name,
                "source_url": doc.source_url,
            }
            try:
                r = await client.post(f"{api_url.rstrip('/')}/ingest/documents", json=payload)
                r.raise_for_status()
                result = r.json()
                indexed += result.get("chunks_indexed", 0)
                deduped += result.get("deduplicated", 0)
            except Exception as e:
                logger.warning(f"  Ingest failed for '{doc.title}': {e}")
                failed += 1

    return {"docs": len(docs), "indexed": indexed, "deduped": deduped, "failed": failed}


async def run(api_url: str):
    logger.info("━━━ Scraping Zendesk Help Center ━━━")
    docs = await scrape_zendesk_help()

    if not docs:
        logger.error("No articles scraped — check network or Zendesk Help Center structure")
        return

    logger.info(f"\nIngesting {len(docs)} help articles into company-knowledge-index...")
    result = await ingest_docs(docs, api_url)

    print("\n" + "━" * 55)
    print("  ZENDESK HELP CENTER SCRAPE COMPLETE")
    print("━" * 55)
    print(f"  Articles scraped:  {result['docs']}")
    print(f"  Chunks indexed:    {result['indexed']}")
    print(f"  Deduplicated:      {result['deduped']}")
    print(f"  Failed:            {result['failed']}")
    print("━" * 55)
    total = result["indexed"] + result["deduped"]
    if total > 0:
        print(f"  ✅ Success — AI can now answer Zendesk support questions")
    else:
        print(f"  ⚠️  No chunks indexed — check API server and scraper output")
    print("━" * 55 + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8000")
    args = parser.parse_args()
    asyncio.run(run(api_url=args.api))


if __name__ == "__main__":
    main()
