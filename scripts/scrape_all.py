"""
Scrape everything we can from Trustpilot for every major CX/support competitor.
Runs companies sequentially (to avoid getting blocked), 5 pages each.

Usage:
    python scripts/scrape_all.py
    python scripts/scrape_all.py --pages 10 --api http://localhost:8000
"""
import asyncio
import argparse
import logging
import httpx
from scraper.trustpilot import TrustpilotScraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

COMPANIES = [
    "Zendesk",
    "Freshdesk",
    "Intercom",
    "HubSpot",
    "Salesforce",
    "Zoho",
    "LiveChat",
    "Drift",
    "Pipedrive",
    "Monday",
]


async def scrape_company(company: str, max_pages: int, api_url: str) -> dict:
    logger.info(f"▶ Scraping {company} ({max_pages} pages)…")
    scraper = TrustpilotScraper(company_name=company, max_pages=max_pages)
    try:
        reviews = await scraper.scrape()
    except Exception as e:
        logger.error(f"  {company} scrape failed: {e}")
        return {"company": company, "scraped": 0, "indexed": 0, "failed": str(e)}

    if not reviews:
        logger.warning(f"  {company}: 0 reviews found")
        return {"company": company, "scraped": 0, "indexed": 0}

    logger.info(f"  {company}: {len(reviews)} reviews scraped — ingesting…")

    payload = {
        "reviews": [
            {
                "review_text": r.review_text,
                "source_site": r.source_site,
                "company_name": r.company_name,
                "rating": r.rating,
                "reviewer": r.reviewer,
                "date": r.date,
                "url": r.url,
                "pros": r.pros,
                "cons": r.cons,
            }
            for r in reviews
        ]
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(f"{api_url.rstrip('/')}/ingest/reviews", json=payload)
        resp.raise_for_status()
        result = resp.json()

    indexed = result.get("indexed", 0)
    deduped = result.get("deduplicated", 0)
    logger.info(f"  {company}: indexed={indexed}  deduped={deduped}")
    return {"company": company, "scraped": len(reviews), "indexed": indexed, "deduped": deduped}


async def run(max_pages: int, api_url: str):
    logger.info(f"Starting bulk scrape — {len(COMPANIES)} companies × {max_pages} pages each\n")
    summary = []

    for company in COMPANIES:
        result = await scrape_company(company, max_pages, api_url)
        summary.append(result)
        await asyncio.sleep(2)  # small pause between companies to avoid rate limiting

    print("\n" + "━" * 50)
    print("  SCRAPE COMPLETE")
    print("━" * 50)
    total_scraped = sum(r.get("scraped", 0) for r in summary)
    total_indexed = sum(r.get("indexed", 0) for r in summary)
    total_deduped = sum(r.get("deduped", 0) for r in summary)
    for r in summary:
        status = "✅" if r.get("indexed", 0) + r.get("deduped", 0) > 0 else "⚠️ "
        print(f"  {status}  {r['company']:<14} scraped={r.get('scraped',0):>3}  indexed={r.get('indexed',0):>3}  deduped={r.get('deduped',0):>3}")
    print("━" * 50)
    print(f"  TOTAL  scraped={total_scraped}  indexed={total_indexed}  deduped={total_deduped}")
    print("━" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=5, help="Pages per company (default 5)")
    parser.add_argument("--api", default="http://localhost:8000")
    args = parser.parse_args()
    asyncio.run(run(max_pages=args.pages, api_url=args.api))


if __name__ == "__main__":
    main()
