# Pydantic models
from pydantic import BaseModel
from typing import Optional, List

class IntentRequest(BaseModel):
    query: str

class IntentMatch(BaseModel):
    intent_id: str
    confidence: float
    allowed_operations: List[str]
    category: str = None
    source: str = None
    text: str = None

class IntentResponse(BaseModel):
    query: str
    matches: List[IntentMatch]
