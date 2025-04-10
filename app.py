import streamlit as st
from openai import OpenAI
from snowflake import connector
from sf_utils import *
from st_utils import *

st.title(":snowflake: :blue[SnowGPT:] Your AI-Powered SQL Assistant")

st.markdown("#### A smart assistant that queries your Snowflake data using natural language")

password = st.text_input("Enter password to use SnowGPT", type="password")
if password != 'keyrus':
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
if "openai_model" not in st.session_state:
    # st.session_state["openai_model"] = "gpt-4o-mini"
    st.session_state["openai_model"] = "o3-mini-2025-01-31"

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
    with st.expander("**GPT Personaly**", expanded=True):
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
            selected_persona = "Snowflake"

    with st.expander("**Prompts ideas**", expanded=False):
        for prompt in prompts:
            st.markdown(f"- {prompt}")

    with st.expander(":pencil: **Email credentials** 🤫"):
        email_login = st.text_input("Login:",value="")
        email_password = st.text_input("Password:",value="", type="password")
    


####################################################
#################### MAIN VIEW #####################
####################################################

# st.write(st.session_state.messages)

# Display chat message from history on app rerun 
for message in st.session_state.messages:
    # st.write(message)
    if message["persona"] == "User":
        with st.chat_message(message["role"],avatar=personas[message["persona"]].avatar):
            st.markdown(message["content"])
    if message["persona"] != "User":
        with st.chat_message(message["role"],avatar=personas[message["persona"]].avatar):
            st.dataframe(message["df"])
            # with st.expander("Show SQL query", expanded=False):
            with st.popover("Show SQL query",use_container_width=False):
                st.code(message["content"], language="sql")

        
# React to user input
if prompt := st.chat_input():
    # Display user message in chat container
    with st.chat_message("user",avatar=personas["User"].avatar):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role":"user","persona":"User","content":prompt})

    # Display assistant response in chat message container
    with st.chat_message("assistant",avatar=personas[selected_persona].avatar):
        response = client.responses.create(
                model=st.session_state["openai_model"],
                instructions= system_prompt,
                input=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                stream=False,
                )
        # response = st.write_stream([words for words in response.output_text])
        df = query_sf(conn, response.output_text)
        st.dataframe(df)
        # with st.expander("Show SQL query", expanded=False):
        with st.popover("Show SQL query",use_container_width=False):
            st.code(response.output_text, language="sql")
    st.session_state.messages.append({"role": "assistant","persona":selected_persona, "content": response.output_text, "df": df})


# Clear the chat history
if st.session_state.messages:
    st.button("Clear chat history", on_click=clear_chat_history)