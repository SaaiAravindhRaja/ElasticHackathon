import re
import logging
from playwright.async_api import Page
from scraper.base_scraper import BaseScraper, RawReview

logger = logging.getLogger(__name__)


class TrustpilotScraper(BaseScraper):
    """
    Scrapes Trustpilot company review pages.
    Trustpilot SSR-renders review cards for SEO, so DOM scraping works well.
    Target: https://www.trustpilot.com/review/www.zendesk.com
    """

    @property
    def source_site(self) -> str:
        return "trustpilot"

    def build_url(self, page_num: int) -> str:
        company_slug = self.company_name.lower()
        base = f"https://www.trustpilot.com/review/www.{company_slug}.com"
        return base if page_num == 1 else f"{base}?page={page_num}"

    async def _scrape_page(self, page: Page, page_url: str) -> list[RawReview]:
        reviews: list[RawReview] = []

        try:
            await page.wait_for_selector("[data-service-review-card-paper]", timeout=12000)
        except Exception:
            # Might be blocked or no reviews — try alternative selector
            try:
                await page.wait_for_selector("article[class*='paper']", timeout=8000)
            except Exception:
                return []

        cards = await page.query_selector_all("[data-service-review-card-paper]")
        if not cards:
            cards = await page.query_selector_all("article[class*='paper']")

        for card in cards:
            try:
                # Review body text
                body_el = await card.query_selector("[data-service-review-text-typography]")
                review_text = (await body_el.inner_text()).strip() if body_el else ""
                if not review_text:
                    continue

                # Star rating — from img alt like "Rated 4 out of 5 stars"
                rating: float | None = None
                star_el = await card.query_selector("img[alt*='star'], img[alt*='Star']")
                if star_el:
                    alt = (await star_el.get_attribute("alt")) or ""
                    m = re.search(r"(\d+(?:\.\d+)?)", alt)
                    if m:
                        rating = float(m.group(1))

                # Date ISO string from <time datetime="...">
                date_str: str | None = None
                time_el = await card.query_selector("time")
                if time_el:
                    date_str = await time_el.get_attribute("datetime")

                # Reviewer display name
                name_el = await card.query_selector("[data-consumer-name-typography]")
                reviewer = (await name_el.inner_text()).strip() if name_el else None

                reviews.append(
                    RawReview(
                        review_text=review_text,
                        rating=rating,
                        date=date_str,
                        reviewer=reviewer,
                        pros=None,
                        cons=None,
                        url=page_url,
                        company_name=self.company_name,
                        source_site=self.source_site,
                    )
                )
            except Exception as e:
                logger.debug(f"Trustpilot card parse error: {e}")
                continue

        return reviews
