import streamlit as st
import random
import time
import yaml
from PIL import Image

CONFIG_PATH = "config.yaml"

class Persona:
    def __init__(self, name, avatar_path, avatar):
        self.name = name
        self.avatar_path = avatar_path
        self.avatar = avatar

@st.cache_data
def load_config(file_path=CONFIG_PATH):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config

@st.cache_data
def load_personas(config):
    personas = {} 
    for name, data in config["personas"].items(): 
        personas[name] = Persona(name=name, avatar_path=data["avatar"], avatar=Image.open(data["avatar"]))
    return personas

def clear_chat_history(key="messages"):
    del st.session_state[key]

if __name__ == '__main__': 

    config = load_config()

    print(config)
    print(config["personas"])

    personas = load_personas(config)

    print(f"""
----------------------------
{personas["ChatGPT"].name}
{personas["ChatGPT"].avatar_path}
{personas["ChatGPT"].avatar}
""")