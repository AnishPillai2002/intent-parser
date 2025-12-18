import logging
from typing import List, Dict, Any
from app.vectorstore.qdrant_client import client
from app.config import COLLECTION_NAME
from app.embeddings.embedder import embed_text

# Configure local logging
logger = logging.getLogger("qdrant_search")

def get_top_intents(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Directly converts a query to a vector and retrieves the top N 
    most similar points from Qdrant.
    """
    logger.info(f"Performing direct search for: '{query}'")

    try:
        # 1. Generate the embedding for the user query
        query_vector = embed_text(query)

        # 2. Query Qdrant using the modern query_points API
        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=limit,
            with_payload=True,
            with_vectors=False  # Set to True if you need the raw coordinates
        )

        # 3. Format the results for readability
        results = []
        for hit in response.points:
            results.append({
                "id": hit.id,
                "score": round(hit.score, 4),
                "payload": hit.payload
            })

        logger.info(f"Successfully retrieved {len(results)} points.")
        return results

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        return []