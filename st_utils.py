import streamlit as st
import yaml
from PIL import Image

CONFIG_PATH = "config.yaml"

class Persona:
    def __init__(self, name, character, avatar_path, avatar):
        self.name = name
        self.character = character
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
        personas[name] = Persona(
            name=name, 
            character=data.get("prompt", ""), 
            avatar_path=data.get("avatar", ""), 
            avatar=Image.open(data.get("avatar", "")))
    return personas

def clear_chat_history(key="messages"):
    del st.session_state[key]

if __name__ == '__main__': 

    config = load_config()

    print(config)
    print(config["personas"])

    personas = load_personas(config)

    personas_list = [personas[p].name for p in personas]
    st.write(personas_list)