import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)


@dataclass
class RawReview:
    review_text: str
    url: str
    company_name: str
    source_site: str
    rating: Optional[float] = None
    date: Optional[str] = None
    reviewer: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None


class BaseScraper(ABC):
    """
    Base class for all review site scrapers.
    Manages the Playwright browser lifecycle.
    Subclasses implement build_url() and _scrape_page().
    """

    def __init__(self, company_name: str, max_pages: int = 5):
        self.company_name = company_name
        self.max_pages = max_pages

    @property
    @abstractmethod
    def source_site(self) -> str: ...

    @abstractmethod
    def build_url(self, page_num: int) -> str: ...

    @abstractmethod
    async def _scrape_page(self, page: Page, page_url: str) -> list[RawReview]: ...

    async def scrape(self) -> list[RawReview]:
        all_reviews: list[RawReview] = []

        async with async_playwright() as pw:
            browser: Browser = await pw.chromium.launch(headless=True)
            context: BrowserContext = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 900},
            )
            page: Page = await context.new_page()

            for page_num in range(1, self.max_pages + 1):
                url = self.build_url(page_num)
                logger.info(f"[{self.source_site}] Scraping page {page_num}: {url}")
                try:
                    await page.goto(url, wait_until="networkidle", timeout=45000)
                    reviews = await self._scrape_page(page, url)
                    if not reviews:
                        logger.info(f"[{self.source_site}] No reviews on page {page_num}, stopping")
                        break
                    all_reviews.extend(reviews)
                    logger.info(f"[{self.source_site}] Got {len(reviews)} reviews from page {page_num}")
                    # Polite delay between pages
                    await page.wait_for_timeout(1500)
                except Exception as e:
                    logger.warning(f"[{self.source_site}] Page {page_num} failed: {e}")
                    break

            await context.close()
            await browser.close()

        logger.info(f"[{self.source_site}] Total scraped: {len(all_reviews)}")
        return all_reviews
