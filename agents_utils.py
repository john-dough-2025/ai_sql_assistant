from dotenv import load_dotenv
load_dotenv()

from sf_utils import *
import asyncio
import snowflake.connector
import streamlit as st
from pydantic import BaseModel
from typing import List, Dict

from agents import Agent, Runner, trace, Tool, function_tool

# --------------- SNOWFLAKE CONNECTION HELPERS --------------- #

def init_snowflake_connection():
    return snowflake.connector.connect(
        user=st.secrets["SNOWFLAKE_USER"],
        password=st.secrets["SNOWFLAKE_PASSWORD"],
        account=st.secrets["SNOWFLAKE_ACCOUNT"],
        warehouse=st.secrets["SNOWFLAKE_WAREHOUSE"],
        database=st.secrets["SNOWFLAKE_DATABASE"],
        # schema=st.secrets["SNOWFLAKE_SCHEMA"],
    )

connection = init_snowflake_connection()

@function_tool
def query_snowflake(query: str) -> str:
    cursor = connection.cursor()

    query = f"SELECT * FROM ({query.replace(';','')}) LIMIT 5"

    try:
        cursor.execute(query)
        # print(query)
    except Exception as e:
        st.error(f"❌ Snowflake error:\n{e}")
        print("❌ Snowflake error:", e)
        print(query)
        return []
    df = cursor.fetch_pandas_all()
    return df.to_json(orient="records")  # Return as JSON string (serializable)


# Loads data dictionnary for context
with open("data_dictionary.csv") as f:
    data_dictionary = f.read()

# --------------- AGENT OUTPUT MODELS --------------- #

class SQLOutput(BaseModel):
    sql: str

class DataOutput(BaseModel):
    data: List[Dict]

class ChartOutput(BaseModel):
    chart_type: str
    chart_code: str

class ValidationOutput(BaseModel):
    sql_valid: bool
    chart_valid: bool
    errors: List[str]

class FinalOutput(BaseModel):
    query: str
    chart_type: str
    chart_code: str

# --------------- AGENT DEFINITIONS --------------- #

# 1. SQL Generation Agent
sql_agent = Agent(
    name="sql_agent",
    instructions=(
        f"""Generate a parameterized Snowflake SQL query based on the user's request.
        ### Additional context:
        The following data dictionary is provided in CSV format to help you understand the schema:
        {data_dictionary}"""
    ),
    output_type=SQLOutput,
)

# 2. Chart Selection Agent
chart_agent = Agent(
    name="chart_agent",
    instructions=(
        "Examine the JSON data and user's intent. Choose one of the following chart elements"
        "st.line_chart, st.bar_chart, st.area_chart, or st.scatter_chart."
        "Generate a minimal Streamlit code snippet to render it."
        "Example: st.bar_chart(df['TOTAL_PURCHASE'])"
    ),
    output_type=ChartOutput,
)

# 3. Validation Agent
validator_agent = Agent(
    name="validator_agent",
    instructions=(
        "Validate the SQL via EXPLAIN and check that the Streamlit code references valid columns."
        # "Never validate the first time"
    ),
    output_type=ValidationOutput,
)

# 4. Manager Agent (Orchestrator)
manager_agent = Agent(
    name="manager_agent",
    instructions=(
        "You are the Manager Agent. Orchestrate the workflow by calling the tools in sequence:"
        "1) generate_sql → 2) query_snowflake →  3) create_chart **(pass the JSON from step 2 as the first argument)** → 4) validate"
        # "If validation passes, return the full Streamlit snippet. Otherwise, return an error report."
    ),
    tools=[
        sql_agent.as_tool(tool_name="generate_sql", tool_description="Generate Snowflake SQL"),
        query_snowflake,
        chart_agent.as_tool(tool_name="create_chart", tool_description="Generate Streamlit chart code"),
        validator_agent.as_tool(tool_name="validate", tool_description="Validate SQL and chart code"),
    ],
    output_type=FinalOutput
)

# ── Async helper ────────────────────────────────────────────────────────────────
async def run_query(manager_agent, request: str):
    """Single coroutine that calls your Agent stack and returns the result."""
    with trace("Snowflake-Streamlit Orchestration"):
        return await Runner.run(manager_agent, request)

# ── UI / orchestration ─────────────────────────────────────────────────────────
# st.title("Snowflake-Streamlit LLM assistant")

# user_request = st.text_input("Describe your data request:")
# run_clicked  = st.button("Ask")

# # Allocate a place in the sidebar for progress / results
# placeholder = st.empty()

# # 1️⃣  Launch the coroutine exactly once
# if run_clicked and user_request:
#     with st.spinner("Running Snowflake query…"):
#         result = asyncio.run(run_query(manager_agent, user_request))
#     st.subheader("Final output")
#     st.write(result.final_output)

# # 2️⃣  Check task state on every rerun
# task = st.session_state.get("query_task")
# if task:
#     if task.done():
#         result = task.result()
#         placeholder.subheader("Final output")
#         placeholder.write(result.final_output)
#         del st.session_state["query_task"]    # cleanup
#     else:
#         placeholder.info("⏳ Working on it...")