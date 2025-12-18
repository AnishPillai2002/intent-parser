"""
Service-layer wrapper for SQL intent ingestion.

This function is responsible for:
    - Handling dry-run mode
    - Calling the ingestion pipeline
    - Validating results
    - Returning a structured API-friendly response
"""

from app.intents.ingest import ingest_intents

def ingest_intents_service(dry_run: bool = False):
    # ---------------------------
    # Dry run mode
    # ---------------------------
    if dry_run:
        return {
            "intents": 0,
            "vectors": 0,
            "message": "Dry run successful. No data ingested."
        }
    
    # ---------------------------
    # Execute ingestion
    # ---------------------------
    try:
        stats = ingest_intents()
    except Exception as exc:
        return {
            "status": "error",
            "dry_run": False,
            "intents": 0,
            "vectors": 0,
            "message": f"Intent ingestion failed: {str(exc)}"
        }
    
    # ---------------------------
    # Validate ingestion result
    # ---------------------------
    if not stats:
        return {
            "status": "error",
            "dry_run": False,
            "intents": 0,
            "vectors": 0,
            "message": "Ingestion completed but returned no statistics"
        }
    # ---------------------------
    # Return Success response
    # ---------------------------
    return {
        "status": "success",
        "dry_run": False,
        "intents": stats["intents"],
        "vectors": stats["vectors"],
        "message": "SQL intents ingested successfully"
    }
