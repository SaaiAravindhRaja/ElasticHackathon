"""
Scrapes Zendesk Help Center (support.zendesk.com/hc/en-us) for support documentation:
- Account management (password reset, profile, 2FA)
- Ticket and request management
- Billing and subscriptions
- Getting started guides
- Integration and API docs

Ingests into company-knowledge-index as doc_type="help_article" for company_name="Zendesk"
so the AI can answer questions like "Where do I reset my password?"
"""
import logging
import re
from playwright.async_api import async_playwright, Page

from scraper.company_scraper import CompanyDoc

logger = logging.getLogger(__name__)

HELP_CENTER_URL = "https://support.zendesk.com/hc/en-us"
MAX_ARTICLES = 50
MAX_PER_CATEGORY = 8


async def _get_article_text(page: Page, url: str) -> tuple[str, str]:
    """Return (title, body_text) for a single help article."""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(1000)

        # Title
        title_el = await page.query_selector("h1")
        title = (await title_el.inner_text()).strip() if title_el else "Zendesk Help Article"

        # Body: try multiple selectors to find article content
        body_parts = []
        # Try container-level selectors first, then fall back to generic
        container_selectors = [
            ".article-body",
            "[itemprop='articleBody']",
            "#article-body",
            ".hc-article-body",
            ".article-container",
            "article",
            "main",
        ]
        container = None
        for sel in container_selectors:
            container = await page.query_selector(sel)
            if container:
                break

        if container:
            for child_sel in ["p", "li", "h2", "h3", "h4"]:
                children = await container.query_selector_all(child_sel)
                for el in children:
                    t = (await el.inner_text()).strip()
                    if t and len(t) > 20:
                        body_parts.append(t)

        # Ultimate fallback: grab all visible text from the page body
        if not body_parts:
            body_el = await page.query_selector("body")
            if body_el:
                raw = (await body_el.inner_text()).strip()
                # Just take the middle chunk (skip nav/header/footer noise)
                lines = [l.strip() for l in raw.split('\n') if len(l.strip()) > 30]
                body_parts = lines[5:60]  # skip first 5 nav lines, take up to 55 content lines

        body = "\n\n".join(body_parts)
        body = re.sub(r"\s{3,}", "\n\n", body)
        return title, body[:5000]
    except Exception as e:
        logger.warning(f"  Failed to get article {url}: {e}")
        return "", ""


async def scrape_zendesk_help() -> list[CompanyDoc]:
    """Scrape Zendesk Help Center and return CompanyDoc objects."""
    docs: list[CompanyDoc] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()

        # 1. Load main help center page
        logger.info(f"Loading Zendesk Help Center: {HELP_CENTER_URL}")
        try:
            await page.goto(HELP_CENTER_URL, wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(2000)
        except Exception as e:
            logger.error(f"Failed to load help center: {e}")
            await browser.close()
            return docs

        # 2. Collect category/section links
        # Zendesk HC has section links like /hc/en-us/sections/...
        # and category links like /hc/en-us/categories/...
        all_links = await page.query_selector_all("a[href*='/hc/en-us/sections/'], a[href*='/hc/en-us/categories/']")
        section_urls = []
        seen = set()
        for link in all_links:
            href = await link.get_attribute("href")
            if href and href not in seen:
                if href.startswith("/"):
                    href = "https://support.zendesk.com" + href
                seen.add(href)
                section_urls.append(href)

        logger.info(f"Found {len(section_urls)} section/category links")

        # If no section links found, try to get article links directly
        if not section_urls:
            logger.info("No section links found, scraping article links directly from main page")
            article_links = await page.query_selector_all("a[href*='/hc/en-us/articles/']")
            article_urls = []
            for link in article_links:
                href = await link.get_attribute("href")
                if href and href not in seen:
                    if href.startswith("/"):
                        href = "https://support.zendesk.com" + href
                    seen.add(href)
                    article_urls.append(href)
            section_urls = []  # skip section loop below
            # Process articles directly
            for url in article_urls[:MAX_ARTICLES]:
                title, body = await _get_article_text(page, url)
                if title and len(body) > 100:
                    logger.info(f"  Article: {title[:60]} ({len(body)} chars)")
                    docs.append(CompanyDoc(
                        title=f"Zendesk Help: {title}",
                        text=body,
                        doc_type="help_article",
                        company_name="Zendesk",
                        source_url=url,
                    ))

        # 3. For each section, collect article links
        article_urls_all: list[str] = []
        for section_url in section_urls:
            if len(article_urls_all) >= MAX_ARTICLES:
                break
            try:
                await page.goto(section_url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(1000)

                links = await page.query_selector_all("a[href*='/hc/en-us/articles/']")
                count = 0
                for link in links:
                    if count >= MAX_PER_CATEGORY:
                        break
                    href = await link.get_attribute("href")
                    if href and href not in seen:
                        if href.startswith("/"):
                            href = "https://support.zendesk.com" + href
                        # Skip non-article anchored links
                        if "#" not in href:
                            seen.add(href)
                            article_urls_all.append(href)
                            count += 1
                logger.info(f"  Section {section_url.split('/')[-1]}: {count} articles")
            except Exception as e:
                logger.warning(f"  Section failed {section_url}: {e}")
                continue

        # 4. Scrape each article
        logger.info(f"Scraping {min(len(article_urls_all), MAX_ARTICLES)} articles...")
        for url in article_urls_all[:MAX_ARTICLES]:
            title, body = await _get_article_text(page, url)
            if title and len(body) > 100:
                logger.info(f"  ✓ {title[:70]} ({len(body)} chars)")
                docs.append(CompanyDoc(
                    title=f"Zendesk Help: {title}",
                    text=body,
                    doc_type="help_article",
                    company_name="Zendesk",
                    source_url=url,
                ))
            await page.wait_for_timeout(500)  # polite delay

        await context.close()
        await browser.close()

    logger.info(f"Total Zendesk help articles scraped: {len(docs)}")
    return docs
