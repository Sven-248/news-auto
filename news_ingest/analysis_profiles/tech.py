def build_prompt(article: dict) -> str:
    title = article.get("title") or ""
    teaser = article.get("teaser") or ""
    full_text = article.get("full_text") or ""

    text = f"""
Titel:
{title}

Teaser:
{teaser}

Artikeltext:
{full_text}
""".strip()

    return f"""
Du analysierst einen deutschsprachigen Technologie-, IT- oder Wissenschaftsartikel.

Aufgaben:
1. Fasse den Artikel neutral in 5-8 Sätzen zusammen.
2. Klassifiziere den Artikeltyp.
3. Bestimme das technische Themengebiet.
4. Bewerte die praktische Anwendbarkeit für Leser.
5. Bestimme die Zielgruppen.
6. Schätze Dringlichkeit und Risiko ein.
7. Gib an, ob eine konkrete Handlung erforderlich ist.
8. Bewerte, ob der Artikel eher faktisch, analytisch, meinungsstark, werblich oder kritisch ist.
9. Nenne zentrale Technologien, Produkte, Organisationen oder Standards.

Wichtig:
- Bewerte nicht die Quelle pauschal, sondern nur diesen einzelnen Artikel.
- "practicality" bedeutet: Kann ein Leser daraus direkt etwas umsetzen, testen, konfigurieren oder entscheiden?
- "action_required" soll nur true sein, wenn aus dem Artikel eine konkrete Handlung folgt, z.B. patchen, prüfen, migrieren, absichern, vermeiden oder evaluieren.
- Bei reinen Branchennews, Produktankündigungen oder Hintergrundtexten ist "action_required" meistens false.
- Bei Sicherheitslücken, aktiven Angriffen, kritischen Updates oder rechtlichen Pflichten kann "urgency" high oder critical sein.

Wenn der Artikel sich um künstliche Intelligenz dreht, unterscheide möglichst:
- llm: Sprachmodelle, Chatbots, lokale Modelle, RAG, Agenten
- ai_tools: konkrete KI-Tools oder Workflows
- ai_research: Forschung, Papers, Benchmarks, Modellarchitekturen
- ai_business: Unternehmen, Investments, Markt, Produktstrategie
- law_policy: Regulierung, AI Act, Urheberrecht, Datenschutz

Gib ausschließlich valides JSON zurück, ohne Markdown.

Schema:
{{
  "summary": "...",
  "analysis_profile": "tech",
  "article_type": "news|analysis|opinion|review|tutorial|security_advisory|research|interview|other",
  "primary_topic": "security|ai_ml|llm|ai_tools|ai_research|ai_business|software_development|cloud_infrastructure|hardware|operating_systems|open_source|privacy_data_protection|law_policy|consumer_tech|business_industry|science_research|mobility|gaming_entertainment|other",
  "secondary_topics": ["..."],
  "practicality": "high|medium|low|none",
  "technology_maturity": "experimental|emerging|production_ready|legacy|deprecated|unclear",
  "target_audience": ["developer", "admin", "security", "consumer", "management", "research"],
  "urgency": "low|medium|high|critical",
  "action_required": true,
  "recommended_action": "...",
  "opinion_level": "factual_report|balanced_analysis|opinionated|promotional|critical_review",
  "novelty": "breaking|new_release|incremental_update|background|recap|speculation",
  "key_technologies": ["..."],
  "confidence": 0.0,
  "reasoning": "..."
}}

Artikel:
{text}
""".strip()
