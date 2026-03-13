"""
Elasticsearch percolator index for registered alert queries.

The percolator type stores a query as a document. When new documents are
ingested, they can be percolated against all stored queries to find matches —
essentially real-time saved-search alerting.
"""

INDEX_NAME = "elasticcx-alerts"

MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
    "mappings": {
        "properties": {
            "name": {"type": "keyword"},
            "description": {"type": "text"},
            "target_index": {"type": "keyword"},
            # The percolator field stores an ES query as a document.
            # Incoming documents are matched against all stored queries.
            "query": {"type": "percolator"},
            "created_at": {"type": "date"},
        }
    },
}
