from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import the service singleton
from app.services.db_schema.schema_loader import schema_ingestion_service

router = APIRouter(
    prefix="/api/schema",
    tags=["Schema Ingestion"]
)

class IngestRequest(BaseModel):
    db_connection_string: str 

# -------------------------------------------------------------------
# POST /api/ingest-schema
# -------------------------------------------------------------------
@router.post(
        "/ingest-schema",
        response_model=dict
)
async def ingest_schema(request: IngestRequest):
    """
    Connects to the provided DB URL, extracts schema, and stores it as vector embeddings.
    """
    if not request.db_connection_string:
        raise HTTPException(status_code=400, detail="Database connection string required")
            
    print(f"Starting ingestion for: {request.db_connection_string}")

    try:
        # 1. Instantiate the service with the provided connection string
        # NOTE: We need to update SchemaIngestionService to accept this argument
        # 2. CALL the function (add parentheses!)
        count = schema_ingestion_service.run_ingestion(db_url=request.db_connection_string)
        
        return {
            "status": "success", 
            "tables_processed": count,
            "message": "Schema successfully stored in Qdrant."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))