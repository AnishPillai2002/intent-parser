"""
API routes for SQL intent ingestion.

This module exposes a FastAPI endpoint that triggers the SQL intent
ingestion pipeline. It acts as the boundary between external clients
(REST API) and the internal ingestion service logic.
"""

import logging
from fastapi import APIRouter, HTTPException

from app.models.ingestion import (
    IntentIngestionRequest,
    IntentIngestionResponse
)
from app.intents.ingest_service import ingest_intents_service

# -------------------------------------------------------------------
# Router configuration
# -------------------------------------------------------------------
# All ingestion-related endpoints are grouped under `/api/ingest`
# and tagged as "Ingestion" for better OpenAPI / Swagger visibility.
router = APIRouter(
    prefix="/api/ingest", 
    tags=["Ingestion"]
)

# -------------------------------------------------------------------
# Logger configuration
# -------------------------------------------------------------------
# Dedicated logger for ingestion API to separate it from
# service-layer and ingestion-pipeline logs.
logger = logging.getLogger("intent_ingestion_api")


# -------------------------------------------------------------------
# POST /api/ingest/intents
# -------------------------------------------------------------------
@router.post(
    "/intents",
    response_model=IntentIngestionResponse
)
def ingest_sql_intents(request: IntentIngestionRequest):
    """
    Trigger SQL intent ingestion.

    This endpoint:
    - Accepts ingestion configuration flags (dry_run, force)
    - Delegates execution to the ingestion service layer
    - Returns a structured, API-safe response

    Parameters
    ----------
    request : IntentIngestionRequest
        Request payload controlling ingestion behavior.
        - dry_run: validates pipeline without storing data
        - force: allows re-ingestion of existing intents

    Returns
    -------
    IntentIngestionResponse
        Structured response containing:
        - ingestion status
        - number of intents ingested
        - number of vectors stored
        - human-readable message

    Raises
    ------
    HTTPException
        Returns HTTP 500 if ingestion fails unexpectedly.
    """
    
    try:
        logger.info(
            f"Intent ingestion triggered | "
            f"force={request.force} | dry_run={request.dry_run}"
        )
        
        # -----------------------------------------------------------
        # Delegate ingestion to service layer
        # -----------------------------------------------------------
        # Business logic is intentionally NOT placed in the API layer.
        # This allows reuse from:
        # - CLI tools
        # - Background jobs
        # - Scheduled tasks
        result = ingest_intents_service(
            dry_run=request.dry_run
        )

         # -----------------------------------------------------------
        # Convert service response into API response model
        # -----------------------------------------------------------
        # This ensures:
        # - Schema validation
        # - OpenAPI documentation accuracy
        # - Consistent API responses
        return IntentIngestionResponse(
            status=result["status"],
            intents_ingested=result["intents"],
            vectors_stored=result["vectors"],
            message=result["message"],
            dry_run=request.dry_run
        )

    except Exception as e:
        # -----------------------------------------------------------
        # Error handling
        # -----------------------------------------------------------
        # Any unhandled exception is logged with full stack trace
        # and converted into a generic HTTP 500 response.
        logger.exception("Intent ingestion failed")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
