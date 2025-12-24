from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.schema_ingestion.schema_loader import SchemaIngestionService

router = APIRouter(
    prefix="/api/ingest",
    tags=["SchemaIngestion"]
)

class IngestRequest(BaseModel):
    db_connection_string: str 

@router.post(
        "/schema",
        response_model=dict
)
async def ingest_schema(request: IngestRequest):
    """
    Connects to the provided DB URL, extracts schema, and stores it in Qdrant.
    """
    if not request.db_connection_string:
        raise HTTPException(status_code=400, detail="Database connection string required")
            
    print(f"Starting ingestion for: {request.db_connection_string}")

    try:
        # 1. Instantiate the service with the provided connection string
        # NOTE: We need to update SchemaIngestionService to accept this argument
        service = SchemaIngestionService(db_url=request.db_connection_string)

        # 2. CALL the function (add parentheses!)
        count = service.run_ingestion()
        
        return {
            "status": "success", 
            "tables_processed": count,
            "message": "Schema successfully stored in Qdrant."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))