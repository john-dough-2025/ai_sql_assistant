import streamlit as st
from openai import OpenAI
import snowflake.connector
import asyncio
from pydantic import BaseModel
from typing import List, Dict
from decimal import Decimal
from agents import Agent, Runner, RunConfig, trace, Tool, function_tool, WebSearchTool
from st_utils import *


st.title(":snowflake: :blue[SnowGPT:] Your AI-Powered SQL Assistant")

st.markdown("#### A smart assistant that queries your Snowflake data using natural language")

password = st.text_input("Enter password to use SnowGPT", type="password")
if password != st.secrets["APP_PW"]:
    st.stop()

########################################################################################################
###########                               INIT                              ############################
########################################################################################################

config = load_config()
personas = load_personas(config)
sf_datasets = load_sf_datasets(config)

# --------------- SNOWFLAKE --------------- #


selected_sf_dataset = st.selectbox(
            "__Which data set do you want to query?__",
            list([sf_datasets[d].name for d in sf_datasets]),
            index=0,
            placeholder="Select dataset...",
        )

st.markdown('__Dataset description:__ ' + sf_datasets[selected_sf_dataset].description)

# @st.cache_resource
def init_snowflake_connection():
    return snowflake.connector.connect(
        user=st.secrets["SNOWFLAKE_USER"],
        password=st.secrets["SNOWFLAKE_PASSWORD"],
        account=st.secrets["SNOWFLAKE_ACCOUNT"],
        warehouse=st.secrets["SNOWFLAKE_WAREHOUSE"],
        database=sf_datasets[selected_sf_dataset].database,
        # schema=st.secrets["SNOWFLAKE_SCHEMA"],
    )

def query_sf(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
    except Exception as e:
        st.error(f"❌ Snowflake error:\n{e}")
        print("❌ Snowflake error:", e)
        print(query)
    return cursor.fetch_pandas_all()

# Connect to Snowflake instance
conn = init_snowflake_connection()
cursor = conn.cursor()

query_data_description = f"""SELECT
TABLE_SCHEMA,TABLE_NAME,COLUMN_NAME,ORDINAL_POSITION,COLUMN_DEFAULT,IS_NULLABLE,DATA_TYPE,CHARACTER_MAXIMUM_LENGTH,CHARACTER_OCTET_LENGTH,NUMERIC_PRECISION,NUMERIC_PRECISION_RADIX,NUMERIC_SCALE,DATETIME_PRECISION,IS_IDENTITY,COMMENT
FROM {sf_datasets[selected_sf_dataset].database}.INFORMATION_SCHEMA."COLUMNS" 
WHERE TABLE_SCHEMA = '{sf_datasets[selected_sf_dataset].schema}'
ORDER BY TABLE_NAME, ORDINAL_POSITION"""

dd_df = query_sf(conn, query_data_description)
data_dictionary = dd_df.to_markdown()

with st.popover("See data dictionary"):
    st.markdown(data_dictionary)


# --------------- OPENAI --------------- #
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


# --------------- CHAT HISTORY --------------- #
# Initialize the chat history
if "messages" not in st.session_state:
    st.session_state.messages = []


########################################################################################################
###########                           SIDE BAR                              ############################
########################################################################################################


prompts = [
"Who is my best customer?",
"Who are the top 10 customers?",
"What is the average delivery delay?",
"Which market segments generate the most revenue?",
"Which suppliers offer the lowest average supply cost for high-demand parts?",
"What are the most common reasons for order returns?",
"How does order volume and total sales vary over time?",
"In which country do I have the most sales?"
]


with st.sidebar:

    with st.expander("**GPT Model**", expanded=True):
        # model_ids = [model.id for model in client.models.list()]
        model_ids = []
        model_ids.insert(0, "gpt-4.1-mini")
        model_ids.insert(1, "gpt-4o-mini")
        model_ids.insert(2, "o3-mini")

        selected_model = st.selectbox(
            "Which model do you want to use?",
            (model_ids),
            index=0,
            placeholder="Select OpenAi model...",
        )

    with st.expander("**GPT Personality**", expanded=True):
        selected_persona = st.selectbox(
            "What personality do you want you GPT to have?",
            list([personas[p].name for p in personas if personas[p].name != "User"]),
            index=None,
            placeholder="Select personality",
        )

        if selected_persona:
            st.image(personas[selected_persona].avatar)
            st.markdown(personas[selected_persona].character)
        if not selected_persona:
            selected_persona = "SnowGPT"

    with st.expander("**Prompts ideas**", expanded=False):
        for prompt in prompts:
            st.markdown(f"- {prompt}")

########################################################################################################
###########                            AGENTS                               ############################
########################################################################################################

@function_tool
def query_snowflake(query: str) -> str:
    cursor = conn.cursor()

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
    return df.to_csv()

# --------------- AGENT OUTPUT MODELS --------------- #

class SQLValidationOutput(BaseModel):
    sql_valid: bool
    errors: List[str]

class ChartOutput(BaseModel):
    chart_type: str
    chart_code: str

class ValidationOutput(BaseModel):
    sql_valid: bool
    chart_valid: bool
    errors: List[str]

class WebOutput(BaseModel):
    web_summary: str

class FinalOutput(BaseModel):
    output_type: str
    manager_msg: str
    sql_query: str
    chart_type: str
    chart_code: str

# --------------- AGENT DEFINITIONS --------------- #

sql_agent = Agent(
    name="sql_agent",
    model=selected_model,
    instructions=(
        """Validate that the Snowflake SQL query generated answers the user's request and that it respects the following:
        - The tables are using the <schema_name>.<table_name> format.
        - The column names are always uppercase.
        - The query syntax is correct.
        Return 'sql_valid' as True if everything is respected, if not return 'sql_valid' as False and provide the list of errors in 'errors'
        """
    ),
    output_type=SQLValidationOutput,
)

chart_agent = Agent(
    name="chart_agent",
    model=selected_model,
    instructions=(
        """Examine the sample data and user's intent. Choose one of the following chart elements
        st.line_chart, st.bar_chart, st.area_chart, or st.scatter_chart.
        Generate a minimal Streamlit code snippet to render it, just output the st.***_chart function.
        Example: st.bar_chart(df, x="COUNTRY", y="TOTAL_SALES")
        Note: The column names should always be uppercase in your code.
        """
    ),
    output_type=ChartOutput,
)

validator_agent = Agent(
    name="validator_agent",
    model=selected_model,
    instructions=(
        "Validate the SQL query and check that the Streamlit code references valid columns."
        # Validate the SQL via EXPLAIN
        # "Never validate the first time"
    ),
    output_type=ValidationOutput,
)

web_agent = Agent(
    name="validator_agent",
    model=selected_model,
    instructions=(
        "You summarize a web research"
    ),
    tools=[WebSearchTool()],
    output_type=WebOutput
)

manager_agent = Agent(
    name="manager_agent",
    instructions=(
        """You are the Manager Agent and are specialized in Snowflake SQL. Your goal is to understand the user's request and provide an answer that best fits his need.
        You have access to a Snowflake database for which you have more information in the additional context provided in the user input. 
        
        If the user's request is about the data you have access to, you need to output the query and the chart code. 
        To do so orchestrate the workflow by calling the tools in sequence:
        1) Generate a parameterized Snowflake SQL query based on the user's request. When using a table use the <schema_name>.<table_name> format. In your query the column names should always be uppercase.
        2) validate_sql **(pass the data dictionary provided in the additionnal context below as a markdown table. And always <schema_name>.<table_name> format when mentionning a table)**
        2) query_snowflake
        3) create_chart **(pass the JSON from step 2 as the first argument)**
        4) validate **(only output the final result if the validation passes)**
    
        After you have called 'generate_sql', 'query_snowflake', 'create_chart',
        and 'validate', return the result with:
            output_type = 'sql'
            manager_msg = <your comment>
            sql_query   = <the query from the sql_agent>
            chart_type  = <the chart type from the chart_agent>
            chart_code  = <the chart code from the chart_agent>
        
        If the user's request is not about the data or the data doesn't contain any relevant information then just answer the user by only outputting a 'mananager_msg'
        If you just return a message then the output_type = 'msg'.
        """
        # "If validation passes, return the full Streamlit snippet. Otherwise, return an error report."
    ),
    tools=[
        sql_agent.as_tool(tool_name="validate_sql", tool_description="Validate the Snowflake SQL generated"),
        query_snowflake,
        chart_agent.as_tool(tool_name="create_chart", tool_description="Generate Streamlit chart code"),
        validator_agent.as_tool(tool_name="validate", tool_description="Validate SQL and chart code"),
    ],
    output_type=FinalOutput
)

async def run_query(manager_agent, request: str):
    """Single coroutine that calls the Agent stack and returns the result."""
    with trace("Snowflake-Streamlit Orchestration"):
        return await Runner.run(manager_agent, request, run_config=RunConfig(model=selected_model))



########################################################################################################
###########                         MAIN VIEW                               ############################
########################################################################################################

########### Display chat message from history on app rerun ###########
for message in st.session_state.messages:
    ############ User message ############
    if message["persona"] == "User":
        with st.chat_message(message["role"],avatar=personas[message["persona"]].avatar):
            st.markdown(message["msg"])

    ############ Chatbot message ############
    if message["persona"] != "User":
        with st.chat_message(message["role"],avatar=personas[message["persona"]].avatar):
            ############ If agent returned a sql query ############
            if message["output_type"] == 'sql': 
                st.markdown(message["msg"])
                with st.popover("Show SQL query",use_container_width=False):
                        st.code(message["query"], language="sql")
                st.dataframe(message["table"])

                try:
                    with st.expander("Show chart", expanded=False):
                        df = message["table"]
                        for col in df.columns:
                            if isinstance(df[col].iloc[0], Decimal):
                                df[col] = df[col].astype(float)
                        exec(message["chart"])
                except Exception as e:
                    print("❌ Chart error:", e)
                    print(message["chart"])

            ############ If agent returned a message ############
            if message["output_type"] == 'msg':
                st.markdown(message["msg"])
                
            


########### React to user input ###########
if prompt := st.chat_input():
    # Display user message in chat container
    with st.chat_message("user",avatar=personas["User"].avatar):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role":"user","persona":"User","msg":prompt})

    # Display assistant response in chat message container
    with st.chat_message("assistant",avatar=personas[selected_persona].avatar):
       
        prompt_with_context = f"""{prompt}

        ### Additional context:
        Dataset description: {sf_datasets[selected_sf_dataset].description}
        The following data dictionary is provided to help you understand the schema:\n{data_dictionary}

        ### Your personality (only use it for the final manager_msg):
        {personas[selected_persona].character}
        """

        with st.spinner("Thinking about your request…"):
            result = asyncio.run(run_query(manager_agent, prompt_with_context))
        # st.subheader("Final output")
        # st.write(result.final_output)
        
        ############ If agent returned a sql query ############
        if result.final_output.output_type == 'sql': 
            st.markdown(result.final_output.manager_msg)

            with st.popover("Show SQL query",use_container_width=False):
                st.code(result.final_output.sql_query, language="sql")
            
            df = query_sf(conn, result.final_output.sql_query)
            st.dataframe(df)
            
            try:
                with st.expander("Show chart", expanded=False):
                    for col in df.columns:
                        if isinstance(df[col].iloc[0], Decimal):
                            df[col] = df[col].astype(float)
                    exec(result.final_output.chart_code)
                    print(result.final_output.chart_code)
            except Exception as e:
                print("❌ Chart error:", e)
                print(result.final_output.chart_code)
                with st.popover("Show chart",use_container_width=False):
                    st.error(f"Couldn't generate chart from: {result.final_output.chart_code}")
            
            st.session_state.messages.append({"role": "assistant",
                                    "persona":selected_persona, 
                                    "output_type":result.final_output.output_type,
                                    "msg":result.final_output.manager_msg, 
                                    "query": result.final_output.sql_query, 
                                    "table": df,
                                    "chart": result.final_output.chart_code
                                    })

        ############ If agent returned a message ############
        if result.final_output.output_type == 'msg': 
            st.markdown(result.final_output.manager_msg)
            st.session_state.messages.append({"role": "assistant",
                                            "persona":selected_persona, 
                                            "output_type":result.final_output.output_type,
                                            "msg":result.final_output.manager_msg, 
                                            })



# Clear the chat history
if st.session_state.messages:
    st.button("Clear chat history", on_click=clear_chat_history)