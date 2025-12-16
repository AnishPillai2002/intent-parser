# Pydantic data point schema validation
from pydantic import BaseModel
from typing import List


class SQLIntentPoint(BaseModel):
    id: int
    operation: str
    category: str
    description: str
    examples: List[str]
    sql_syntax: List[str]