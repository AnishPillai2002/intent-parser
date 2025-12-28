from typing import Dict, Any, List
from app.utils.logging_util import logger

# Import your existing services
from app.services.db_schema.schema_retrieval import schema_retrieval_service as schema_service
from app.services.sql_intents.sql_intent_retrieval import intent_retrieval_service as intent_service
from app.services.llm.strategies.llm_generation_strategy import LLMGenerationStrategy, GeminiStrategy, CustomAPIStrategy

class SQLGenerationService:
    """
    Orchestrator class that:
    1. Fetches context (Schema + Intents)
    2. Builds the prompt
    3. Delegates generation to the selected LLM Strategy
    """

    def __init__(self):
        # Register available strategies
        self.strategies: Dict[str, LLMGenerationStrategy] = {
            "gemini": GeminiStrategy(),
            "custom": CustomAPIStrategy()
        }

    async def generate_query(self, user_query: str, provider: str = "gemini") -> Dict[str, Any]:
        """
        Main entry point. Returns both the SQL and the context used (for debugging).
        """
        logger.info(f"Generating SQL for query: '{user_query}' using provider: {provider}")

        if provider not in self.strategies:
            raise ValueError(f"Unknown provider '{provider}'. Available: {list(self.strategies.keys())}")
        
        strategy = self.strategies[provider]

        # 1. Gather Context
        #    (We call the internal service methods directly)
        schema_context = schema_service.retrieve_relevant_schema(user_query, top_k=15)
        intent_matches = intent_service.get_top_intents(user_query, limit=5)

        # 2. Build the System Prompt
        #    (Logic moved here so Strategy is just an executor)
        system_prompt = self._build_system_prompt(schema_context, intent_matches)

        # 3. Generate SQL
        #    (Matches the signature: strategy.generate_sql(system, user))
        sql_query = await strategy.generate_sql(system_prompt, user_query)
        
        return {
            "sql": sql_query,
            "context": {
                "schema_tables": [t.get('table_name') for t in schema_context.get('context', {}).get('tables', [])],
                "intents_found": len(intent_matches)
            }
        }

    def _build_system_prompt(
        self, 
        schema_context: Dict[str, Any], 
        intent_context: List[Dict[str, Any]]
    ) -> str:
        """
        Internal helper to format the system prompt.
        """
        
        # --- PART A: SCHEMA FORMATTING ---
        # The schema_context comes from _format_output_for_llm
        # Structure: {"tables": [{"table_name": "...", "columns": [...], ...}]}
        
        schema_text = "### DATABASE SCHEMA (PostgreSQL)\n"
        tables = schema_context.get("tables", [])

        if not tables:
            schema_text += "No relevant tables found in context.\n"
        else:
            for table in tables:
                t_name = table.get("table_name", "unknown")
                description = table.get("description", "")
                
                # Format columns as "name (type)"
                col_list = []
                for col in table.get("columns", []):
                    c_name = col.get("name")
                    c_type = col.get("type")
                    col_list.append(f"{c_name} ({c_type})")
                
                columns_str = ", ".join(col_list)
                
                # Format relationships if they exist
                rels_str = ""
                relationships = table.get("relationships", [])
                if relationships:
                    rel_parts = [f"{r['column']} -> {r['references_table']}" for r in relationships]
                    rels_str = f" | FKs: {', '.join(rel_parts)}"

                # Construct the line for this table
                # e.g. - Table `users`: (id (int), name (text)) | FKs: role_id -> roles
                schema_text += f"- Table `{t_name}`: ({columns_str}){rels_str}"
                if description:
                    schema_text += f" -- {description}"
                schema_text += "\n"

        # --- PART B: INTENT FORMATTING ---
        examples_text = "### SIMILAR PAST EXAMPLES (Reference Only)\n"
        
        if not intent_context:
            examples_text += "No reference examples available.\n"
        else:
            for idx, intent in enumerate(intent_context):
                # Unpack the payload wrapper from Qdrant response
                payload = intent.get("payload", {})
                
                example_q = payload.get("text", "Unknown query")
                operation = payload.get("operation", "SELECT")
                category = payload.get("category", "General")
                
                examples_text += (
                    f"{idx+1}. User: '{example_q}'\n"
                    f"   Intent: {category} ({operation})\n"
                )

        # --- PART C: FINAL ASSEMBLY ---
        prompt = f"""
You are an expert SQL Generator for a PostgreSQL database.
Your goal is to convert the user's natural language request into a valid, efficient SQL query.

{schema_text}

{examples_text}

### RULES:
1. **Scope:** Use ONLY the tables and columns defined in the schema above. Do not hallucinate table names.
2. **Dialect:** Generate standard PostgreSQL syntax.
3. **Format:** Return ONLY the raw SQL query. Do not include markdown formatting (like ```sql), comments, or explanations.
4. **Relationships:** Pay attention to the 'FKs' (Foreign Keys) listed in the schema to join tables correctly.
5. **Context:** Use the 'Similar Past Examples' to understand how to map vague terms to specific database columns.
"""
        return prompt
# Singleton instance
sql_generator = SQLGenerationService()