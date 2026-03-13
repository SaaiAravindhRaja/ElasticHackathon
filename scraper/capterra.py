import re
import logging
from playwright.async_api import Page
from scraper.base_scraper import BaseScraper, RawReview

logger = logging.getLogger(__name__)


class CapterraScraper(BaseScraper):
    """
    Scrapes Capterra review pages.
    Capterra uses a React SPA — wait for review cards to render.
    Target: https://www.capterra.com/p/25922/Zendesk/
    """

    # Map company name → Capterra product path
    _URL_MAP = {
        "zendesk": "https://www.capterra.com/p/25922/Zendesk/",
    }

    @property
    def source_site(self) -> str:
        return "capterra"

    def build_url(self, page_num: int) -> str:
        base = self._URL_MAP.get(
            self.company_name.lower(),
            f"https://www.capterra.com/p/{self.company_name.lower()}/",
        )
        return base if page_num == 1 else f"{base}?page={page_num}"

    async def _scrape_page(self, page: Page, page_url: str) -> list[RawReview]:
        reviews: list[RawReview] = []

        # Wait for review cards
        try:
            await page.wait_for_selector(
                "[data-testid='review-card'], .review-card, [class*='ReviewCard']",
                timeout=20000,
            )
        except Exception:
            # Try a broader wait
            try:
                await page.wait_for_selector(
                    "section[aria-label*='review'], article[class*='review']",
                    timeout=10000,
                )
            except Exception:
                return []

        cards = await page.query_selector_all(
            "[data-testid='review-card'], .review-card, [class*='ReviewCard']"
        )
        if not cards:
            cards = await page.query_selector_all(
                "section[aria-label*='review'], article[class*='review']"
            )

        for card in cards:
            try:
                # Pros and cons (Capterra always shows these)
                pros_el = await card.query_selector(
                    "[data-testid='pros'], [class*='pros'], p[class*='Pros']"
                )
                cons_el = await card.query_selector(
                    "[data-testid='cons'], [class*='cons'], p[class*='Cons']"
                )
                pros = (await pros_el.inner_text()).strip() if pros_el else None
                cons = (await cons_el.inner_text()).strip() if cons_el else None

                parts = [p for p in [pros, cons] if p]
                review_text = " | ".join(parts)

                # Fallback to overall review body
                if not review_text:
                    body_el = await card.query_selector(
                        "[class*='review-body'], [class*='ReviewBody'], p[class*='comment']"
                    )
                    review_text = (await body_el.inner_text()).strip() if body_el else ""

                if not review_text:
                    continue

                # Star rating
                rating: float | None = None
                star_el = await card.query_selector(
                    "[aria-label*='out of 5'], [aria-label*='stars'], [class*='star-rating']"
                )
                if star_el:
                    aria = (await star_el.get_attribute("aria-label")) or ""
                    m = re.search(r"([\d.]+)\s*(?:out of\s*5|stars?)", aria, re.I)
                    if m:
                        rating = float(m.group(1))

                # Date
                date_str: str | None = None
                time_el = await card.query_selector("time, [datetime]")
                if time_el:
                    date_str = await time_el.get_attribute("datetime")
                    if not date_str:
                        date_str = (await time_el.inner_text()).strip() or None

                # Reviewer name
                name_el = await card.query_selector(
                    "[class*='reviewer-name'], [class*='ReviewerName'], [data-testid='reviewer-name']"
                )
                reviewer = (await name_el.inner_text()).strip() if name_el else None

                reviews.append(
                    RawReview(
                        review_text=review_text,
                        rating=rating,
                        date=date_str,
                        reviewer=reviewer,
                        pros=pros,
                        cons=cons,
                        url=page_url,
                        company_name=self.company_name,
                        source_site=self.source_site,
                    )
                )
            except Exception as e:
                logger.debug(f"Capterra card parse error: {e}")
                continue

        return reviews
