from fastapi import APIRouter, HTTPException
from app.services.sql_intents.sql_intent_loader import SQLIntentIngestionService
from app.models.sql_intent.ingestion import (
    IntentIngestionRequest,
    IntentIngestionResponse
)

# Import the service singleton
from app.utils.logging_util import logger

router = APIRouter(
    prefix="/api/intent", 
    tags=["SQL IntentIngestion"]
)

# -------------------------------------------------------------------
# POST /api/intent/ingest-intents
# -------------------------------------------------------------------
@router.post(
    "/ingest-intents",
    response_model=IntentIngestionResponse
)
def ingest_sql_intents(request: IntentIngestionRequest):
    """
    Trigger SQL intent ingestion.

    This endpoint delegates execution to the intent ingestion service layer
    and returns a structured, API-safe response.
    """

    try:
        logger.info(
            f"Intent ingestion triggered | "
            f"force={request.force} | dry_run={request.dry_run}"
        )
        
        # Delegate ingestion to service layer (Singleton)
        intent_ingestion_service = SQLIntentIngestionService()
        result = intent_ingestion_service.run(
            dry_run=request.dry_run
        )

        # Convert service response into API response model
        return IntentIngestionResponse(
            status=result["status"],
            intents_ingested=result["intents"],
            vectors_stored=result["vectors"],
            message=result["message"],
            dry_run=request.dry_run
        )

    except Exception as e:
        logger.exception("Intent ingestion API failed")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )