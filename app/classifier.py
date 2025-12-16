# Intent classification
from app.qdrant_client import client, COLLECTION_NAME
from app.embeddings import embed_text

CONFIDENCE_THRESHOLD = 0.00

def classify_query(query: str):
    vector = embed_text(query)

    result = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=1
    )

    if not result.points:
        return {"operation": "UNKNOWN", "confidence": 0.0}

    hit = result.points[0]

    if hit.score < CONFIDENCE_THRESHOLD:
        return {
            "operation": "UNKNOWN",
            "confidence": hit.score
        }

    return {
        "operation": hit.payload["operation"],
        "category": hit.payload["category"],
        "confidence": hit.score
    }
