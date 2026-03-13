import hashlib


def content_fingerprint(index: str, text: str) -> str:
    """
    Deterministic 24-char hex ID derived from (index, content).
    Used as Elasticsearch _id with op_type='create' to silently
    reject duplicate documents rather than overwriting them.
    """
    payload = f"{index}:{text.strip()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
