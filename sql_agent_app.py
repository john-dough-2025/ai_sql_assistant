import streamlit as st
from openai import OpenAI
from snowflake import connector
from sf_utils import *
from st_utils import *
from agents_utils import *

st.title(":snowflake: :blue[SnowGPT:] Your AI-Powered SQL Assistant")

st.markdown("#### A smart assistant that queries your Snowflake data using natural language")

password = st.text_input("Enter password to use SnowGPT", type="password")
if password != st.secrets["APP_PW"]:
    st.stop()

####################################################
####################### INIT #######################
####################################################

config = load_config()
personas = load_personas(config)

# --------------- SNOWFLAKE --------------- #
# Connect to Snowflake instance
conn = init_snowflake_connection()

cursor = conn.cursor()

with open("data_dictionary.csv") as f:
    data_dictionary = f.read()


# --------------- OPENAI --------------- #
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
# Set a default model


system_prompt = f"""You are a SQL expert specialized in Snowflake.
Your task is to write a SQL query that answers the user's question as clearly and efficiently as possible.

### Output instructions:
- Only output the SQL query — no explanations or commentary
- Do not format it as a code block (no backticks)
- Use the format <TABLE_SCHEMA>.<TABLE_NAME> when referencing tables

### Additional context:
The following data dictionary is provided in CSV format to help you understand the schema:
{data_dictionary}
"""

# --------------- CHAT HISTORY --------------- #
# Initialize the chat history
if "messages" not in st.session_state:
    st.session_state.messages = []


####################################################
#################### SIDE BAR  #####################
####################################################


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

    # with st.expander(":pencil: **Email credentials** 🤫"):
    #     email_login = st.text_input("Login:",value="")
    #     email_password = st.text_input("Password:",value="", type="password")
    


####################################################
#################### MAIN VIEW #####################
####################################################

# st.write(st.session_state.messages)

# Display chat message from history on app rerun 
# for message in st.session_state.messages:
#     # st.write(message)
#     if message["persona"] == "User":
#         with st.chat_message(message["role"],avatar=personas[message["persona"]].avatar):
#             st.markdown(message["content"])
#     if message["persona"] != "User":
#         with st.chat_message(message["role"],avatar=personas[message["persona"]].avatar):
#             st.dataframe(message["df"])
#             # with st.expander("Show SQL query", expanded=False):
#             with st.popover("Show SQL query",use_container_width=False):
#                 st.code(message["content"], language="sql")


# React to user input
if prompt := st.chat_input():
    # Display user message in chat container
    with st.chat_message("user",avatar=personas["User"].avatar):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role":"user","persona":"User","content":prompt})

    # Display assistant response in chat message container
    with st.chat_message("assistant",avatar=personas[selected_persona].avatar):
       
        with st.spinner("Running Snowflake query…"):
            result = asyncio.run(run_query(manager_agent, prompt))
        # st.subheader("Final output")
        # st.write(result.final_output)
        
        # response = st.write_stream([words for words in response.output_text])
        df = query_sf(conn, result.final_output.query)
        st.dataframe(df)
        
        # with st.expander("Show SQL query", expanded=False):
        with st.popover("Show SQL query",use_container_width=False):
            st.code(result.final_output.query, language="sql")
        with st.popover("Show chart",use_container_width=False):
            exec(result.final_output.chart_code)
    st.session_state.messages.append({"role": "assistant","persona":selected_persona, "content": result.final_output.query, "df": df})


# Clear the chat history
if st.session_state.messages:
    st.button("Clear chat history", on_click=clear_chat_history)