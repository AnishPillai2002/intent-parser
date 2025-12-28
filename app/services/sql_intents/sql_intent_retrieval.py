from typing import List, Dict, Any
from app.vectorstore.qdrant_client import client
from app.config import settings
from app.utils.logging_util import logger  # Using your centralized logger
from app.services.embedding.embedding import embedding_service
class SQLIntentRetrievalService:
    """
    Service class to handle the retrieval (search) of SQL intents from Qdrant.
    
    This class encapsulates:
    - Query embedding generation
    - Vector search execution (finding nearest neighbors)
    - Result formatting and cleaning
    """

    def __init__(self):
        self.logger = logger

    def get_top_intents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Converts a natural language query into a vector and retrieves 
        the top N most similar intent definitions from Qdrant.

        Args:
            query (str): The user's natural language question.
            limit (int): The maximum number of results to return.

        Returns:
            List[Dict[str, Any]]: A list of ranked search results with scores and metadata.
        """
        self.logger.info(f"Performing direct search for: '{query}'")

        try:
            # 1. Generate the embedding for the user query
            #    This converts text like "Show me users" into a vector [0.12, -0.98, ...]
            query_vector = embedding_service.embed_text(query)

            # 2. Query Qdrant using the modern query_points API
            #    We retrieve only the payload (metadata) and not the vectors themselves
            response = client.query_points(
                collection_name=settings.COLLECTION_NAME,
                query=query_vector,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )

            # 3. Format the results for readability
            #    We strip out complex Qdrant objects and return clean dictionaries
            results = []
            for hit in response.points:
                results.append({
                    "id": hit.id,
                    "score": round(hit.score, 4),  # Rounding score for cleaner UI display
                    "payload": hit.payload
                })

            self.logger.info(f"Successfully retrieved {len(results)} points.")
            return results

        except Exception as e:
            # Log the full stack trace for debugging
            self.logger.exception(f"Search failed for query '{query}'")
            return []

# ---------------------------------------------------------
# SINGLETON INSTANCE
# ---------------------------------------------------------
intent_retrieval_service = SQLIntentRetrievalService()