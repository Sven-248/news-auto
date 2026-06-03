import json
from pathlib import Path

import pandas as pd
import streamlit as st
import os
from dotenv import load_dotenv

ENV_FILE = ".env.test"
load_dotenv(ENV_FILE)

POLIT_DATA_PATH = Path(
    os.getenv("POLIT_DASHBOARD_DATA_PATH", "demo/analyzed_demo_polit.jsonl")
)

TECH_DATA_PATH = Path(
    os.getenv("TECH_DASHBOARD_DATA_PATH", "demo/analyzed_demo_tech.jsonl")
)

DATA_PATH = Path(os.getenv("DASHBOARD_DATA_PATH", "data/analyzed_news.jsonl"))

SHOW_POLIT_DASHBOARD = os.getenv("SHOW_POLIT_DASHBOARD", "false").lower() == "true"

st.set_page_config(
    page_title="NewsAuto Dashboard",
    page_icon="📰",
    layout="wide",
)


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
                    "section": item.get("section"),
                    "analysis_profile": item.get("analysis_profile")
                    or analysis.get("analysis_profile", "political"),
                    # Shared
                    "summary": analysis.get("summary"),
                    "confidence": analysis.get("confidence", 0.0),
                    "reasoning": analysis.get("reasoning"),
                    "topic": analysis.get("topic"),
                    # Political
                    "classification": analysis.get(
                        "political_classification", "unklar"
                    ),
                    "main_political_subject": analysis.get("main_political_subject"),
                    "article_framing_orientation": analysis.get(
                        "article_framing_orientation"
                    ),
                    # Tech
                    "article_type": analysis.get("article_type"),
                    "primary_topic": analysis.get("primary_topic")
                    or analysis.get("topic"),
                    "practicality": analysis.get("practicality"),
                    "technology_maturity": analysis.get("technology_maturity"),
                    "target_audience": analysis.get("target_audience", []),
                    "urgency": analysis.get("urgency"),
                    "action_required": analysis.get("action_required"),
                    "recommended_action": analysis.get("recommended_action"),
                    "opinion_level": analysis.get("opinion_level"),
                    "novelty": analysis.get("novelty"),
                    "key_technologies": analysis.get("key_technologies", []),
                }
            )

    return pd.DataFrame(rows)


def safe_text(value, fallback=""):
    if value is None:
        return fallback
    return str(value)


def render_tech_dashboard(df: pd.DataFrame) -> None:
    st.title("NewsAuto – Tech Dashboard")
    st.caption(
        "Analyse von Technologie- und IT-Artikeln nach Thema, Praxisnutzen, Dringlichkeit und Zielgruppe."
    )

    df = df.copy()

    df["source"] = df["source"].fillna("unknown")
    df["primary_topic"] = df["primary_topic"].fillna("other")
    df["article_type"] = df["article_type"].fillna("other")
    df["practicality"] = df["practicality"].fillna("none")
    df["urgency"] = df["urgency"].fillna("low")
    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce").fillna(0.0)

    st.sidebar.header("Tech Filter")

    sources = sorted(df["source"].unique())
    selected_sources = st.sidebar.multiselect(
        "Quellen",
        sources,
        default=sources,
        key="tech_sources",
    )
    topics = sorted(df["primary_topic"].dropna().unique())
    selected_topics = st.sidebar.multiselect(
        "Themen",
        topics,
        default=topics,
        key="tech_topics",
    )

    article_types = sorted(df["article_type"].dropna().unique())
    selected_article_types = st.sidebar.multiselect(
        "Artikeltyp",
        article_types,
        default=article_types,
        key="tech_article_types",
    )

    practicality_values = ["high", "medium", "low", "none"]
    available_practicality = [
        p for p in practicality_values if p in df["practicality"].unique()
    ]
    selected_practicality = st.sidebar.multiselect(
        "Praktische Anwendbarkeit",
        available_practicality,
        default=available_practicality,
        key="tech_practicality",
    )

    urgency_values = ["critical", "high", "medium", "low"]
    available_urgency = [u for u in urgency_values if u in df["urgency"].unique()]
    selected_urgency = st.sidebar.multiselect(
        "Dringlichkeit",
        available_urgency,
        default=available_urgency,
        key="tech_urgency",
    )

    action_filter = st.sidebar.radio(
        "Handlung erforderlich",
        ["alle", "ja", "nein"],
        index=0,
        key="tech_action_filter",
    )

    min_conf = st.sidebar.slider(
        "Minimale Confidence",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05,
        key="tech_min_confidence",
    )

    search = st.sidebar.text_input(
        "Suche",
        key="tech_search",
    )

    filtered = df.copy()

    ai_topics = ["ai_ml", "llm", "ai_tools", "ai_research", "ai_business"]

    ai_only = st.sidebar.checkbox("Nur AI/ML-Themen anzeigen")

    if ai_only:
        filtered = filtered[filtered["primary_topic"].isin(ai_topics)]

    if selected_sources:
        filtered = filtered[filtered["source"].isin(selected_sources)]

    if selected_topics:
        filtered = filtered[filtered["primary_topic"].isin(selected_topics)]

    if selected_article_types:
        filtered = filtered[filtered["article_type"].isin(selected_article_types)]

    if selected_practicality:
        filtered = filtered[filtered["practicality"].isin(selected_practicality)]

    if selected_urgency:
        filtered = filtered[filtered["urgency"].isin(selected_urgency)]

    if action_filter == "ja":
        filtered = filtered[filtered["action_required"] == True]
    elif action_filter == "nein":
        filtered = filtered[filtered["action_required"] == False]

    filtered = filtered[filtered["confidence"] >= min_conf]

    if search:
        q = search.lower()
        filtered = filtered[
            filtered.apply(
                lambda row: q in str(row.get("title", "")).lower()
                or q in str(row.get("summary", "")).lower()
                or q in str(row.get("reasoning", "")).lower()
                or q in str(row.get("primary_topic", "")).lower()
                or q in str(row.get("key_technologies", "")).lower(),
                axis=1,
            )
        ]

    total = len(filtered)
    action_required_count = int((filtered["action_required"] == True).sum())
    high_urgency_count = int(filtered["urgency"].isin(["high", "critical"]).sum())
    high_practicality_count = int((filtered["practicality"] == "high").sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Artikel", total)
    col2.metric("Action Required", action_required_count)
    col3.metric("High/Critical Urgency", high_urgency_count)
    col4.metric("High Practicality", high_practicality_count)

    st.divider()

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Themen")
        st.bar_chart(filtered["primary_topic"].value_counts())

    with chart_col2:
        st.subheader("Artikeltypen")
        st.bar_chart(filtered["article_type"].value_counts())

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        st.subheader("Praktische Anwendbarkeit")
        st.bar_chart(filtered["practicality"].value_counts())

    with chart_col4:
        st.subheader("Dringlichkeit")
        st.bar_chart(filtered["urgency"].value_counts())

    st.divider()

    max_items = st.sidebar.slider(
        "Max. Artikel anzeigen",
        min_value=10,
        max_value=300,
        value=50,
        step=10,
        key="tech_max_items",
    )

    sort_option = st.selectbox(
        "Sortierung",
        [
            "Neueste zuerst",
            "Höchste Dringlichkeit",
            "Höchste Confidence",
            "Praktische Anwendbarkeit",
        ],
    )

    display_df = filtered.copy()

    if sort_option == "Neueste zuerst":
        display_df["published_sort"] = pd.to_datetime(
            display_df["published_at"], errors="coerce"
        )
        display_df = display_df.sort_values("published_sort", ascending=False)

    elif sort_option == "Höchste Confidence":
        display_df = display_df.sort_values("confidence", ascending=False)

    elif sort_option == "Höchste Dringlichkeit":
        urgency_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        display_df["urgency_score"] = display_df["urgency"].map(urgency_order).fillna(0)
        display_df = display_df.sort_values("urgency_score", ascending=False)

    elif sort_option == "Praktische Anwendbarkeit":
        practicality_order = {"high": 4, "medium": 3, "low": 2, "none": 1}
        display_df["practicality_score"] = (
            display_df["practicality"].map(practicality_order).fillna(0)
        )
        display_df = display_df.sort_values("practicality_score", ascending=False)

    display_df = display_df.head(max_items)

    st.subheader("Tech-Artikel")

    for _, row in display_df.iterrows():
        title = str(row.get("title") or "Ohne Titel")
        source = str(row.get("source") or "unknown")
        published_at = str(row.get("published_at") or "")
        url = str(row.get("url") or "")

        summary = str(row.get("summary") or "Keine Zusammenfassung vorhanden.")
        reasoning = str(row.get("reasoning") or "Keine Begründung vorhanden.")

        article_type = str(row.get("article_type") or "other")
        primary_topic = str(row.get("primary_topic") or "other")
        practicality = str(row.get("practicality") or "none")
        urgency = str(row.get("urgency") or "low")
        confidence = float(row.get("confidence") or 0.0)
        action_required = row.get("action_required")
        recommended_action = row.get("recommended_action")

        key_technologies = row.get("key_technologies") or []
        target_audience = row.get("target_audience") or []

        with st.container(border=True):
            top_left, top_right = st.columns([4, 1])

            with top_left:
                st.subheader(title)
                st.caption(f"{source} · {published_at}")

            with top_right:
                st.metric("Confidence", f"{confidence:.2f}")

            badge_line = (
                f"**Type:** `{article_type}` · "
                f"**Topic:** `{primary_topic}` · "
                f"**Practicality:** `{practicality}` · "
                f"**Urgency:** `{urgency}`"
            )
            st.markdown(badge_line)

            if action_required is True:
                st.warning("Action required")
                if recommended_action:
                    st.write(f"Empfohlene Aktion: {recommended_action}")
            elif action_required is False:
                st.info("Keine direkte Handlung erforderlich")

            st.write(summary)

            if key_technologies:
                st.write(
                    "**Technologien / Produkte:** "
                    + ", ".join(map(str, key_technologies))
                )

            if target_audience:
                st.write("**Zielgruppen:** " + ", ".join(map(str, target_audience)))

            with st.expander("Begründung anzeigen"):
                st.write(reasoning)

            if url:
                st.link_button("Original öffnen", url)


def render_political_dashboard(df: pd.DataFrame) -> None:
    st.title("NewsAuto Dashboard")
    st.caption(
        "Lokale Analyse von Nachrichtenartikeln: Zusammenfassung, Thema und politische Einordnung."
    )

    df = df.copy()

    if df.empty:
        st.warning("Keine politischen Artikel gefunden.")
        st.stop()

    df["analysis_profile"] = (
        df["analysis_profile"].fillna("political").astype(str).str.lower().str.strip()
    )
    df["classification"] = (
        df["classification"].fillna("unklar").astype(str).str.lower().str.strip()
    )
    df["source"] = df["source"].fillna("unknown")
    df["topic"] = df["topic"].fillna("Unklar")
    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce").fillna(0.0)

    # Sidebar
    st.sidebar.header("Filter")

    sources = sorted(df["source"].unique())
    selected_sources = st.sidebar.multiselect(
        "Quellen",
        sources,
        default=sources,
        key="polit_sources",
    )

    classes = ["links", "mitte", "rechts", "unklar"]
    available_classes = [c for c in classes if c in df["classification"].unique()]
    selected_class = st.sidebar.radio(
        "Politische Einordnung",
        ["alle", "links", "mitte", "rechts", "unklar"],
        index=0,
        key="polit_class_filter",
    )

    topics = sorted(df["topic"].dropna().unique())
    selected_topics = st.sidebar.multiselect(
        "Themen",
        topics,
        default=topics,
        key="polit_topics",
    )

    min_conf = st.sidebar.slider(
        "Minimale Confidence",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05,
        key="polit_min_confidence",
    )

    search = st.sidebar.text_input(
        "Suche in Titel / Zusammenfassung / Begründung",
        key="polit_search",
    )

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
        key="polit_max_items",
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


st.sidebar.title("NewsAuto")

views = ["Tech"]

if SHOW_POLIT_DASHBOARD:
    views.append("Polit")


selected_view = st.sidebar.radio(
    "Dashboard",
    views,
    index=0,
    key="dashboard_view",
)

if selected_view == "Polit":
    polit_df = load_jsonl(str(POLIT_DATA_PATH))

    if polit_df.empty:
        st.warning(f"Keine Polit-Daten gefunden: {POLIT_DATA_PATH}")
        st.stop()

    render_political_dashboard(polit_df)

elif selected_view == "Tech":
    tech_df = load_jsonl(str(TECH_DATA_PATH))

    if tech_df.empty:
        st.warning(f"Keine Tech-Daten gefunden: {TECH_DATA_PATH}")
        st.stop()

    render_tech_dashboard(tech_df)
