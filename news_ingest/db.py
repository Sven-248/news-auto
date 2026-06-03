import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path(os.getenv("NEWS_DB_PATH", "data/newsauto.db"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path or DEFAULT_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            canonical_url TEXT,
            source TEXT,
            profile TEXT,
            section TEXT,
            language TEXT,
            title TEXT,
            teaser TEXT,
            full_text TEXT,
            published_at TEXT,
            fetched_at TEXT,
            created_at TEXT NOT NULL
        );
        """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS article_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            analysis_profile TEXT NOT NULL,

            summary TEXT,
            topic TEXT,
            confidence REAL,
            reasoning TEXT,

            main_political_subject TEXT,
            article_framing_orientation TEXT,
            political_classification TEXT,

            article_type TEXT,
            primary_topic TEXT,
            secondary_topics TEXT,
            practicality TEXT,
            technology_maturity TEXT,
            target_audience TEXT,
            urgency TEXT,
            action_required INTEGER,
            recommended_action TEXT,
            opinion_level TEXT,
            novelty TEXT,
            key_technologies TEXT,

            raw_json TEXT,
            status TEXT NOT NULL DEFAULT 'success',
            error TEXT,
            analyzed_at TEXT NOT NULL,

            FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE CASCADE,
            UNIQUE(article_id, analysis_profile)
        );
        """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_source
        ON articles(source);
        """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_profile
        ON articles(profile);
        """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_articles_published_at
        ON articles(published_at);
        """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_article_analyses_profile
        ON article_analyses(analysis_profile);
        """)

    conn.commit()


def normalize_article(article: dict[str, Any]) -> dict[str, Any]:
    url = article.get("url") or article.get("canonical_url")

    if not url:
        raise ValueError("Article has no url or canonical_url")

    return {
        "url": url,
        "canonical_url": article.get("canonical_url"),
        "source": article.get("source"),
        "profile": article.get("profile"),
        "section": article.get("section"),
        "language": article.get("language"),
        "title": article.get("title"),
        "teaser": article.get("teaser"),
        "full_text": article.get("full_text"),
        "published_at": article.get("published_at"),
        "fetched_at": article.get("fetched_at"),
        "created_at": utc_now(),
    }


def insert_article(
    conn: sqlite3.Connection,
    article: dict[str, Any],
) -> tuple[int | None, bool]:
    """
    Inserts an article if it does not already exist.

    Returns:
        (article_id, inserted)
    """
    normalized = normalize_article(article)

    cursor = conn.execute(
        """
        INSERT OR IGNORE INTO articles (
            url,
            canonical_url,
            source,
            profile,
            section,
            language,
            title,
            teaser,
            full_text,
            published_at,
            fetched_at,
            created_at
        )
        VALUES (
            :url,
            :canonical_url,
            :source,
            :profile,
            :section,
            :language,
            :title,
            :teaser,
            :full_text,
            :published_at,
            :fetched_at,
            :created_at
        );
        """,
        normalized,
    )

    inserted = cursor.rowcount == 1

    row = conn.execute(
        "SELECT id FROM articles WHERE url = ?;",
        (normalized["url"],),
    ).fetchone()

    conn.commit()

    return (row["id"] if row else None), inserted


def article_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def get_unanalyzed_articles(
    conn: sqlite3.Connection,
    source_profile: str | None = None,
    analysis_profile: str | None = None,
    limit: int | None = None,
    random_order: bool = False,
) -> list[dict[str, Any]]:
    """
    Returns articles that do not yet have a successful analysis for the given analysis profile.

    source_profile:
        article profile from sources.py, e.g. "tech" or "polit"

    analysis_profile:
        LLM analysis profile, e.g. "tech" or "political"
    """
    params: list[Any] = []

    where = []

    if source_profile:
        where.append("a.profile = ?")
        params.append(source_profile)

    if analysis_profile:
        join_condition = """
            an.article_id = a.id
            AND an.analysis_profile = ?
            AND an.status = 'success'
        """
        params.insert(0, analysis_profile)
    else:
        join_condition = """
            an.article_id = a.id
            AND an.status = 'success'
        """

    where.append("an.id IS NULL")

    where_sql = " AND ".join(where)

    order_sql = "ORDER BY RANDOM()" if random_order else "ORDER BY a.published_at DESC"

    limit_sql = ""
    if limit:
        limit_sql = "LIMIT ?"
        params.append(limit)

    query = f"""
        SELECT a.*
        FROM articles a
        LEFT JOIN article_analyses an
            ON {join_condition}
        WHERE {where_sql}
        {order_sql}
        {limit_sql};
    """

    rows = conn.execute(query, params).fetchall()
    return [article_row_to_dict(row) for row in rows]


def save_analysis(
    conn: sqlite3.Connection,
    article_id: int,
    analysis_profile: str,
    analysis: dict[str, Any],
) -> None:
    def json_or_none(value: Any) -> str | None:
        if value is None:
            return None
        return json.dumps(value, ensure_ascii=False)

    action_required = analysis.get("action_required")

    if isinstance(action_required, bool):
        action_required_value = int(action_required)
    elif action_required is None:
        action_required_value = None
    else:
        action_required_value = 1 if str(action_required).lower() == "true" else 0

    conn.execute(
        """
        INSERT INTO article_analyses (
            article_id,
            analysis_profile,

            summary,
            topic,
            confidence,
            reasoning,

            main_political_subject,
            article_framing_orientation,
            political_classification,

            article_type,
            primary_topic,
            secondary_topics,
            practicality,
            technology_maturity,
            target_audience,
            urgency,
            action_required,
            recommended_action,
            opinion_level,
            novelty,
            key_technologies,

            raw_json,
            status,
            error,
            analyzed_at
        )
        VALUES (
            :article_id,
            :analysis_profile,

            :summary,
            :topic,
            :confidence,
            :reasoning,

            :main_political_subject,
            :article_framing_orientation,
            :political_classification,

            :article_type,
            :primary_topic,
            :secondary_topics,
            :practicality,
            :technology_maturity,
            :target_audience,
            :urgency,
            :action_required,
            :recommended_action,
            :opinion_level,
            :novelty,
            :key_technologies,

            :raw_json,
            'success',
            NULL,
            :analyzed_at
        )
        ON CONFLICT(article_id, analysis_profile)
        DO UPDATE SET
            summary = excluded.summary,
            topic = excluded.topic,
            confidence = excluded.confidence,
            reasoning = excluded.reasoning,

            main_political_subject = excluded.main_political_subject,
            article_framing_orientation = excluded.article_framing_orientation,
            political_classification = excluded.political_classification,

            article_type = excluded.article_type,
            primary_topic = excluded.primary_topic,
            secondary_topics = excluded.secondary_topics,
            practicality = excluded.practicality,
            technology_maturity = excluded.technology_maturity,
            target_audience = excluded.target_audience,
            urgency = excluded.urgency,
            action_required = excluded.action_required,
            recommended_action = excluded.recommended_action,
            opinion_level = excluded.opinion_level,
            novelty = excluded.novelty,
            key_technologies = excluded.key_technologies,

            raw_json = excluded.raw_json,
            status = 'success',
            error = NULL,
            analyzed_at = excluded.analyzed_at;
        """,
        {
            "article_id": article_id,
            "analysis_profile": analysis_profile,
            "summary": analysis.get("summary"),
            "topic": analysis.get("topic") or analysis.get("primary_topic"),
            "confidence": analysis.get("confidence"),
            "reasoning": analysis.get("reasoning"),
            "main_political_subject": analysis.get("main_political_subject"),
            "article_framing_orientation": analysis.get("article_framing_orientation"),
            "political_classification": analysis.get("political_classification"),
            "article_type": analysis.get("article_type"),
            "primary_topic": analysis.get("primary_topic"),
            "secondary_topics": json_or_none(analysis.get("secondary_topics")),
            "practicality": analysis.get("practicality"),
            "technology_maturity": analysis.get("technology_maturity"),
            "target_audience": json_or_none(analysis.get("target_audience")),
            "urgency": analysis.get("urgency"),
            "action_required": action_required_value,
            "recommended_action": analysis.get("recommended_action"),
            "opinion_level": analysis.get("opinion_level"),
            "novelty": analysis.get("novelty"),
            "key_technologies": json_or_none(analysis.get("key_technologies")),
            "raw_json": json.dumps(analysis, ensure_ascii=False),
            "analyzed_at": utc_now(),
        },
    )

    conn.commit()


def save_analysis_error(
    conn: sqlite3.Connection,
    article_id: int,
    analysis_profile: str,
    error: str,
) -> None:
    conn.execute(
        """
        INSERT INTO article_analyses (
            article_id,
            analysis_profile,
            status,
            error,
            analyzed_at
        )
        VALUES (?, ?, 'failed', ?, ?)
        ON CONFLICT(article_id, analysis_profile)
        DO UPDATE SET
            status = 'failed',
            error = excluded.error,
            analyzed_at = excluded.analyzed_at;
        """,
        (article_id, analysis_profile, error, utc_now()),
    )

    conn.commit()


def get_stats(conn: sqlite3.Connection) -> dict[str, Any]:
    article_count = conn.execute("SELECT COUNT(*) AS c FROM articles;").fetchone()["c"]

    analyzed_count = conn.execute("""
        SELECT COUNT(*) AS c
        FROM article_analyses
        WHERE status = 'success';
        """).fetchone()["c"]

    failed_count = conn.execute("""
        SELECT COUNT(*) AS c
        FROM article_analyses
        WHERE status = 'failed';
        """).fetchone()["c"]

    by_profile = conn.execute("""
        SELECT profile, COUNT(*) AS count
        FROM articles
        GROUP BY profile
        ORDER BY count DESC;
        """).fetchall()

    return {
        "articles": article_count,
        "analyses_success": analyzed_count,
        "analyses_failed": failed_count,
        "articles_by_profile": {
            row["profile"] or "unknown": row["count"] for row in by_profile
        },
    }
