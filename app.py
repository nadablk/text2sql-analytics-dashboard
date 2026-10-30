"""Streamlit Text-to-SQL analytics dashboard."""

from __future__ import annotations

import os
import re
import sqlite3
from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st

SAMPLE_DATA = pd.DataFrame(
    [
        ["France", "Data Scientist", "Python", 62000, 180],
        ["France", "Software Engineer", "Java", 58000, 220],
        ["Germany", "Data Scientist", "Python", 72000, 240],
        ["Germany", "ML Engineer", "PyTorch", 76000, 150],
        ["Italy", "Data Analyst", "SQL", 42000, 190],
        ["Italy", "Software Engineer", "JavaScript", 45000, 210],
        ["Spain", "Data Analyst", "SQL", 39000, 175],
        ["Spain", "Software Engineer", "Python", 43000, 205],
        ["Netherlands", "ML Engineer", "PyTorch", 78000, 130],
        ["Netherlands", "Data Scientist", "Python", 75000, 160],
    ],
    columns=["country", "role", "technology", "average_salary_eur", "job_count"],
)


def create_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    SAMPLE_DATA.to_sql("developer_jobs", conn, index=False, if_exists="replace")
    return conn


def deterministic_text_to_sql(question: str) -> Optional[str]:
    """Translate common portfolio-demo questions without an external API."""
    q = question.lower().strip()

    if "highest average salary" in q or "highest salary" in q:
        return """
        SELECT country, ROUND(AVG(average_salary_eur), 0) AS average_salary_eur
        FROM developer_jobs
        GROUP BY country
        ORDER BY average_salary_eur DESC
        """

    if "average salary by country" in q or "average salary for each country" in q:
        return """
        SELECT country, ROUND(AVG(average_salary_eur), 0) AS average_salary_eur
        FROM developer_jobs
        GROUP BY country
        ORDER BY average_salary_eur DESC
        """

    if "technology" in q and ("most jobs" in q or "most job" in q):
        return """
        SELECT technology, SUM(job_count) AS total_jobs
        FROM developer_jobs
        GROUP BY technology
        ORDER BY total_jobs DESC
        """

    if "jobs by role" in q or ("job" in q and "role" in q):
        return """
        SELECT role, SUM(job_count) AS total_jobs
        FROM developer_jobs
        GROUP BY role
        ORDER BY total_jobs DESC
        """

    if "total number of jobs" in q or "total jobs" in q:
        return "SELECT SUM(job_count) AS total_jobs FROM developer_jobs"

    if "average salary" in q:
        return "SELECT ROUND(AVG(average_salary_eur), 0) AS average_salary_eur FROM developer_jobs"

    return None


def llm_text_to_sql(question: str) -> Optional[str]:
    """Generate SQL with OpenAI when OPENAI_API_KEY is configured."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    schema = """
    Table: developer_jobs
    Columns:
      country TEXT
      role TEXT
      technology TEXT
      average_salary_eur INTEGER
      job_count INTEGER
    """

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "You generate SQLite SELECT queries only. "
                    "Return only SQL, no markdown and no explanation. "
                    f"Use only this schema:\\n{schema}"
                ),
            },
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content.strip()


def validate_sql(sql: str) -> str:
    """Allow read-only SQL and reject obvious write/mutation statements."""
    cleaned = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE).strip()
    if not re.match(r"^(SELECT|WITH)\b", cleaned, flags=re.IGNORECASE):
        raise ValueError("Only SELECT or WITH queries are allowed.")

    forbidden = r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|ATTACH|DETACH|REPLACE|PRAGMA|VACUUM)\b"
    if re.search(forbidden, cleaned, flags=re.IGNORECASE):
        raise ValueError("The generated SQL contains a forbidden operation.")

    if ";" in cleaned.rstrip(";"):
        raise ValueError("Only one SQL statement is allowed.")

    return cleaned.rstrip(";") + ";"


def choose_chart(df: pd.DataFrame):
    numeric = df.select_dtypes(include="number").columns.tolist()
    categorical = df.select_dtypes(exclude="number").columns.tolist()

    if not numeric or not categorical:
        return None

    x = categorical[0]
    y = numeric[0]
    if len(df) <= 15:
        return px.bar(df, x=x, y=y, title=f"{y.replace('_', ' ').title()} by {x.title()}")
    return px.scatter(df, x=x, y=y, title=f"{y.replace('_', ' ').title()} by {x.title()}")


st.set_page_config(page_title="Text-to-SQL Analytics", page_icon="📊", layout="wide")

st.title("📊 NLP Text-to-SQL Analytics Dashboard")
st.caption("Ask a business question in plain English and explore the generated SQL, table, and chart.")

conn = create_connection()

with st.sidebar:
    st.header("Sample questions")
    examples = [
        "Which country has the highest average salary?",
        "Show average salary by country.",
        "Which technology has the most jobs?",
        "Show jobs by role.",
        "What is the total number of jobs?",
    ]
    for example in examples:
        st.write(f"• {example}")

question = st.text_input(
    "Your question",
    value="Which country has the highest average salary?",
)

if st.button("Analyze", type="primary"):
    with st.spinner("Generating SQL..."):
        sql = llm_text_to_sql(question) or deterministic_text_to_sql(question)

    if not sql:
        st.error(
            "I couldn't map that question to the demo schema. "
            "Try one of the sample questions, or configure OPENAI_API_KEY."
        )
        st.stop()

    try:
        sql = validate_sql(sql)
        result = pd.read_sql_query(sql, conn)
    except Exception as exc:
        st.error(f"Query failed: {exc}")
        st.stop()

    st.subheader("Generated SQL")
    st.code(sql, language="sql")

    st.subheader("Results")
    st.dataframe(result, use_container_width=True)

    fig = choose_chart(result)
    if fig is not None:
        st.subheader("Visualization")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No suitable categorical + numeric column pair was found for an automatic chart.")

st.divider()
st.subheader("Dataset preview")
st.dataframe(SAMPLE_DATA, use_container_width=True)
