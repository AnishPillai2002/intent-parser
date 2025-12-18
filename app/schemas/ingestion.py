from pydantic import BaseModel, Field
from typing import Optional


class IntentIngestionRequest(BaseModel):
    """
    Request schema for SQL intent ingestion.

    This model controls how the ingestion pipeline behaves.
    """

    force: bool = Field(
        default=False,
        description=(
            "Force re-ingestion of intents even if they already exist. "
            "Useful when intent definitions or embeddings have changed."
        )
    )

    dry_run: bool = Field(
        default=False,
        description=(
            "Validate the ingestion pipeline without storing any data. "
            "Used for testing, CI pipelines, or configuration verification."
        )
    )


class IntentIngestionResponse(BaseModel):
    """
    Response schema returned after SQL intent ingestion.
    """

    status: str = Field(
        description="Overall status of the ingestion process. "
                    "Possible values: success, error"
    )

    intents_ingested: int = Field(
        description="Number of SQL intents processed during ingestion."
    )

    vectors_stored: int = Field(
        description="Total number of vector embeddings stored in the vector database."
    )

    message: str = Field(
        description="Human-readable message describing the result."
    )

    # Optional future-proof fields
    dry_run: Optional[bool] = Field(
        default=None,
        description="Indicates whether the ingestion was executed in dry-run mode."
    )
