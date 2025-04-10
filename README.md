# SnowGPT: Your AI-Powered SQL Assistant for Snowflake

SnowGPT is a Streamlit-based AI assistant that lets you query your Snowflake data warehouse using plain English. Powered by OpenAI and Snowflake, it translates your natural language prompts into efficient SQL queries and executes them instantly.

---

## 🚀 Features

- 🔐 Password-protected access
- 🤖 Natural language to SQL conversion using OpenAI
- ❄️ Direct integration with Snowflake
- 📄 Data dictionary awareness for smarter queries
- 🧑‍💼 Persona-driven chat interface with avatars
- 📊 Query results displayed as interactive tables
- 💬 Chat history with SQL popovers
- 🧠 Built-in prompt suggestions for inspiration

---

## 🧰 Tech Stack

- **Python**
- **Streamlit** for the UI
- **OpenAI** (via `openai` Python SDK)
- **Snowflake Connector** for database access
- **PIL** for avatar image handling
- **YAML** for persona configuration

---

## 📁 Project Structure

```
.
├── app.py                # Main Streamlit app
├── config.yaml           # Persona configuration
├── data_dictionary.csv   # Data dictionary for schema context
├── sf_utils.py           # Snowflake utility functions
├── st_utils.py           # Streamlit helper functions
├── images/               # Avatar images
├── venv/                 # Python virtual environment
```

---

## 🔧 Setup & Run

1. **Clone the repo:**
```bash
git clone https://github.com/your-repo/snowgpt.git
cd snowgpt
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure your environment:**
- Set your OpenAI API key in `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "your-openai-key"
```
- Update your Snowflake credentials in `sf_utils.py`
- Add your table definitions in `data_dictionary.csv`

4. **Run the app:**
```bash
streamlit run app.py
```

---

## 🧠 How It Works

- Loads personas from `config.yaml`
- Reads a data dictionary (CSV) to inform the system prompt
- User submits a natural language question
- OpenAI converts it to a SQL query
- Snowflake connector executes the query
- Results are shown with the SQL in a popover

---

## ✅ Example Prompts

- "Who is my best customer?"
- "What is the average delivery delay?"
- "Which market segments generate the most revenue?"

---

## 📌 To Do / Ideas

- Add support for multiple personas or models
- Cache query results for performance
- Improve error handling and logging
- Enable editing and rerunning SQL before execution

---

## 📄 License
MIT License

---

Made with ❤️ by [Julien Chantrel]

