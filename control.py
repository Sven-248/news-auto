import os
import subprocess
from pathlib import Path
import webbrowser
import subprocess
import time

import streamlit as st
from dotenv import load_dotenv

st.set_page_config(
    page_title="NewsAuto Control Panel",
    page_icon="⚙️",
    layout="centered",
)

PROJECT_ROOT = Path(__file__).parent

st.title("NewsAuto Control Panel")
st.caption("Private local control panel for scraping and analysis.")

st.warning(
    "This control panel is intended for local use only. "
    "Do not deploy it publicly because it can run local commands."
)

env_file = st.selectbox(
    "Environment",
    [".env", ".env.test"],
    index=1,
)

load_dotenv(PROJECT_ROOT / env_file, override=True)

st.write(f"Using environment: `{env_file}`")

news_input = os.getenv("NEWS_INPUT_PATH", "data/news_tech.jsonl")
analysis_output = os.getenv("NEWS_ANALYZED_OUTPUT_PATH", "data/analyzed_tech.jsonl")
tech_dashboard_path = os.getenv(
    "TECH_DASHBOARD_DATA_PATH", "demo/analyzed_demo_tech.jsonl"
)

st.subheader("Current paths")
st.code(
    f"NEWS_INPUT_PATH={news_input}\n"
    f"NEWS_ANALYZED_OUTPUT_PATH={analysis_output}\n"
    f"TECH_DASHBOARD_DATA_PATH={tech_dashboard_path}"
)


def run_command(command: list[str]) -> tuple[int, str, str]:
    env = os.environ.copy()
    env["ENV_FILE"] = env_file

    process = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        shell=False,
        env=env,
    )

    return process.returncode, process.stdout, process.stderr


st.subheader("Analysis settings")

analyze_limit = st.number_input(
    "Max. Artikel analysieren",
    min_value=1,
    max_value=500,
    value=int(os.getenv("ANALYZE_LIMIT", "40")),
    step=5,
)

analyze_random = st.checkbox(
    "Zufällige Artikel auswählen",
    value=os.getenv("ANALYZE_RANDOM", "true").strip().lower() == "true",
)

st.subheader("Pipeline")

if st.button("1. Scrape tech sources"):
    with st.spinner("Scraping tech sources..."):
        code, out, err = run_command(["scrapy", "crawl", "rss", "-a", "profile=tech"])

    if code == 0:
        st.success("Scraping finished.")
    else:
        st.error("Scraping failed.")

    with st.expander("Logs"):
        if out:
            st.code(out)
        if err:
            st.code(err)


if st.button("2. Analyze articles"):
    command = [
        "python",
        "news_ingest/analyze_news.py",
        "--limit",
        str(analyze_limit),
    ]

    if analyze_random:
        command.append("--random")

    with st.spinner("Analyzing articles with local LLM..."):
        code, out, err = run_command(command)

    if code == 0:
        st.success("Analysis finished.")
    else:
        st.error("Analysis failed.")

    with st.expander("Logs"):
        if out:
            st.code(out)
        if err:
            st.code(err)


st.subheader("Dashboard")

if st.button("Dashboard starten und öffnen"):

    env = os.environ.copy()
    env["ENV_FILE"] = env_file

    subprocess.Popen(
        [
            "streamlit",
            "run",
            "app.py",
            "--server.port",
            "8502",
            "--server.headless",
            "true",
        ],
        cwd=PROJECT_ROOT,
        shell=False,
        env=env,
    )

    st.success("Dashboard wurde gestartet.")


st.subheader("Files")

for file in [
    news_input,
    analysis_output,
    tech_dashboard_path,
]:
    path = PROJECT_ROOT / file

    if path.exists():
        st.write(f"✅ `{file}` – {path.stat().st_size / 1024:.1f} KB")
    else:
        st.write(f"❌ `{file}` not found")
