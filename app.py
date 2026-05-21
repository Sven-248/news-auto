import json
from pathlib import Path

import pandas as pd
import streamlit as st
import os
from dotenv import load_dotenv

ENV_FILE = ".env.test"
load_dotenv(ENV_FILE)

DATA_PATH = Path(os.getenv("DASHBOARD_DATA_PATH", "data/analyzed_news.jsonl"))
print(DATA_PATH)


@st.cache_data
def load_jsonl(path: Path) -> pd.DataFrame:
    rows = []

    file_path = Path(path)

    if not file_path.exists():
        return pd.DataFrame()

    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            analysis = item.get("analysis") or {}

            rows.append(
                {
                    "source": item.get("source"),
                    "title": item.get("title"),
                    "url": item.get("url") or item.get("canonical_url"),
                    "published_at": item.get("published_at"),
                    "summary": analysis.get("summary"),
                    "classification": analysis.get(
                        "political_classification", "unklar"
                    ),
                    "confidence": analysis.get("confidence", 0.0),
                    "reasoning": analysis.get("reasoning"),
                    "topic": analysis.get("topic"),
                }
            )

    return pd.DataFrame(rows)


def safe_text(value, fallback=""):
    if value is None:
        return fallback
    return str(value)


st.set_page_config(
    page_title="NewsAuto Dashboard",
    page_icon="📰",
    layout="wide",
)

st.title("NewsAuto Dashboard")
st.caption(
    "Lokale Analyse von Nachrichtenartikeln: Zusammenfassung, Thema und politische Einordnung."
)

df = load_jsonl(str(DATA_PATH))

if df.empty:
    st.warning(
        "Keine analysierten Daten gefunden. Erwartet wird: data/analyzed_news.jsonl"
    )
    st.stop()

# Normalisierung
df["classification"] = (
    df["classification"].fillna("unklar").astype(str).str.lower().str.strip()
)
df["source"] = df["source"].fillna("unknown")
df["topic"] = df["topic"].fillna("Unklar")
df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce").fillna(0.0)

# Sidebar
st.sidebar.header("Filter")

sources = sorted(df["source"].unique())
selected_sources = st.sidebar.multiselect("Quellen", sources, default=sources)

classes = ["links", "mitte", "rechts", "unklar"]
available_classes = [c for c in classes if c in df["classification"].unique()]
selected_class = st.sidebar.radio(
    "Politische Einordnung",
    ["alle", "links", "mitte", "rechts", "unklar"],
    index=0,
)

topics = sorted(df["topic"].dropna().unique())
selected_topics = st.sidebar.multiselect("Themen", topics, default=topics)

min_conf = st.sidebar.slider(
    "Minimale Confidence",
    min_value=0.0,
    max_value=1.0,
    value=0.0,
    step=0.05,
)

search = st.sidebar.text_input("Suche in Titel / Zusammenfassung / Begründung")

filtered = df.copy()

filtered = filtered[filtered["source"].isin(selected_sources)]
if selected_class != "alle":
    filtered = filtered[filtered["classification"] == selected_class]
filtered = filtered[filtered["topic"].isin(selected_topics)]
filtered = filtered[filtered["confidence"] >= min_conf]

if search:
    q = search.lower()
    filtered = filtered[
        filtered.apply(
            lambda row: q in safe_text(row.get("title")).lower()
            or q in safe_text(row.get("summary")).lower()
            or q in safe_text(row.get("reasoning")).lower()
            or q in safe_text(row.get("topic")).lower(),
            axis=1,
        )
    ]

# KPIs
total = len(filtered)
left_count = int((filtered["classification"] == "links").sum())
center_count = int((filtered["classification"] == "mitte").sum())
right_count = int((filtered["classification"] == "rechts").sum())
unclear_count = int((filtered["classification"] == "unklar").sum())

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Artikel", total)
col2.metric("Links", left_count)
col3.metric("Mitte", center_count)
col4.metric("Rechts", right_count)
col5.metric("Unklar", unclear_count)

st.divider()

# Charts
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Einordnung")
    class_counts = (
        filtered["classification"]
        .value_counts()
        .reindex(["links", "mitte", "rechts", "unklar"])
        .fillna(0)
    )
    st.bar_chart(class_counts)

with chart_col2:
    st.subheader("Quellen")
    source_counts = filtered["source"].value_counts()
    st.bar_chart(source_counts)

st.divider()

# Sortierung
sort_option = st.selectbox(
    "Sortierung",
    [
        "Neueste zuerst",
        "Höchste Confidence",
        "Quelle",
        "Einordnung",
    ],
)

max_items = st.sidebar.slider(
    "Max. Artikel anzeigen",
    min_value=10,
    max_value=300,
    value=50,
    step=10,
)

display_df = filtered.copy()

display_df = display_df.head(max_items)

if sort_option == "Neueste zuerst":
    display_df["published_sort"] = pd.to_datetime(
        display_df["published_at"], errors="coerce"
    )
    display_df = display_df.sort_values("published_sort", ascending=False)
elif sort_option == "Höchste Confidence":
    display_df = display_df.sort_values("confidence", ascending=False)
elif sort_option == "Quelle":
    display_df = display_df.sort_values("source")
elif sort_option == "Einordnung":
    display_df = display_df.sort_values("classification")

# Cards
st.subheader("Artikel")

for _, row in display_df.iterrows():
    title = safe_text(row.get("title"), "Ohne Titel")
    source = safe_text(row.get("source"), "unknown")
    published_at = safe_text(row.get("published_at"), "")
    classification = safe_text(row.get("classification"), "unklar")
    confidence = float(row.get("confidence") or 0.0)
    topic = safe_text(row.get("topic"), "Unklar")
    summary = safe_text(row.get("summary"), "Keine Zusammenfassung vorhanden.")
    reasoning = safe_text(row.get("reasoning"), "Keine Begründung vorhanden.")
    url = safe_text(row.get("url"))

    with st.container(border=True):
        top_left, top_right = st.columns([4, 1])

        with top_left:
            st.subheader(title)
            st.caption(f"{source} · {published_at} · Thema: {topic}")

        with top_right:
            st.metric(classification.upper(), f"{confidence:.2f}")

        st.write(summary)

        with st.expander("Begründung anzeigen"):
            st.write(reasoning)

        if url:
            st.link_button("Original öffnen", url)
