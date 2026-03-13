"""
Scrapes full company intelligence from multiple sources:
- Wikipedia (company overview, founding, HQ, key people, products, revenue)
- Company's own About page
- Company's own Team/Leadership page
- Company's own Products/Features page

All content is ingested as documents into company-knowledge-index so the
agent-builder has rich company context — not just customer reviews.
"""
import logging
import re
from dataclasses import dataclass
from playwright.async_api import async_playwright, Page

logger = logging.getLogger(__name__)


@dataclass
class CompanyDoc:
    title: str
    text: str
    doc_type: str        # "company_overview" | "leadership" | "products" | "about"
    company_name: str
    source_url: str


# Company slug mappings for website URLs
COMPANY_SLUGS = {
    "Zendesk":     {"web": "zendesk.com",     "wiki": "Zendesk"},
    "Freshdesk":   {"web": "freshworks.com",  "wiki": "Freshworks"},
    "Intercom":    {"web": "intercom.com",     "wiki": "Intercom_(company)"},
    "HubSpot":     {"web": "hubspot.com",      "wiki": "HubSpot"},
    "Salesforce":  {"web": "salesforce.com",   "wiki": "Salesforce"},
    "Zoho":        {"web": "zoho.com",         "wiki": "Zoho_Corporation"},
    "LiveChat":    {"web": "livechat.com",     "wiki": "LiveChat"},
    "Drift":       {"web": "drift.com",        "wiki": "Drift_(software)"},
    "Pipedrive":   {"web": "pipedrive.com",    "wiki": "Pipedrive"},
    "Monday":      {"web": "monday.com",       "wiki": "Monday.com"},
}


async def _get_text(page: Page, selector: str) -> str:
    try:
        el = await page.query_selector(selector)
        return (await el.inner_text()).strip() if el else ""
    except Exception:
        return ""


async def _get_all_text(page: Page, selector: str) -> str:
    try:
        els = await page.query_selector_all(selector)
        parts = []
        for el in els:
            t = (await el.inner_text()).strip()
            if t and len(t) > 30:
                parts.append(t)
        return "\n\n".join(parts)
    except Exception:
        return ""


async def scrape_wikipedia(page: Page, company: str, wiki_slug: str) -> CompanyDoc | None:
    url = f"https://en.wikipedia.org/wiki/{wiki_slug}"
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_selector("#mw-content-text", timeout=8000)

        # Grab the intro paragraphs (before the first section header)
        paragraphs = await page.query_selector_all("#mw-content-text .mw-parser-output > p")
        intro_parts = []
        for p in paragraphs[:8]:
            text = (await p.inner_text()).strip()
            # Remove citation brackets like [1], [2]
            text = re.sub(r"\[\d+\]", "", text)
            if len(text) > 50:
                intro_parts.append(text)

        # Grab the infobox (key facts table)
        infobox_text = ""
        infobox = await page.query_selector(".infobox")
        if infobox:
            raw = (await infobox.inner_text()).strip()
            raw = re.sub(r"\[\d+\]", "", raw)
            infobox_text = f"\nKEY FACTS:\n{raw[:1500]}"

        full_text = "\n\n".join(intro_parts) + infobox_text
        if not full_text.strip():
            return None

        logger.info(f"  [{company}] Wikipedia: {len(full_text)} chars")
        return CompanyDoc(
            title=f"{company} — Company Overview",
            text=full_text[:4000],
            doc_type="company_overview",
            company_name=company,
            source_url=url,
        )
    except Exception as e:
        logger.warning(f"  [{company}] Wikipedia failed: {e}")
        return None


async def scrape_about_page(page: Page, company: str, domain: str) -> CompanyDoc | None:
    for path in ["/about", "/about-us", "/company", "/company/about"]:
        url = f"https://www.{domain}{path}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)

            text = await _get_all_text(page, "p, h1, h2, h3, li")
            text = re.sub(r"\s{3,}", "\n\n", text)
            if len(text) > 300:
                logger.info(f"  [{company}] About page ({path}): {len(text)} chars")
                return CompanyDoc(
                    title=f"{company} — About",
                    text=text[:4000],
                    doc_type="about",
                    company_name=company,
                    source_url=url,
                )
        except Exception:
            continue
    return None


async def scrape_leadership_page(page: Page, company: str, domain: str) -> CompanyDoc | None:
    for path in ["/company/leadership", "/about/leadership", "/team", "/company/team",
                 "/about/team", "/company/management", "/leadership"]:
        url = f"https://www.{domain}{path}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)

            text = await _get_all_text(page, "h1, h2, h3, h4, p, [class*='name'], [class*='title'], [class*='role']")
            text = re.sub(r"\s{3,}", "\n\n", text)
            if len(text) > 300:
                logger.info(f"  [{company}] Leadership page ({path}): {len(text)} chars")
                return CompanyDoc(
                    title=f"{company} — Leadership & Team",
                    text=text[:4000],
                    doc_type="leadership",
                    company_name=company,
                    source_url=url,
                )
        except Exception:
            continue
    return None


async def scrape_products_page(page: Page, company: str, domain: str) -> CompanyDoc | None:
    for path in ["/products", "/platform", "/features", "/solutions",
                 "/what-we-offer", "/product"]:
        url = f"https://www.{domain}{path}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)

            text = await _get_all_text(page, "h1, h2, h3, p, li")
            text = re.sub(r"\s{3,}", "\n\n", text)
            if len(text) > 300:
                logger.info(f"  [{company}] Products page ({path}): {len(text)} chars")
                return CompanyDoc(
                    title=f"{company} — Products & Features",
                    text=text[:4000],
                    doc_type="products",
                    company_name=company,
                    source_url=url,
                )
        except Exception:
            continue
    return None


async def scrape_company_full(company: str) -> list[CompanyDoc]:
    """Scrape all available data for one company."""
    info = COMPANY_SLUGS.get(company)
    if not info:
        logger.warning(f"No config for {company}")
        return []

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

        # 1. Wikipedia overview
        doc = await scrape_wikipedia(page, company, info["wiki"])
        if doc:
            docs.append(doc)

        # 2. About page
        doc = await scrape_about_page(page, company, info["web"])
        if doc:
            docs.append(doc)

        # 3. Leadership/Team page
        doc = await scrape_leadership_page(page, company, info["web"])
        if doc:
            docs.append(doc)

        # 4. Products/Features page
        doc = await scrape_products_page(page, company, info["web"])
        if doc:
            docs.append(doc)

        await context.close()
        await browser.close()

    logger.info(f"[{company}] Total docs scraped: {len(docs)}")
    return docs
