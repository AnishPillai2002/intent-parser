from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.schema_ingestion.schema_retrieval import SchemaRetrievalService

router = APIRouter(
    prefix="/api/schema", 
    tags=["Schema Retrieval"]
)

# Initialize the service
retrieval_service = SchemaRetrievalService()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 15

class QueryResponse(BaseModel):
    context: str

@router.post("/retrieval", response_model=QueryResponse)
async def get_schema_context(request: QueryRequest):
    """
    Endpoint to retrieve contextualized schema based on a natural language query.
    """
    try:
        context = retrieval_service.retrieve_relevant_schema(
            user_query=request.query, 
            top_k=request.top_k
        )
        return QueryResponse(context=context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
