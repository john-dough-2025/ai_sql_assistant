# ❄️ SnowGPT – Your AI-Powered SQL Assistant for Snowflake

SnowGPT is a **Streamlit** web‑app that lets anyone ask natural‑language questions about their Snowflake data and get back:

1. A parameterized **SQL query** (ready to run in Snowflake)  
2. An optional **preview table** (first 5 rows)  
3. A minimal **Streamlit chart snippet** (line, bar, area, scatter)  
4. A friendly, persona‑driven explanation of the results

Behind the scenes SnowGPT wires together:

| Layer | Tech |
|-------|------|
| UI / state | **Streamlit** |
| LLM orchestration | `agents` SDK (`Agent`, `Runner`, `RunConfig`) |
| LLM provider | **OpenAI** (GPT‑4o/4‑mini/o3‑mini—pick in sidebar) |
| SQL execution | **Snowflake Python Connector** |
| Caching & images | Streamlit `@st.cache_data`, PIL |

---

## ✨ Features

* **Natural‑language ↔︎ SQL** Type “Which market segments generate the most revenue?” and get a full Snowflake query.  
* **Configurable personas** Switch the assistant’s tone with YAML‑defined avatars & prompts.  
* **Dataset selector** Point to any Snowflake database/schema listed in `config.yaml`.  
* **Automatic data dictionary** Query Snowflake `INFORMATION_SCHEMA.COLUMNS` and show as Markdown.  
* **Sample preview** Appends `LIMIT 5` so you can inspect the result before running at scale.  
* **Chart autogeneration** LLM chooses the best chart type and returns a ready‑to‑run Streamlit call.  
* **Validation agent** Optional agent to sanity‑check SQL & chart code.  
* **Chat history + clear button** Keeps conversation context until you wipe it.  

---

## 🚀 Quick Start

1. **Clone & install**

   ```bash
   git clone https://github.com/<your-org>/snowgpt.git
   cd snowgpt
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scriptsctivate
   pip install -r requirements.txt
   ```

2. **Add secrets**

   Create `.streamlit/secrets.toml` (***never commit this!***)

   ```toml
   APP_PW = "super-secret-app-password"

   OPENAI_API_KEY   = "sk-..."

   SNOWFLAKE_USER      = "JULIEN"
   SNOWFLAKE_PASSWORD  = "••••••"
   SNOWFLAKE_ACCOUNT   = "abc-xy12345"
   SNOWFLAKE_WAREHOUSE = "COMPUTE_WH"
   ```

3. **Configure personas & datasets**

   ```yaml
   # config.yaml
   personas:
     SnowGPT:
       prompt: "You are a helpful Snowflake assistant."
       avatar: "avatars/snowgpt.png"
     BroGPT:
       prompt: "Speak like a hype gym bro…"
       avatar: "avatars/brogpt.png"

   sf_datasets:
     SALES_DEMO:
       description: "TPC-H sales demo"
       database: "SALES_DB"
       schema: "PUBLIC"
     WEATHER:
       description: "NOAA daily weather"
       database: "WX_DB"
       schema: "RAW"
   ```

4. **Run**

   ```bash
   streamlit run sql_agent_app.py --server.port 8501
   ```

   Open `http://localhost:8501`, enter the **app password**, pick a dataset/model/persona, and start chatting!

---

## 🗺️ Project Structure

```
.
├── sql_agent_app.py      # Main Streamlit app
├── st_utils.py           # Streamlit helper functions
├── images/              # PNG icons for personas
├── config.yaml           # Personas & dataset metadata
├── requirements.txt
└── README.md
```

---

## 🔑 Environment Variables & Secrets

| Key | Description |
|-----|-------------|
| `APP_PW` | Password gate for the UI |
| `OPENAI_API_KEY` | Your OpenAI key (needed for GPT models) |
| `SNOWFLAKE_*` | Standard Snowflake connector credentials |

All stored in **`.streamlit/secrets.toml`** so Streamlit’s built‑in secrets manager can inject them at runtime.

---

## 🛠️ How It Works (High‑Level)

1. **User prompt → Manager Agent**  
   Adds schema context + chosen persona prompt.  
2. **Manager Agent → SQL Agent**  
   Generates uppercase Snowflake SQL (`<SCHEMA>.<TABLE>` notation).  
3. **Manager Agent → `query_snowflake` tool**  
   Executes query.  
4. **Manager Agent → Chart Agent**  
   Looks at CSV preview, returns `st.<type>_chart(df, x="...", y="...")`.  
5. **Manager Agent → (optional) Validator Agent**  
   Checks column names & chart code.  
6. **Manager Agent → UI**  
   Sends final payload, Streamlit renders message, SQL popover, dataframe, and chart.

---

## ⚠️ Limitations & Gotchas

* Chart code uses `exec()` — validate before trusting in production.  
* Decimal columns are cast to float before plotting (Altair quirk).  
* Only the first 5 rows are previewed; rerun SQL manually for full data.  
* Currently Snowflake‑only; PRs welcome for other back ends.

---

## 📜 License

MIT — see [`LICENSE`](LICENSE).

---

## 🙌 Acknowledgements

* [Streamlit](https://streamlit.io/) for the UI framework  
* [OpenAI](https://openai.com/) for GPT models  
* Snowflake community & TPC‑H sample data for testing 🎉
