# FastAPI entry point
from fastapi import FastAPI
from typing import List
from fastapi.staticfiles import StaticFiles

from app.schemas.schemas import SQLIntentPoint
from app.storage import store_sql_intents, store_dynamic_intents
from app.classifier import classify_query


app = FastAPI(
    title="SQL Intent Parser API",
    description="API for storing SQL intent embeddings and classifying user queries",
    version="1.0.0"
)


@app.post("/store-intents", summary="Store default SQL intents")
def store_intents():
    count = store_sql_intents()
    return {
        "status": "success",
        "stored_points": count
    }


@app.post("/intents", summary="Add SQL intent data points")
def add_sql_intents(intents: List[SQLIntentPoint]):
    count = store_dynamic_intents(intents)
    return {
        "status": "success",
        "stored_points": count
    }


@app.post("/classify", summary="Classify a user query into SQL operation")
def classify(user_query: str):
    return classify_query(user_query)



