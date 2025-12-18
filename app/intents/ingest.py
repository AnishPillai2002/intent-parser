# app/intents/ingest.py
"""
This module is responsible for ingesting SQL intent definitions
into a Qdrant vector database.

Each intent is represented by multiple textual forms:
- A primary description
- Example queries
- Paraphrases
- Keywords

All texts are embedded once, deduplicated, and stored as vectors
with deterministic IDs to ensure idempotent ingestion.
"""

import logging
from qdrant_client.models import PointStruct

from app.intents.sql_intents import SQL_INTENTS
from app.config import COLLECTION_NAME
from app.embeddings.embedder import batch_embed
from app.vectorstore.qdrant_client import client, ensure_collection
from app.utils.idempotent_id import make_id


# ============================================================
# Logger Configuration
# ============================================================
# A dedicated logger helps isolate ingestion logs from other
# application logs and makes debugging ingestion issues easier.
logger = logging.getLogger("intent_ingestion")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s"
)
handler.setFormatter(formatter)

# Prevent duplicate handlers when the module is imported multiple times
if not logger.handlers:
    logger.addHandler(handler)


# ============================================================
# Main Ingestion Function
# ============================================================
def ingest_intents():
    """
    Ingest all SQL intents into the Qdrant vector store.

    High-level flow:
    1. Collect all textual variants from SQL intents
    2. Deduplicate and batch-embed texts
    3. Ensure Qdrant collection exists
    4. Store vectors with deterministic IDs and rich metadata
    """
    logger.info("Starting SQL intent ingestion into Qdrant...")
    
    # --------------------------------------------------------
    # Step 1: Collect all texts to be embedded
    # --------------------------------------------------------
    # We gather *every* textual representation across all intents
    # first so that embeddings can be generated in one batch.
    #
    # This is:
    # - Faster (batch embedding)
    # - Cheaper (fewer API calls)
    # - Safer (consistent embedding model usage)
    all_texts = []

    # Tracks how many texts are associated with each intent
    # (useful for debugging or analytics)
    intent_text_counts = {}

    for intent in SQL_INTENTS:
        count = 0

        # Primary intent description
        all_texts.append(intent["text"])
        count += 1

        # Natural-language examples
        for ex in intent.get("examples", []):
            all_texts.append(ex)
            count += 1

        # Paraphrased variations
        for para in intent.get("paraphrases", []):
            all_texts.append(para)
            count += 1

        # Keyword-level hints
        for kw in intent.get("keywords", []):
            all_texts.append(kw)
            count += 1

        intent_text_counts[intent["id"]] = count

    logger.info(f"Collected {len(all_texts)} texts for embedding.")

    # --------------------------------------------------------
    # Step 2: Generate embeddings (deduplicated)
    # --------------------------------------------------------
    # Deduplication is critical because:
    # - Multiple intents may share keywords
    # - Repeated texts should not be embedded multiple times
    # - It reduces cost and memory usage
    all_texts = list(set(all_texts))

    logger.info("Generating embeddings...")
    vectors = batch_embed(all_texts)

    # Create a direct text → vector lookup map.
    # This eliminates fragile index-based alignment logic.
    text_vector_map = dict(zip(all_texts, vectors))

    if not vectors:
        logger.error("Embedding generation failed: no vectors returned.")
        return

    logger.info(f"Embedding dimension: {len(vectors[0])}")

    # --------------------------------------------------------
    # Step 3: Ensure Qdrant collection exists
    # --------------------------------------------------------
    # This function typically:
    # - Creates the collection if missing
    # - Verifies vector size and distance metric
    # - Is safe to call multiple times (idempotent)
    ensure_collection()
    logger.info("Qdrant collection ensured.")

    # --------------------------------------------------------
    # Step 4: Upsert intent vectors into Qdrant
    # --------------------------------------------------------
    # Each intent produces multiple vector points,
    # one per textual representation.
    total_points = 0

    for intent in SQL_INTENTS:
        points = []

        def add_point(text: str, source: str):
            """
            Create and append a Qdrant PointStruct for a given text.

            Args:
                text: The original text being embedded
                source: Where the text came from
                        (description | example | paraphrase | keyword)
            """
            nonlocal total_points

            points.append(
                PointStruct(
                    # Deterministic ID ensures idempotent ingestion:
                    # re-running ingestion updates, not duplicates.
                    id=make_id(intent["id"], source, text),

                    # Safe lookup via text → vector mapping
                    vector=text_vector_map[text],

                    # Rich metadata for filtering & debugging
                    payload={
                        "intent_id": intent["id"],
                        "operation": intent["operation"],
                        "category": intent["category"],
                        "complexity": intent["complexity"],
                        "source": source,
                        "text": text
                    }
                )
            )
            total_points += 1

        # Primary description vector
        add_point(intent["text"], "description")

        # Example vectors
        for ex in intent.get("examples", []):
            add_point(ex, "example")

        # Paraphrase vectors
        for para in intent.get("paraphrases", []):
            add_point(para, "paraphrase")

        # Keyword vectors
        for kw in intent.get("keywords", []):
            add_point(kw, "keyword")

        # Upsert all points for this intent in one call
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )

        logger.info(
            f"Stored intent_id={intent['id']} "
            f"({intent['operation']}) "
            f"with {len(points)} vectors."
        )

    # --------------------------------------------------------
    # Step 5: Final confirmation
    # --------------------------------------------------------
    logger.info("==========================================")
    logger.info("SQL INTENT INGESTION COMPLETED SUCCESSFULLY")
    logger.info(f"Total intents ingested: {len(SQL_INTENTS)}")
    logger.info(f"Total vectors stored: {total_points}")
    logger.info("==========================================")

    return {
        "intents": len(SQL_INTENTS),
        "vectors": total_points
    }
