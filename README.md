# NewsAuto

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://sven-248-news-auto-app-featurepublic-demo-dashboard-fssa60.streamlit.app)

NewsAuto is a local-first news ingestion and analysis prototype.

It crawls German news and technology sources via RSS, stores articles as JSONL, analyzes each article with a local LLM through Ollama, and displays the results in a Streamlit dashboard.

The project is intended as a portfolio and experimentation project for Python-based data pipelines, local LLM workflows, news analysis, technology news classification, and lightweight dashboards.

---

## Online Demo

A public demo version of the dashboard is available here:

[Open NewsAuto Demo](https://sven-248-news-auto-app-featurepublic-demo-dashboard-fssa60.streamlit.app)
The online demo uses static demo data from:

- `demo/analyzed_demo_polit.jsonl`
- `demo/analyzed_demo_tech.jsonl`

It does not contain full article texts or live scraped data.  
The local version supports live crawling and local LLM analysis via Ollama.

## Features

- RSS-based news crawling with Scrapy
- Profile-based source crawling:
  - `polit` for general German news and political reporting
  - `tech` for technology, IT, security and AI-related sources
- Multiple German news and technology sources
- JSONL-based local data pipeline
- Local LLM analysis through Ollama
- Separate analysis profiles:
  - political framing analysis for general news
  - tech applicability analysis for technology and AI articles
- Article summaries
- Topic extraction
- Article-level political framing classification:
  - `links`
  - `mitte`
  - `rechts`
  - `unklar`
- Tech article classification by:
  - article type
  - primary topic
  - secondary topics
  - practicality
  - urgency
  - target audience
  - key technologies
  - action required
- Confidence score and model reasoning
- Profile-aware Streamlit dashboard
- Fully local processing
- No external LLM API required

---

## Architecture

```text
RSS Feeds
   ↓
Scrapy Crawler
   ↓
Profile-based JSONL files
   ↓
Ollama / Local LLM
   ↓
Analyzed JSONL files
   ↓
Streamlit Dashboard
```

NewsAuto supports source profiles.

```text
polit sources → political framing analysis
tech sources  → tech applicability analysis
```

---

## Project Structure

```text
NewsAuto/
├─ news_ingest/
│  ├─ analysis_profiles/
│  │  ├─ __init__.py
│  │  ├─ political.py
│  │  └─ tech.py
│  ├─ spiders/
│  │  └─ rss_spider.py
│  ├─ sources.py
│  ├─ items.py
│  ├─ pipelines.py
│  ├─ settings.py
│  └─ analyze_news.py
├─ data/
│  ├─ news_polit.jsonl
│  ├─ news_tech.jsonl
│  ├─ analyzed_polit.jsonl
│  └─ analyzed_tech.jsonl
├─ app.py
├─ requirements.txt
├─ scrapy.cfg
├─ .env.example
├─ .gitignore
└─ README.md
```

The `data/` directory is generated locally and should not be committed.

---

## Requirements

- Python 3.11+
- Ollama
- A local Ollama model, for example:
  - `qwen3:4b`
  - `qwen2.5:7b`
  - `llama3.2:3b`

Python dependencies are listed in `requirements.txt`.

Recommended default model:

```text
qwen3:4b
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/NewsAuto.git
cd NewsAuto
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Linux / macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration

The project uses environment variables for local configuration.

Copy the example file:

Windows PowerShell:

```powershell
copy .env.example .env
```

Linux / macOS:

```bash
cp .env.example .env
```

Example `.env`:

```env
# Ollama / Local LLM
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen3:4b

# Input / Output files
NEWS_INPUT_PATH=data/news_polit.jsonl
NEWS_ANALYZED_OUTPUT_PATH=data/analyzed_polit.jsonl

# Analysis settings
MIN_TEXT_LENGTH=200
LLM_TIMEOUT_SECONDS=300
LLM_TEMPERATURE=0.2
LLM_NUM_PREDICT=1200

# Streamlit dashboard
DASHBOARD_DATA_PATH=data/analyzed_polit.jsonl
```

The `.env` file is local only and should not be committed.

You can also use separate local environment files, for example:

```text
.env
.env.test
```

These files should stay local and are ignored by Git.

---

## Source Profiles

NewsAuto supports profile-based crawling.

Current profiles:

| Profile | Purpose                                      |
| ------- | -------------------------------------------- |
| `polit` | General German news and political reporting  |
| `tech`  | Technology, IT, security and AI-related news |

Examples of `polit` sources:

- Tagesschau
- ZEIT
- SPIEGEL
- taz
- Deutschlandfunk
- ZDFheute
- n-tv

Examples of `tech` sources:

- Heise
- Golem
- t3n
- The Decoder
- All-AI

Sources are configured in:

```text
news_ingest/sources.py
```

Each source defines a profile:

```python
"heise": {
    "language": "de",
    "profile": "tech",
    "rss": [
        "https://www.heise.de/rss/heise-atom.xml",
    ],
}
```

---

## Running Ollama

Install Ollama from:

```text
https://ollama.com
```

Pull a model:

```bash
ollama pull qwen3:4b
```

Start Ollama:

```bash
ollama serve
```

Check if Ollama is running:

```bash
curl http://localhost:11434/api/tags
```

If Ollama is running correctly, this returns a JSON response with the available local models.

---

## Crawl Articles

Run the Scrapy crawler:

```bash
scrapy crawl rss
```

This crawls all configured sources and writes:

```text
data/news_all.jsonl
```

You can crawl a single source:

```bash
scrapy crawl rss -a source=tagesschau
```

Example output:

```text
data/news_polit_tagesschau.jsonl
```

You can also crawl only one profile.

Crawl all political/news sources:

```bash
scrapy crawl rss -a profile=polit
```

Example output:

```text
data/news_polit.jsonl
```

Crawl all technology and AI sources:

```bash
scrapy crawl rss -a profile=tech
```

Example output:

```text
data/news_tech.jsonl
```

Sources and profiles are configured in:

```text
news_ingest/sources.py
```

---

## Analyze Articles with the Local LLM

Make sure Ollama is running before starting the analysis.

```bash
python news_ingest/analyze_news.py
```

The input and output paths are configured through `.env`.

Example for political/news articles:

```env
NEWS_INPUT_PATH=data/news_polit.jsonl
NEWS_ANALYZED_OUTPUT_PATH=data/analyzed_polit.jsonl
DASHBOARD_DATA_PATH=data/analyzed_polit.jsonl
```

Example for technology and AI articles:

```env
NEWS_INPUT_PATH=data/news_tech.jsonl
NEWS_ANALYZED_OUTPUT_PATH=data/analyzed_tech.jsonl
DASHBOARD_DATA_PATH=data/analyzed_tech.jsonl
```

The analysis pipeline automatically selects the correct analysis profile based on the article source and section.

---

## Political Analysis Profile

The political profile is used for general news sources such as Tagesschau, ZEIT, SPIEGEL, taz, Deutschlandfunk, ZDFheute or n-tv.

It extracts:

- neutral summary
- topic
- main political subject
- article framing orientation
- political classification
- confidence
- reasoning

Example output:

```json
{
  "analysis_profile": "political",
  "analysis": {
    "summary": "...",
    "main_political_subject": "gemischt",
    "article_framing_orientation": "mitte",
    "political_classification": "mitte",
    "confidence": 0.74,
    "reasoning": "...",
    "topic": "Innenpolitik"
  }
}
```

The political classification is article-level and describes the article's framing or perspective. It does not classify the publisher as a whole.

---

## Tech Analysis Profile

The tech profile is used for technology, IT, security and AI sources such as Heise, Golem, t3n, The Decoder or All-AI.

It extracts:

- neutral summary
- article type
- primary topic
- secondary topics
- practical applicability
- technology maturity
- target audience
- urgency
- action required
- recommended action
- opinion level
- novelty
- key technologies
- confidence
- reasoning

Example output:

```json
{
  "analysis_profile": "tech",
  "analysis": {
    "summary": "...",
    "article_type": "security_advisory",
    "primary_topic": "security",
    "secondary_topics": ["cloud_infrastructure"],
    "practicality": "high",
    "technology_maturity": "production_ready",
    "target_audience": ["admin", "security"],
    "urgency": "high",
    "action_required": true,
    "recommended_action": "Apply the available security update.",
    "opinion_level": "factual_report",
    "novelty": "breaking",
    "key_technologies": ["Linux", "OpenSSL"],
    "confidence": 0.81,
    "reasoning": "..."
  }
}
```

---

## Start the Dashboard

```bash
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

The dashboard is profile-aware.

For political/news articles it shows:

- article summary
- topic
- political classification
- framing orientation
- confidence
- reasoning
- original article link

For technology and AI articles it shows:

- article type
- primary topic
- practicality
- urgency
- action required
- target audience
- key technologies
- confidence
- reasoning
- original article link

The dashboard can be pointed to different analyzed JSONL files through `.env`.

Example for political data:

```env
DASHBOARD_DATA_PATH=data/analyzed_polit.jsonl
```

Example for tech data:

```env
DASHBOARD_DATA_PATH=data/analyzed_tech.jsonl
```

---

## Example Workflows

### Political news workflow

```bash
# 1. Start Ollama
ollama serve

# 2. Crawl political/news sources
scrapy crawl rss -a profile=polit

# 3. Configure .env
NEWS_INPUT_PATH=data/news_polit.jsonl
NEWS_ANALYZED_OUTPUT_PATH=data/analyzed_polit.jsonl
DASHBOARD_DATA_PATH=data/analyzed_polit.jsonl

# 4. Analyze articles
python news_ingest/analyze_news.py

# 5. Start dashboard
streamlit run app.py
```

### Tech and AI workflow

```bash
# 1. Start Ollama
ollama serve

# 2. Crawl technology and AI sources
scrapy crawl rss -a profile=tech

# 3. Configure .env
NEWS_INPUT_PATH=data/news_tech.jsonl
NEWS_ANALYZED_OUTPUT_PATH=data/analyzed_tech.jsonl
DASHBOARD_DATA_PATH=data/analyzed_tech.jsonl

# 4. Analyze articles
python news_ingest/analyze_news.py

# 5. Start dashboard
streamlit run app.py
```

### Single-source workflow

```bash
# Crawl only Heise
scrapy crawl rss -a source=heise

# Example output
data/news_tech_heise.jsonl
```

Then configure `.env`:

```env
NEWS_INPUT_PATH=data/news_tech_heise.jsonl
NEWS_ANALYZED_OUTPUT_PATH=data/analyzed_tech_heise.jsonl
DASHBOARD_DATA_PATH=data/analyzed_tech_heise.jsonl
```

Run:

```bash
python news_ingest/analyze_news.py
streamlit run app.py
```

---

## Recommended Models

For local analysis on consumer hardware, the following Ollama models are useful.

### Balanced default

```bash
ollama pull qwen3:4b
```

Good balance between quality, speed, and hardware requirements.

### Faster / lighter

```bash
ollama pull llama3.2:3b
```

Useful for faster batch processing.

### Higher quality, heavier

```bash
ollama pull qwen2.5:7b
```

Potentially stronger, but slower and more memory-intensive.

---

## Notes on GPU Usage

Ollama can use the GPU if a compatible GPU backend is available.

On NVIDIA systems, you can check GPU usage while the analysis is running:

```bash
nvidia-smi
```

If Ollama is using the GPU, you should see an `ollama` process and increased GPU utilization.

---

## Data Privacy

All processing is local.

The crawler stores article data in local JSONL files. The LLM analysis is performed via a local Ollama instance. No external LLM API is required.

Generated article data, model files and local environment files should not be committed.

---

## Disclaimer

The political classification is experimental and generated by a language model.

It should be understood as an article-level analytical signal, not as an objective statement about a publisher, author, or media outlet.

The system does not claim to determine political truth. It attempts to classify framing, wording, topic emphasis and article-level perspective based on the available text.

The tech classification is also experimental. Fields such as urgency, practicality or action required should be interpreted as model-generated signals and not as professional security, legal or technical advice.

---

## Legal Notes

This project is intended as a local prototype for technical experimentation and portfolio purposes.

When crawling news websites, users are responsible for respecting:

- `robots.txt`
- website terms of service
- copyright law
- publisher rights
- applicable local regulations

Do not publish full article texts unless you have the necessary rights.

---

## Roadmap

Possible next steps:

- Add persistent storage with SQLite or Postgres
- Add persistent deduplication across crawler runs
- Add event clustering across multiple news sources
- Compare reporting on the same topic across publishers
- Add source-level trend analysis
- Add more technology and AI sources
- Add AI-only dashboard filters
- Add source-level comparison for tech reporting
- Add "must know" scoring for important tech and security articles
- Add classification profiles:
  - political framing
  - tech applicability
  - security urgency
  - opinion vs factual reporting
- Add evaluation dataset for classification quality
- Add tests for JSON parsing and prompt output validation
- Add optional scheduling for daily or twice-daily local runs

---

## License

This project is currently intended as a personal portfolio and learning project.

Add a license before using or distributing it publicly.
