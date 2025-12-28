from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

# Import the service singleton
from app.services.llm.sql_generation import sql_generator
from app.utils.logging_util import logger

# Create Router
router = APIRouter(
    prefix="/api", 
    tags=["SQL Generation"]
)

# --- Request Model ---
class GenerateSQLRequest(BaseModel):
    query: str = Field(..., example="Show me the top 5 products by revenue")
    provider: str = Field("gemini", example="gemini", description="LLM provider to use")
    
# --- Response Model ---
class GenerateSQLResponse(BaseModel):
    status: str
    user_query: str
    generated_sql: str
    provider: str
    meta: Optional[Dict[str, Any]] = None

# -------------------------------------------------------------------
# POST /api/generate-sql
# -------------------------------------------------------------------
@router.post("/generate-sql", response_model=GenerateSQLResponse)
async def generate_sql_endpoint(request: GenerateSQLRequest):
    """
    Generates a SQL query from natural language.
    
    Orchestrates:
    1. Schema Retrieval
    2. Intent Classification
    3. LLM Generation (Gemini/Custom)
    """
    try:
        logger.info(f"SQL Generation Request: '{request.query}' [{request.provider}]")
        
        # Call the service layer
        result = await sql_generator.generate_query(
            user_query=request.query,
            provider=request.provider
        )

        return GenerateSQLResponse(
            status="success",
            user_query=request.query,
            generated_sql=result["sql"],
            provider=request.provider,
            meta=result["context"]  # Useful for frontend debugging
        )

    except ValueError as ve:
        # Graceful handling of bad provider names
        logger.warning(f"Bad Request: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
        
    except Exception as e:
        # Catch-all for LLM failures or Service errors
        logger.exception("Critical failure in SQL generation endpoint")
        raise HTTPException(status_code=500, detail="Failed to generate SQL query. Please try again.")