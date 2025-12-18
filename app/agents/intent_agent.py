import logging
from typing import TypedDict, List, Dict, Any, Optional
from collections import defaultdict
from langgraph.graph import StateGraph, END
from qdrant_client.models import Filter # Kept for potential future use

# Internal project imports
from app.vectorstore.qdrant_client import client
from app.config import COLLECTION_NAME
from app.embeddings.embedder import embed_text

# Configure logger
logger = logging.getLogger("intent_agent")
logging.basicConfig(level=logging.INFO)

class IntentState(TypedDict):
    query: str
    vector_hits: List[Any]
    intent_scores: Dict[int, float]
    final_intent_id: Optional[int]
    confidence: Optional[float]

# --- Nodes ---

def embedding_search_node(state: IntentState) -> Dict[str, Any]:
    """Performs direct semantic search against the full Qdrant collection."""
    query_text = state["query"]
    logger.info(f"[NODE: embedding_search] Initiating direct semantic search for: '{query_text}'")

    try:
        # Convert text query to vector
        query_vector = embed_text(query_text)

        # Search without 'query_filter' to allow full semantic discovery
        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=10,
            with_payload=True,
        )
        
        hits = response.points
        logger.info(f"[NODE: embedding_search] Search complete. Found {len(hits)} raw hits.")
        return {"vector_hits": hits}
        
    except Exception as e:
        logger.error(f"[NODE: embedding_search] Critical failure during Qdrant search: {str(e)}")
        return {"vector_hits": []}


def voting_node(state: IntentState) -> Dict[str, Any]:
    """Calculates weighted confidence based on hit source and cosine similarity."""
    logger.info("[NODE: voting] Analyzing hit relevance and source weights")
    scores = defaultdict(float)
    hits = state.get("vector_hits", [])

    if not hits:
        logger.warning("[NODE: voting] No hits to process.")
        return {"final_intent_id": None, "confidence": 0.0}

    # Weights determine how much we trust different types of data in our DB
    source_weights = {
        "description": 1.0, # High trust for official intent descriptions
        "example": 0.9,     # High trust for user examples
        "paraphrase": 0.7,  # Moderate trust for AI-generated paraphrases
        "keyword": 0.4,     # Lower trust for single keyword matches
    }

    for hit in hits:
        payload = hit.payload or {}
        intent_id = payload.get("intent_id")
        source = payload.get("source", "unknown") 
        weight = source_weights.get(source, 0.5)
        
        # Weighted Score = Cosine Similarity * Source Reliability
        contribution = hit.score * weight
        
        if intent_id is not None:
            scores[intent_id] += contribution

    if not scores:
        logger.error("[NODE: voting] No valid 'intent_id' found in payload of search hits.")
        return {"final_intent_id": None, "confidence": 0.0}

    # Determine winner
    best_intent = max(scores, key=scores.get)
    total_score = sum(scores.values())
    confidence = round(scores[best_intent] / total_score, 4)

    logger.info(f"[NODE: voting] Winner: Intent {best_intent} | Confidence: {confidence}")
    logger.info(f"[NODE: voting] Full score distribution: {dict(scores)}")
    
    return {
        "intent_scores": dict(scores),
        "final_intent_id": best_intent,
        "confidence": confidence
    }


def confidence_check_node(state: IntentState) -> Dict[str, Any]:
    """Ensures the top result meets the minimum quality bar."""
    conf = state.get("confidence", 0)
    intent_id = state.get("final_intent_id")
    
    THRESHOLD = 0.4
    logger.info(f"[NODE: confidence] Safety check for Intent {intent_id} (Score: {conf})")

    if intent_id is None or conf < THRESHOLD:
        logger.warning(f"[NODE: confidence] REJECTED: Score {conf} < Threshold {THRESHOLD}")
        return {"final_intent_id": None}
    
    logger.info(f"[NODE: confidence] SUCCESS: Intent {intent_id} verified.")
    return {"final_intent_id": intent_id}

# --- Graph Assembly ---

workflow = StateGraph(IntentState)

# Define nodes
workflow.add_node("embedding_search", embedding_search_node)
workflow.add_node("voting", voting_node)
workflow.add_node("confidence", confidence_check_node)

# Define flow
workflow.set_entry_point("embedding_search")
workflow.add_edge("embedding_search", "voting")
workflow.add_edge("voting", "confidence")
workflow.add_edge("confidence", END)

# Compile
intent_agent = workflow.compile()