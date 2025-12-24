import logging
import json
from fastapi import APIRouter, HTTPException
from app.models.request_response import IntentRequest, IntentResponse,IntentMatch
from app.intent_search.semantic_search import get_top_intents

# Use the name defined in LogConfig.LOGGER_NAME
logger = logging.getLogger("my_app")

router = APIRouter(prefix="/api")

@router.post("/classify-intent", response_model=IntentResponse)
def classify_intent(req: IntentRequest):
    logger.info(f"--- Intent Classification Start: '{req.query}' ---")
    
    # 1. Fetch the top 5 intents from Qdrant
    top_hits = get_top_intents(req.query, limit=5)
    if not top_hits:
        logger.error(f"Search returned 0 hits for query: '{req.query}'")
        raise HTTPException(status_code=404, detail="No matching intent found")

    # 2. Map the hits into a list of IntentMatch objects
    results = []
    for hit in top_hits:
        payload = hit["payload"]
        score = hit["score"]
        
        # Determine allowed operations
        operation = payload.get("operation")
        allowed_ops = [operation] if operation else ["SELECT_BASIC"]
        
        # Build the match object
        # Inside your loop in classify_intent
        match_data = IntentMatch(
            # Force the intent_id to be a string
            intent_id=str(payload.get("intent_id", "unknown")), 
            confidence=score,
            allowed_operations=allowed_ops,
            category=payload.get("category"),
            source=payload.get("source"),
            text=payload.get("text")
        )
        results.append(match_data)

    # 3. Log the top result for quick monitoring
    if results:
        logger.info(f"Top Result: {results[0].intent_id} (Score: {results[0].confidence:.4f})")

    # 4. Return the structured response containing all 5 points
    return IntentResponse(
        query=req.query,
        matches=results
    )