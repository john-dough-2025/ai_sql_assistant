import streamlit as st
import snowflake.connector
from snowflake import connector



# Establish the Snowflake connection


@st.cache_resource
def init_snowflake_connection():
    return snowflake.connector.connect(
        user=st.secrets["SNOWFLAKE_USER"],
        password=st.secrets["SNOWFLAKE_PASSWORD"],
        account=st.secrets["SNOWFLAKE_ACCOUNT"],
        warehouse=st.secrets["SNOWFLAKE_WAREHOUSE"],
        database=st.secrets["SNOWFLAKE_DATABASE"],
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

