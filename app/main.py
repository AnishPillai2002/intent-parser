# FastAPI entry point\
from fastapi import FastAPI
from app.api.routes import router
from app.api.ingestion_routes import router as ingestion_router
from app.api.schema_ingestion_routes import router as schema_ingestion_router
from fastapi import FastAPI
from logging.config import dictConfig
from app.utils.logging_util import LogConfig

# Initialize config
log_cfg = LogConfig()
dictConfig(log_cfg.get_dict_config())


# Now the logger is ready to be used anywhere
app = FastAPI(title="SQL Intent Classification Service")

app.include_router(router)
app.include_router(ingestion_router)
app.include_router(schema_ingestion_router)