"""
Scrape full company intelligence for all competitors:
Wikipedia overview, About page, Leadership/Team, Products/Features.

Ingests everything into company-knowledge-index as searchable documents.

Usage:
    python -m scripts.scrape_companies
    python -m scripts.scrape_companies --company Zendesk
"""
import asyncio
import argparse
import logging
import httpx
from scraper.company_scraper import scrape_company_full, COMPANY_SLUGS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)


async def ingest_docs(docs, company: str, api_url: str) -> dict:
    if not docs:
        return {"company": company, "docs": 0, "indexed": 0}

    async with httpx.AsyncClient(timeout=120.0) as client:
        indexed = 0
        deduped = 0
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

    logger.info(f"  [{company}] Ingested {len(docs)} docs → chunks indexed={indexed} deduped={deduped}")
    return {"company": company, "docs": len(docs), "indexed": indexed, "deduped": deduped}


async def run(companies: list[str], api_url: str):
    logger.info(f"Scraping full company data for: {companies}\n")
    summary = []

    for company in companies:
        logger.info(f"━━━ {company} ━━━")
        docs = await scrape_company_full(company)
        result = await ingest_docs(docs, company, api_url)
        summary.append(result)
        await asyncio.sleep(2)

    print("\n" + "━" * 55)
    print("  COMPANY SCRAPE COMPLETE")
    print("━" * 55)
    for r in summary:
        status = "✅" if r.get("indexed", 0) + r.get("deduped", 0) > 0 else "⚠️ "
        print(f"  {status}  {r['company']:<14}  docs={r.get('docs',0)}  chunks={r.get('indexed',0)}  deduped={r.get('deduped',0)}")
    print("━" * 55)
    total = sum(r.get("indexed", 0) for r in summary)
    print(f"  Total chunks indexed: {total}")
    print("━" * 55 + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--company", help="Single company (default: all)")
    parser.add_argument("--api", default="http://localhost:8000")
    args = parser.parse_args()

    companies = [args.company] if args.company else list(COMPANY_SLUGS.keys())
    asyncio.run(run(companies=companies, api_url=args.api))


if __name__ == "__main__":
    main()
