import json
import time
from pathlib import Path
import requests
import os
from dotenv import load_dotenv
import random
import argparse
from analysis_profiles import build_prompt
from db import (
    get_connection,
    init_db,
    get_unanalyzed_articles,
    save_analysis,
    save_analysis_error,
)

ENV_FILE = ".env.test"
load_dotenv(ENV_FILE)

INPUT_PATH = Path(os.getenv("NEWS_INPUT_PATH", "data/news.jsonl"))
OUTPUT_PATH = Path(os.getenv("NEWS_ANALYZED_OUTPUT_PATH", "data/analyzed_news.jsonl"))

LLM_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")

MIN_TEXT_LENGTH = int(os.getenv("MIN_TEXT_LENGTH", "200"))
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "300"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_NUM_PREDICT = int(os.getenv("LLM_NUM_PREDICT", "1200"))

ANALYZE_LIMIT = int(os.getenv("ANALYZE_LIMIT", "30"))
ANALYZE_RANDOM = os.getenv("ANALYZE_RANDOM", "true").lower() == "true"

NEWS_DB_PATH = Path(os.getenv("NEWS_DB_PATH", "data/newsauto.db"))
ANALYZE_FROM_DB = os.getenv("ANALYZE_FROM_DB", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
ANALYZE_PROFILE = os.getenv("ANALYZE_PROFILE", "tech")


def get_ollama_base_url() -> str:
    if "/api/generate" in LLM_URL:
        return LLM_URL.split("/api/generate")[0]
    return LLM_URL.rstrip("/")


def check_ollama() -> None:
    base_url = get_ollama_base_url()
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        response.raise_for_status()
    except Exception as e:
        raise SystemExit(
            f"Ollama is not reachable. Start it first: ollama serve\nError: {e}"
        )


def load_articles(path: Path):
    if path.suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            yield from data
        else:
            yield data


def load_analyzed_urls(path: Path) -> set[str]:
    urls: set[str] = set()

    if not path.exists():
        return urls

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            url = item.get("url") or item.get("canonical_url")

            if url:
                urls.add(url)

    return urls


def call_llm(prompt: str) -> dict:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": LLM_TEMPERATURE, "num_predict": LLM_NUM_PREDICT},
    }

    response = requests.post(LLM_URL, json=payload, timeout=LLM_TIMEOUT_SECONDS)
    response.raise_for_status()

    data = response.json()
    raw = data.get("response", "").strip()

    # if the model outputs Markdown fences
    if raw.startswith("```json"):
        raw = raw.replace("```json", "", 1).strip()
    if raw.startswith("```"):
        raw = raw.replace("```", "", 1).strip()
    if raw.endswith("```"):
        raw = raw[:-3].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "summary": None,
            "political_classification": "unklar",
            "confidence": 0.0,
            "reasoning": f"LLM returned non-JSON output: {raw[:1000]}",
            "topic": None,
        }


def analyze_from_db(args) -> None:
    conn = get_connection(NEWS_DB_PATH)
    init_db(conn)

    articles = get_unanalyzed_articles(
        conn=conn,
        source_profile=args.source_profile,
        analysis_profile=args.source_profile,
        limit=args.limit,
        random_order=args.random,
    )

    print(f"Loaded unanalyzed DB articles: {len(articles)}")

    if not articles:
        print("No new articles to analyze.")
        conn.close()
        return

    for i, article in enumerate(articles, start=1):
        title = article.get("title") or "Ohne Titel"
        article_id = article["id"]

        print(f"[{i}/{len(articles)}] analyzing: {title}", flush=True)

        text = article.get("full_text") or article.get("teaser") or ""

        if len(text.strip()) < MIN_TEXT_LENGTH:
            msg = "too little text"
            print(f"[{i}/{len(articles)}] skipped: {msg}", flush=True)
            save_analysis_error(
                conn=conn,
                article_id=article_id,
                analysis_profile=args.source_profile,
                error=msg,
            )
            continue

        try:
            profile, prompt = build_prompt(article)
            analysis = call_llm(prompt)

            save_analysis(
                conn=conn,
                article_id=article_id,
                analysis_profile=profile,
                analysis=analysis,
            )

        except Exception as e:
            print(f"[{i}/{len(articles)}] error: {e}", flush=True)

            save_analysis_error(
                conn=conn,
                article_id=article_id,
                analysis_profile=args.source_profile,
                error=str(e),
            )

    conn.close()
    print("DB analysis finished.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit", type=int, default=ANALYZE_LIMIT, help="Analyze only N articles"
    )
    parser.add_argument(
        "--random",
        action="store_true",
        default=ANALYZE_RANDOM,
        help="Select random articles",
    )
    parser.add_argument(
        "--output", type=str, default=str(OUTPUT_PATH), help="Output JSONL path"
    )
    parser.add_argument(
        "--profile",
        choices=["auto", "polit", "tech"],
        default="auto",
        help="Force an analysis profile or use automatic selection",
    )
    parser.add_argument(
        "--from-db",
        action="store_true",
        default=ANALYZE_FROM_DB,
        help="Read unanalyzed articles from SQLite instead of JSONL",
    )
    parser.add_argument(
        "--source-profile",
        type=str,
        default=ANALYZE_PROFILE,
        help="Article source profile to analyze, e.g. tech or polit",
    )

    args = parser.parse_args()

    check_ollama()

    if args.from_db:
        analyze_from_db(args)
        return

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(INPUT_PATH)
    articles = list(load_articles(INPUT_PATH))
    # print(f"Loaded articles: {len(articles)}")

    if args.random:
        random.shuffle(articles)

    if args.limit:
        articles = articles[: args.limit]
        print(f"Analyzing subset: {len(articles)} articles")

    print(f"Loaded articles: {len(articles)}")

    already_analyzed_urls = load_analyzed_urls(output_path)
    if already_analyzed_urls:
        before = len(articles)
        articles = [
            article
            for article in articles
            if (article.get("url") or article.get("canonical_url"))
            not in already_analyzed_urls
        ]
        skipped = before - len(articles)
        print(f"Skipped already analyzed articles: {skipped}")
        print(f"Remaining new articles: {len(articles)}")

    if not articles:
        print("No new articles to analyze.")
        return

    with OUTPUT_PATH.open("a", encoding="utf-8") as out:
        for i, article in enumerate(articles, start=1):
            text = (
                article.get("full_text")
                or article.get("teaser")
                or article.get("title")
                or ""
            )

            if len(text.strip()) < LLM_TIMEOUT_SECONDS:
                print(f"[{i}] skipped: too little text")
                continue

            print(f"[{i}/{len(articles)}] analyzing: {article.get('title')}")

            profile, prompt = build_prompt(article)

            try:
                analysis = call_llm(prompt)
            except Exception as e:
                analysis = {
                    "summary": None,
                    "political_classification": "unklar",
                    "confidence": 0.0,
                    "reasoning": f"Error: {e}",
                    "topic": None,
                }

            result = {
                "source": article.get("source"),
                "url": article.get("url"),
                "canonical_url": article.get("canonical_url"),
                "title": article.get("title"),
                "published_at": article.get("published_at"),
                "section": article.get("section"),
                "analysis_profile": profile,
                "analysis": analysis,
            }

            out.write(json.dumps(result, ensure_ascii=False) + "\n")
            out.flush()

            time.sleep(0.3)

    print(f"Done. Output written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
