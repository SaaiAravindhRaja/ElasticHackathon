"""
Standalone script — connect to Elasticsearch Cloud and create all three indices.
Run once after setting up .env:

    python scripts/create_indices.py
"""
import asyncio
import sys
import os

# Allow running from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from elasticsearch import AsyncElasticsearch
from app.config import get_settings
from app.indices.company_knowledge import INDEX_NAME as COMPANY_INDEX, MAPPING as COMPANY_MAPPING
from app.indices.market_intelligence import INDEX_NAME as MARKET_INDEX, MAPPING as MARKET_MAPPING
from app.indices.customer_history import INDEX_NAME as HISTORY_INDEX, MAPPING as HISTORY_MAPPING


async def main():
    settings = get_settings()
    client = AsyncElasticsearch(
        cloud_id=settings.es_cloud_id,
        api_key=settings.es_api_key,
        request_timeout=30,
    )

    try:
        info = await client.info()
        print(f"Connected to cluster: {info['cluster_name']} (ES {info['version']['number']})")

        for name, mapping in [
            (COMPANY_INDEX, COMPANY_MAPPING),
            (MARKET_INDEX, MARKET_MAPPING),
            (HISTORY_INDEX, HISTORY_MAPPING),
        ]:
            exists = await client.indices.exists(index=name)
            if not exists:
                await client.indices.create(index=name, body=mapping)
                print(f"  Created: {name}")
            else:
                print(f"  Already exists: {name}")

        print("\nAll indices ready.")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
