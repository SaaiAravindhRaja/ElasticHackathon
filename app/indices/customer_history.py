INDEX_NAME = "customer-history-index"

MAPPING = {
    "mappings": {
        "properties": {
            "source_type": {"type": "keyword"},
            "raw_text": {"type": "text", "analyzer": "english"},
            "text_embedding": {
                "type": "dense_vector",
                "dims": 1536,
                "index": True,
                "index_options": {"type": "int8_hnsw"},
                "similarity": "dot_product",
            },
            "extracted_features": {"type": "object", "dynamic": True},
            "sentiment": {"type": "keyword"},
            "customer_id": {"type": "keyword"},
            "timestamp": {"type": "date"},
            "subject": {"type": "text", "analyzer": "english"},
            "chunk_id": {"type": "integer"},
            "conversation_id": {"type": "keyword"},
            "intent": {"type": "keyword"},
            "topics": {"type": "keyword"},
        }
    },
}
