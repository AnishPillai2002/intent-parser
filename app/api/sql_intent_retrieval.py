from fastapi import APIRouter, HTTPException
from app.services.sql_intents.sql_intent_retrieval import intent_retrieval_service
from app.models.sql_intent.request_response import IntentRequest, IntentResponse, IntentMatch

# Import the service singleton
from app.utils.logging_util import logger

router = APIRouter(
    prefix="/api/intent", 
    tags=["SQL Intent Retrieval"]
)

# -------------------------------------------------------------------
# POST /api/intent/classify-intent
# -------------------------------------------------------------------
@router.post("/classify-intent", response_model=IntentResponse)
def classify_intent(req: IntentRequest):
    """
    Classifies a natural language query into specific SQL intents.
    """
    logger.info(f"--- Intent Classification Start: '{req.query}' ---")
    
    # Fetch top intents (Using Singleton)
    top_hits = intent_retrieval_service.get_top_intents(req.query, limit=5)
    
    if not top_hits:
        # Logger handles timestamp and formatting automatically
        logger.warning(f"Search returned 0 hits for query: '{req.query}'")
        raise HTTPException(status_code=404, detail="No matching intent found")

    # Map hits to Response Model
    results = []
    for hit in top_hits:
        payload = hit["payload"]
        score = hit["score"]
        
        # Determine allowed operations
        operation = payload.get("operation")
        allowed_ops = [operation] if operation else ["SELECT_BASIC"]
        
        # Build the match object
        match_data = IntentMatch(
            intent_id=str(payload.get("intent_id", "unknown")), 
            confidence=score,
            allowed_operations=allowed_ops,
            category=payload.get("category"),
            source=payload.get("source"),
            text=payload.get("text")
        )
        results.append(match_data)

    # Final Logging & Return
    if results:
        top_match = results[0]
        logger.info(
            f"Top Match: {top_match.intent_id} | "
            f"Conf: {top_match.confidence:.4f} | "
            f"Op: {top_match.allowed_operations[0]}"
        )

    return IntentResponse(
        query=req.query,
        matches=results
    )