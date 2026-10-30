# Automated NLP Text-to-SQL Analytics Dashboard

A Streamlit analytics dashboard that converts plain-English business questions into executable SQL over an in-memory SQLite database, then visualizes the results with Plotly.

## Features

- Loads a small developer-jobs dataset into SQLite.
- Accepts natural-language analytics questions.
- Generates SQL using an LLM when an OpenAI API key is configured.
- Includes a deterministic fallback translator for common demo questions, so the project remains runnable without an API key.
- Executes only read-only `SELECT`/`WITH` queries.
- Displays the generated SQL and result table.
- Automatically chooses a Plotly chart based on the returned columns.
- Includes a notebook for exploratory Text-to-SQL analysis.

## Project structure

```text
text2sql-analytics-dashboard/
├── README.md
├── requirements.txt
├── app.py
└── notebooks/
    └── text2sql_analysis.ipynb
```

## Setup

Python 3.10+ is recommended.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install:

```bash
pip install -r requirements.txt
```

## Run the dashboard

```bash
streamlit run app.py
```

The dashboard starts with an in-memory sample dataset containing developer roles, countries, technologies, salaries, and job counts.

## Optional LLM mode

For LLM-powered Text-to-SQL, set an OpenAI API key in your environment:

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="your-key"
streamlit run app.py
```

Without a key, the application uses a deterministic translator for the example questions shown in the UI.

## Example questions

- Which country has the highest average salary?
- Show average salary by country.
- Which technology has the most jobs?
- Show jobs by role.
- What is the total number of jobs?

## Safety design

The application executes only `SELECT` and `WITH` statements. Mutating SQL such as `DROP`, `DELETE`, `UPDATE`, and `INSERT` is rejected.

For production systems, add authentication, query timeouts, database permissions, stronger SQL parsing, audit logging, and a sandboxed database.

## Notebook

Open:

```text
notebooks/text2sql_analysis.ipynb
```

## License

MIT
