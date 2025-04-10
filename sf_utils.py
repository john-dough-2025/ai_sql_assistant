import streamlit as st
import snowflake.connector
import pandas as pd


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
    cursor.execute("SELECT * FROM TPCH_SF10.CUSTOMER LIMIT 10")

