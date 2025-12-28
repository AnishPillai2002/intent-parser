from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

# Import the service singleton
from app.services.db_schema.schema_retrieval import schema_retrieval_service

router = APIRouter(
    prefix="/api/schema", 
    tags=["Schema Retrieval"]
)

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class QueryResponse(BaseModel):
    context: Dict[str, Any]

# -------------------------------------------------------------------
# POST /api/schema/retrieval
# -------------------------------------------------------------------
@router.post("/retrieval", response_model=QueryResponse)
async def get_schema_context(request: QueryRequest):
    """
    Endpoint to retrieve contextualized schema based on a natural language query.
    """
    try:
        context = schema_retrieval_service.retrieve_relevant_schema(
            user_query=request.query, 
            top_k=request.top_k
        )
        return QueryResponse(context=context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
