import logging
from strands import Agent, tool
from agents import default_model
from tools.knowledge_base_tool import get_schema
from tools.sqllite_tool import run_sqlite_query

logger = logging.getLogger(__name__)

# --- Agent Definition ---
system_prompt = """
You are an NL2SQL agent that converts natural language questions into SQL queries.

Your task is to:
1. Understand the user's question
2. Generate a valid SQL query that answers the question
3. If provided with an error message, correct your SQL query
4. If you are unable to retrieve the schema fully, call get_schema with bool flag=True

When generating SQL:
- Use standard SQL syntax compatible with Amazon Athena
- Include appropriate table joins when needed
- Use column names exactly as they appear in the schema

Example response format:
Query: "SELECT customer_id, name FROM customers WHERE account_status = 'active'"
Results:
customer_id | name
1 | Jane Doe
2 | John Doe

If you receive an error, carefully analyze it and fix your query.
"""

# Create the actual Agent object
text2sql_agent = Agent(
    model=default_model,
    system_prompt=system_prompt,
    tools=[get_schema, run_sqlite_query]
)

tool_names = ["get_schema", "run_sqlite_query"]

# --- Tool Definition ---

@tool
def text2sql_agent_tool(query: str) -> str:
    """
    NL2SQL agent that converts natural language questions into SQL queries and executes them.
    
    Args:
        query: A natural language question about the database
        
    Returns:
        SQL query results and analysis
    """
    response = text2sql_agent(query)
    return str(response)