from analysis_profiles import political, tech

TECH_SOURCES = {
    "heise",
    "golem",
    "t3n",
    "the_decoder",
    "all_ai",
}


TECH_SECTIONS = {
    "technologie",
    "software_development",
    "security",
}


def select_profile(article: dict) -> str:
    source = (article.get("source") or "").lower().strip()
    section = (article.get("section") or "").lower().strip()

    if source in TECH_SOURCES:
        return "tech"

    if section in TECH_SECTIONS:
        return "tech"

    return "polit"


def build_prompt(article: dict) -> tuple[str, str]:
    profile = select_profile(article)

    if profile == "tech":
        return "tech", tech.build_prompt(article)

    return "polit", political.build_prompt(article)
