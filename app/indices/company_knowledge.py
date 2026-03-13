INDEX_NAME = "company-knowledge-index"

MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
    "mappings": {
        "properties": {
            "title": {"type": "text", "analyzer": "english"},
            "text": {"type": "text", "analyzer": "english"},
            "text_embedding": {
                "type": "dense_vector",
                "dims": 1536,
                "index": True,
                "index_options": {"type": "int8_hnsw"},
                "similarity": "dot_product",
            },
            "doc_type": {"type": "keyword"},
            "source_url": {"type": "keyword"},
            "metadata": {"type": "object", "dynamic": True},
            "timestamp": {"type": "date"},
            "chunk_id": {"type": "integer"},
            "total_chunks": {"type": "integer"},
            "document_id": {"type": "keyword"},
        }
    },
}
