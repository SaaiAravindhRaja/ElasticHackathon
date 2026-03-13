import re
import logging
from playwright.async_api import Page
from scraper.base_scraper import BaseScraper, RawReview

logger = logging.getLogger(__name__)


class G2Scraper(BaseScraper):
    """
    Scrapes G2 company review pages.
    G2 explicitly shows pros and cons per review — great for sentiment analysis.
    Target: https://www.g2.com/products/zendesk-support-suite/reviews
    """

    # Map company name → G2 product slug (override for non-default slugs)
    _SLUG_MAP = {
        "zendesk": "zendesk-support-suite",
    }

    @property
    def source_site(self) -> str:
        return "g2"

    def build_url(self, page_num: int) -> str:
        key = self.company_name.lower()
        slug = self._SLUG_MAP.get(key, key.replace(" ", "-"))
        base = f"https://www.g2.com/products/{slug}/reviews"
        return base if page_num == 1 else f"{base}?page={page_num}"

    async def _scrape_page(self, page: Page, page_url: str) -> list[RawReview]:
        reviews: list[RawReview] = []

        # G2 is a React SPA — wait for review cards
        try:
            await page.wait_for_selector(
                ".paper.paper--white.paper--box, [itemprop='review']",
                timeout=20000,
            )
        except Exception:
            return []

        # Try both possible card selectors
        cards = await page.query_selector_all("[itemprop='review']")
        if not cards:
            cards = await page.query_selector_all(".paper.paper--white.paper--box")

        for card in cards:
            try:
                # G2 uses structured pros/cons sections
                pros_el = await card.query_selector(
                    "[data-testid='pros'], .review-pros p, .review-pros span"
                )
                cons_el = await card.query_selector(
                    "[data-testid='cons'], .review-cons p, .review-cons span"
                )
                pros = (await pros_el.inner_text()).strip() if pros_el else None
                cons = (await cons_el.inner_text()).strip() if cons_el else None

                # Combine pros + cons as the main review text
                parts = [p for p in [pros, cons] if p]
                review_text = " | ".join(parts) if parts else ""

                # Fallback: look for any review body text
                if not review_text:
                    body_el = await card.query_selector(
                        "[itemprop='reviewBody'], .review-text, .pjax-content p"
                    )
                    review_text = (await body_el.inner_text()).strip() if body_el else ""

                if not review_text:
                    continue

                # Star rating from aria-label
                rating: float | None = None
                star_el = await card.query_selector(
                    ".stars, [class*='star'], [aria-label*='out of 5']"
                )
                if star_el:
                    aria = (await star_el.get_attribute("aria-label")) or ""
                    m = re.search(r"([\d.]+)\s*out of\s*5", aria, re.I)
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
                    ".fw-semibold, [class*='reviewer-name'], [itemprop='author']"
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
                logger.debug(f"G2 card parse error: {e}")
                continue

        return reviews
