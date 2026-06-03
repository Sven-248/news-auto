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
Du analysierst einen deutschsprachigen Nachrichtenartikel.

Aufgaben:
1. Fasse den Artikel neutral in 5-8 Sätzen zusammen.
2. Bestimme das politische Hauptthema des Artikels, falls vorhanden. Ordne nicht das Thema selbst als links/rechts ein.
3. Ordne die politische Perspektive bzw. das Framing des Artikels ein: links, mitte, rechts oder unklar.
4. Begründe die Einordnung anhand von Sprache, Framing, Themengewichtung, Problemdefinition, Wertung und Perspektive.

Wichtig:
- Ignoriere ausdrücklich Navigation, Menüs, Teaser, Footer, Schlagwortlisten, Werbung, Empfehlungen, Links zu anderen Artikeln und Seitenelemente. Analysiere nur den erkennbaren Fließtext des eigentlichen Artikels.
- Ordne nicht danach ein, über welche Partei, Bewegung oder Position berichtet wird.
- Ein Artikel über rechte Akteure ist nicht automatisch rechts.
- Ein Artikel über linke Akteure ist nicht automatisch links.
- Entscheidend ist, welche Perspektive, Wertung, Sprache, Problemdefinition und Lösungsvorstellung der Artikel selbst nahelegt.
- Wenn der Artikel überwiegend neutral berichtet oder keine klare wertende Perspektive erkennbar ist, wähle "unklar", nicht "mitte". Verwende "mitte" nur, wenn der Artikel ausdrücklich eine moderierende, ausgleichende oder zentristische politische Perspektive erkennen lässt.
- Bewerte nicht die Quelle pauschal, sondern nur diesen einzelnen Artikel.
- Jede Einordnung zu Framing oder politischer Perspektive muss auf konkreten Formulierungen aus dem Artikel beruhen. Wenn keine konkreten Textbelege vorhanden sind, muss article_framing_orientation "unklar" sein.

Gib ausschließlich valides JSON zurück, ohne Markdown.

Schema:
{{
  "summary": "...",
  "analysis_profile": "political",
  "main_political_subject": "...",
  "article_framing_orientation": "links|mitte|rechts|unklar",
  "political_classification": "links|mitte|rechts|unklar",
  "confidence": 0.0,
  "reasoning": "...",
  "topic": "..."
}}

Hinweis:
- "main_political_subject" beschreibt, worum es politisch geht. Wähle große Themengebiete wie beispielsweise: innenpolitik, wirtschaft, etc.
- "article_framing_orientation" beschreibt, aus welcher Perspektive der Artikel selbst framed.
- "political_classification" soll denselben Wert wie "article_framing_orientation" enthalten, damit bestehende Dashboards weiter funktionieren.

Artikel:
{text}
""".strip()
