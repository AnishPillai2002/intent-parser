import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # =========================================================================
    # 1. DATABASE SETTINGS (Postgres / Supabase)
    # =========================================================================
    # The connection string: postgresql://user:password@host:port/dbname
    DB_URL = os.getenv("DB_URL")
    
    # Optional: Default schema to look for tables (usually 'public')
    DB_SCHEMA = os.getenv("DB_SCHEMA", "public")

    # =========================================================================
    # 2. QDRANT SETTINGS (Vector Database)
    # =========================================================================
    # If using Qdrant Cloud, use URL + API KEY. 
    # If using local Docker, URL might be 'http://localhost:6333' and Key is None.
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
    
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "sql_intents")
    DB_COLLECTION_NAME = os.getenv("DB_COLLECTION_NAME", "db_schemas")
    VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", 384))

    # =========================================================================
    # 3. MODEL SETTINGS
    # =========================================================================
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    CUSTOM_LLM_URL = os.getenv("CUSTOM_LLM_URL", "")
    CUSTOM_LLM_KEY = os.getenv("CUSTOM_LLM_KEY", "")
# Instantiate simple singleton for easy import
settings = Settings()