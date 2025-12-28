from typing import Dict, Any, Optional, List
from qdrant_client.models import PointStruct

# ---------------------------------------------------------
# CUSTOM LOGGER IMPORT
# ---------------------------------------------------------
from app.utils.logging_util import logger  # Imported from your custom utility

# ---------------------------------------------------------
# APP IMPORTS
# ---------------------------------------------------------
from app.definitions import SQL_INTENTS
from app.config import settings
from app.services.embedding.embedding import embedding_service
from app.vectorstore.qdrant_client import client, ensure_collection
from app.utils.idempotent_id import make_id


class SQLIntentIngestionService:
    """
    Service class to handle the ingestion of SQL intents into Qdrant.
    
    This class encapsulates:
    - Service Layer Logic: Dry-runs, error handling, response formatting.
    - Core Business Logic: Text collection, embedding, and vector upsertion.
    """

    def __init__(self):
        # Use the centralized custom logger
        self.logger = logger

    # ---------------------------------------------------------
    # PUBLIC ENTRY POINT
    # ---------------------------------------------------------
    def run(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Executes the intent ingestion process.

        Args:
            dry_run (bool): If True, returns success without modifying the database.

        Returns:
            Dict[str, Any]: A structured API response dictionary.
        """
        # 1. Handle Dry Run
        if dry_run:
            self.logger.info("Dry run requested. Skipping actual ingestion.")
            return {
                "status": "success",
                "dry_run": True,
                "intents": 0,
                "vectors": 0,
                "message": "Dry run successful. No data ingested."
            }

        # 2. Execute Ingestion Pipeline
        try:
            stats = self._execute_ingestion()
        except Exception as exc:
            # .exception() automatically logs the full traceback
            self.logger.exception("Ingestion failed with an unexpected error.")
            return {
                "status": "error",
                "dry_run": False,
                "intents": 0,
                "vectors": 0,
                "message": f"Intent ingestion failed: {str(exc)}"
            }

        # 3. Validate Results
        if not stats:
            return {
                "status": "error",
                "dry_run": False,
                "intents": 0,
                "vectors": 0,
                "message": "Ingestion completed but returned no statistics (possible embedding failure)."
            }

        # 4. Return Success
        return {
            "status": "success",
            "dry_run": False,
            "intents": stats["intents"],
            "vectors": stats["vectors"],
            "message": "SQL intents ingested successfully"
        }

    # ---------------------------------------------------------
    # INTERNAL CORE LOGIC
    # ---------------------------------------------------------
    def _execute_ingestion(self) -> Optional[Dict[str, int]]:
        """
        Internal logic to collect texts, generate embeddings, and upsert to Qdrant.
        """
        self.logger.info("Starting SQL intent ingestion into Qdrant...")

        # --- Step 1: Collect texts ---
        all_texts = self._collect_all_texts()
        self.logger.info(f"Collected {len(all_texts)} raw texts.")

        # --- Step 2: Deduplicate & Embed ---
        unique_texts = list(set(all_texts))
        self.logger.info(f"Generating embeddings for {len(unique_texts)} unique texts...")

        vectors = embedding_service.batch_embed(unique_texts)

        if not vectors:
            self.logger.error("Embedding generation failed: no vectors returned.")
            return None

        # Map text -> vector for O(1) lookup
        text_vector_map = dict(zip(unique_texts, vectors))
        self.logger.info(f"Embedding dimension: {len(vectors[0])}")

        # --- Step 3: Ensure Collection & Upsert ---
        ensure_collection()
        
        total_points = self._upsert_intents(text_vector_map)

        # --- Step 4: Final Stats ---
        self.logger.info("=== INGESTION COMPLETE ===")
        self.logger.info(f"Intents: {len(SQL_INTENTS)} | Vectors: {total_points}")

        return {
            "intents": len(SQL_INTENTS),
            "vectors": total_points
        }

    def _collect_all_texts(self) -> List[str]:
        """Helper to gather all text variants from the intent definitions."""
        texts = []
        for intent in SQL_INTENTS:
            texts.append(intent["text"])
            texts.extend(intent.get("examples", []))
            texts.extend(intent.get("paraphrases", []))
            texts.extend(intent.get("keywords", []))
        return texts

    def _upsert_intents(self, text_vector_map: Dict[str, List[float]]) -> int:
        """Helper to build points and upsert them into Qdrant."""
        total_points = 0
        
        for intent in SQL_INTENTS:
            points = []
            intent_id = intent["id"]

            # Nested helper to build a single point
            def add_point(text_val, source_type):
                nonlocal total_points
                points.append(
                    PointStruct(
                        id=make_id(intent_id, source_type, text_val),
                        vector=text_vector_map[text_val],
                        payload={
                            "intent_id": intent_id,
                            "operation": intent["operation"],
                            "category": intent["category"],
                            "complexity": intent["complexity"],
                            "source": source_type,
                            "text": text_val
                        }
                    )
                )
                total_points += 1

            # Build points
            add_point(intent["text"], "description")
            for ex in intent.get("examples", []): add_point(ex, "example")
            for para in intent.get("paraphrases", []): add_point(para, "paraphrase")
            for kw in intent.get("keywords", []): add_point(kw, "keyword")

            # Upsert batch
            client.upsert(
                collection_name=settings.COLLECTION_NAME,
                points=points
            )
            # Typically debug logs are good for loops, so it doesn't flood INFO logs
            self.logger.debug(f"Stored intent {intent_id} with {len(points)} vectors.")
            
        return total_points
