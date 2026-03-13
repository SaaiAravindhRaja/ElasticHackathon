"""
Orchestrates all review scrapers and POSTs collected reviews to the ingestion API.

Usage:
    python -m scraper.runner
    python -m scraper.runner --company Zendesk --pages 3 --api http://localhost:8000
"""
import asyncio
import argparse
import logging
import httpx
from dataclasses import asdict

from scraper.trustpilot import TrustpilotScraper
from scraper.g2 import G2Scraper
from scraper.capterra import CapterraScraper
from scraper.base_scraper import RawReview

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)


async def run(company: str, max_pages: int, api_url: str) -> None:
    scrapers = [
        TrustpilotScraper(company_name=company, max_pages=max_pages),
        G2Scraper(company_name=company, max_pages=max_pages),
        CapterraScraper(company_name=company, max_pages=max_pages),
    ]

    all_reviews: list[RawReview] = []
    for scraper in scrapers:
        logger.info(f"Starting {scraper.source_site} scraper for '{company}'")
        try:
            reviews = await scraper.scrape()
            logger.info(f"{scraper.source_site}: {len(reviews)} reviews")
            all_reviews.extend(reviews)
        except Exception as e:
            logger.error(f"{scraper.source_site} scraper failed: {e}")

    if not all_reviews:
        logger.warning("No reviews scraped — nothing to POST")
        return

    logger.info(f"Total reviews scraped: {len(all_reviews)}")

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
            for r in all_reviews
        ]
    }

    ingest_endpoint = f"{api_url.rstrip('/')}/ingest/reviews"
    logger.info(f"POSTing {len(all_reviews)} reviews to {ingest_endpoint}")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(ingest_endpoint, json=payload)
        response.raise_for_status()
        result = response.json()
        logger.info(
            f"Ingest complete — indexed: {result.get('indexed')}, "
            f"failed: {result.get('failed')}"
        )


def main():
    parser = argparse.ArgumentParser(description="ElasticCX review scraper")
    parser.add_argument("--company", default="Zendesk", help="Company name to scrape reviews for")
    parser.add_argument("--pages", type=int, default=3, help="Max pages per site")
    parser.add_argument("--api", default="http://localhost:8000", help="Ingestion API base URL")
    args = parser.parse_args()

    asyncio.run(run(company=args.company, max_pages=args.pages, api_url=args.api))


if __name__ == "__main__":
    main()
