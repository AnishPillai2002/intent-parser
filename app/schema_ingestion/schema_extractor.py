# app/schema_ingestion/schema_extractor.py
import psycopg2
from typing import Iterator, Dict
from app.config import settings
from app.utils.logging_util import logger

class SchemaExtractor:
    def __init__(self, db_url: str = None):
        self.conn_str = db_url if db_url else settings.DB_URL
        self.schema = settings.DB_SCHEMA

    # CHANGE: Return an Iterator (generator) instead of a List
    def extract_schema_generator(self) -> Iterator[Dict]:
        conn = None
        try:
            logger.debug("Connecting to database for streaming extraction...")
            conn = psycopg2.connect(self.conn_str)
            cursor = conn.cursor()

            # 1. Fetch Tables
            cursor.execute(
                """
                SELECT table_name, obj_description(quote_ident(table_name)::regclass)
                FROM information_schema.tables
                WHERE table_schema = %s AND table_type = 'BASE TABLE';
                """,
                (self.schema,),
            )
            # Fetch all table names first (low memory footprint)
            tables = cursor.fetchall()

            for table_name, table_comment in tables:
                # 2. Fetch Columns
                cursor.execute(
                    """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = %s AND table_schema = %s;
                    """,
                    (table_name, self.schema),
                )
                columns = [{"name": row[0], "type": row[1]} for row in cursor.fetchall()]

                # 3. Fetch Foreign Keys
                cursor.execute(
                    """
                    SELECT
                        kcu.column_name, ccu.table_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu
                      ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                      AND tc.table_schema = %s AND tc.table_name = %s;
                    """,
                    (self.schema, table_name),
                )
                foreign_keys = [
                    {"col": row[0], "foreign_table": row[1]} for row in cursor.fetchall()
                ]

                # YIELD the result one by one
                yield {
                    "table_name": table_name,
                    "description": table_comment or "", # PostgreSQL table comments are gold for RAG
                    "columns": columns,
                    "foreign_keys": foreign_keys,
                }

        except Exception as e:
            logger.error(f"Schema extraction failed: {e}", exc_info=True)
        finally:
            if conn:
                conn.close()