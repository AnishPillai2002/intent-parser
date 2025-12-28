import psycopg2
from typing import Iterator, Dict, List
from app.config import settings
from app.utils.logging_util import logger

class SchemaExtractor:
    def __init__(self, db_url: str = None):
        self.conn_str = db_url if db_url else settings.DB_URL
        self.schema = settings.DB_SCHEMA
        # Focus sampling on strings/categories
        self.categorical_types = {'character varying', 'varchar', 'text', 'char'}
        self.sample_limit = 10
        # Skip sampling if a column is likely a Primary Key or Unique ID
        self.skip_keywords = {'id', 'uuid', 'guid', 'pk', 'fk', 'hash'}

    def _get_smart_samples(self, cursor, table_name: str, column_name: str) -> List[str]:
        """
        Tiered sampling: 
        1. pg_stats (Instant/No Load)
        2. TABLESAMPLE BERNOULLI (Medium/Large Tables)
        3. Standard SELECT DISTINCT (Small Tables Fallback)
        """
        if any(key in column_name.lower() for key in self.skip_keywords):
            return []

        try:
            # --- TIER 1: pg_stats (Internal Metadata) ---
            cursor.execute("""
                SELECT most_common_vals::text 
                FROM pg_stats 
                WHERE schemaname = %s AND tablename = %s AND attname = %s;
            """, (self.schema, table_name, column_name))
            
            stats = cursor.fetchone()
            if stats and stats[0]:
                raw_vals = stats[0].strip("{}").split(",")
                return [v.strip('"') for v in raw_vals[:self.sample_limit]]

            # --- TIER 2: Check Table Size ---
            # We fetch the estimated row count to decide if we should use sampling
            cursor.execute("""
                SELECT reltuples AS estimate 
                FROM pg_class c 
                JOIN pg_namespace n ON n.oid = c.relnamespace 
                WHERE n.nspname = %s AND c.relname = %s;
            """, (self.schema, table_name))
            row_count_estimate = cursor.fetchone()[0]

            # --- TIER 3: Adaptive Selection ---
            if row_count_estimate > 1000:
                # Use BERNOULLI (row-level sampling) for large tables. 
                # It's slower than SYSTEM but works on small/medium tables too.
                query = f"""
                    SELECT DISTINCT "{column_name}" 
                    FROM "{self.schema}"."{table_name}" TABLESAMPLE BERNOULLI (10)
                    WHERE "{column_name}" IS NOT NULL 
                    LIMIT %s;
                """
            else:
                # Standard scan for small tables (like your 10-row sample)
                query = f"""
                    SELECT DISTINCT "{column_name}" 
                    FROM "{self.schema}"."{table_name}"
                    WHERE "{column_name}" IS NOT NULL 
                    LIMIT %s;
                """

            cursor.execute(query, (self.sample_limit,))
            return [str(row[0]) for row in cursor.fetchall()]

        except Exception as e:
            logger.warning(f"Sampling failed for {table_name}.{column_name}: {e}")
            return []
        
    def extract_schema_generator(self) -> Iterator[Dict]:
        conn = None
        try:
            conn = psycopg2.connect(self.conn_str)
            cursor = conn.cursor()

            # Fetch tables and descriptions
            cursor.execute("""
                SELECT table_name, obj_description(quote_ident(table_name)::regclass)
                FROM information_schema.tables
                WHERE table_schema = %s AND table_type = 'BASE TABLE';
            """, (self.schema,))
            tables = cursor.fetchall()

            for table_name, table_comment in tables:
                cursor.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = %s AND table_schema = %s;
                """, (table_name, self.schema))
                raw_columns = cursor.fetchall()
                
                columns = []
                for col_name, data_type in raw_columns:
                    samples = []
                    if data_type in self.categorical_types:
                        # Use the smart sampling method
                        samples = self._get_smart_samples(cursor, table_name, col_name)
                    
                    columns.append({
                        "name": col_name,
                        "type": data_type,
                        "samples": samples
                    })

                # Fetch foreign keys (relationships)
                cursor.execute("""
                    SELECT kcu.column_name, ccu.table_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = %s AND tc.table_name = %s;
                """, (self.schema, table_name))
                
                yield {
                    "table_name": table_name,
                    "description": table_comment or "",
                    "columns": columns,
                    "foreign_keys": [{"col": row[0], "foreign_table": row[1]} for row in cursor.fetchall()]
                }

        finally:
            if conn: conn.close()