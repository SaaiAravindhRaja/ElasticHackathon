"""
Elasticsearch percolator index for registered alert queries.

The percolator type stores a query as a document. When new documents are
ingested, they can be percolated against all stored queries to find matches —
essentially real-time saved-search alerting.
"""

INDEX_NAME = "elasticcx-alerts"

MAPPING = {
    "mappings": {
        # dynamic=true lets ES auto-create mappings for any new fields referenced
        # in percolator queries — required so queries against any target index field work.
        "dynamic": True,
        "properties": {
            # --- percolator admin fields ---
            "name": {"type": "keyword"},
            "description": {"type": "text"},
            "target_index": {"type": "keyword"},
            "query": {"type": "percolator"},
            "created_at": {"type": "date"},
            # --- mirror of company-knowledge-index fields ---
            "title": {"type": "text", "analyzer": "english"},
            "text": {"type": "text", "analyzer": "english"},
            "doc_type": {"type": "keyword"},
            # --- mirror of market-intelligence-index fields ---
            "review_text": {"type": "text", "analyzer": "english"},
            "company_name": {"type": "keyword"},
            "source_site": {"type": "keyword"},
            "rating": {"type": "float"},
            "sentiment": {"type": "keyword"},
            "pros": {"type": "text", "analyzer": "english"},
            "cons": {"type": "text", "analyzer": "english"},
            # --- mirror of customer-history-index fields ---
            "raw_text": {"type": "text", "analyzer": "english"},
            "source_type": {"type": "keyword"},
            "intent": {"type": "keyword"},
            "topics": {"type": "keyword"},
            "customer_id": {"type": "keyword"},
        },
    },
}
