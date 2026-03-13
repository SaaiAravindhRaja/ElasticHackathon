INDEX_NAME = "market-intelligence-index"

MAPPING = {
    "mappings": {
        "properties": {
            "source_site": {"type": "keyword"},
            "company_name": {"type": "keyword"},
            "review_text": {"type": "text", "analyzer": "english"},
            "text_embedding": {
                "type": "dense_vector",
                "dims": 1536,
                "index": True,
                "index_options": {"type": "int8_hnsw"},
                "similarity": "dot_product",
            },
            "rating": {"type": "float"},
            "sentiment": {"type": "keyword"},
            "reviewer": {"type": "keyword"},
            "date": {"type": "date", "ignore_malformed": True},
            "url": {"type": "keyword"},
            "pros": {"type": "text", "analyzer": "english"},
            "cons": {"type": "text", "analyzer": "english"},
        }
    },
}
