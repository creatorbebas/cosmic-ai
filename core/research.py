import json
from core.ai import ask_ai, ask_ai_with_web_search_data, parse_json_response

RESEARCH_FIELDS = [
    "topic", "research_mode", "main_question", "short_answer", "executive_summary",
    "key_facts", "important_numbers", "timeline", "scientific_or_historical_context",
    "surprising_facts", "common_misconceptions", "uncertainties", "story_opportunities",
    "research_gaps", "sources"
]

def empty_research(topic="", research_mode="knowledge"):
    return {
        "topic": topic,
        "research_mode": research_mode,
        "main_question": "",
        "short_answer": "",
        "executive_summary": [],
        "key_facts": [],
        "important_numbers": [],
        "timeline": [],
        "scientific_or_historical_context": [],
        "surprising_facts": [],
        "common_misconceptions": [],
        "uncertainties": [],
        "story_opportunities": [],
        "research_gaps": [],
        "sources": []
    }

def normalize_research(research, topic, research_mode):
    if not isinstance(research, dict):
        research = {}

    result = empty_research(topic=topic, research_mode=research_mode)
    for field in RESEARCH_FIELDS:
        if field in research:
            result[field] = research[field]

    result["topic"] = result.get("topic") or topic
    result["research_mode"] = result.get("research_mode") or research_mode

    list_fields = [
        "executive_summary", "key_facts", "important_numbers", "timeline",
        "scientific_or_historical_context", "surprising_facts", "common_misconceptions",
        "uncertainties", "story_opportunities", "research_gaps", "sources"
    ]
    for field in list_fields:
        if not isinstance(result.get(field), list):
            result[field] = []

    return result

def build_research_prompt(topic, audience="General", language="English", web_enabled=False):
    web_instruction = """
WEB RESEARCH IS ENABLED. Use web search tool and prioritize reputable scientific sources. Do not fabricate URLs.
""" if web_enabled else """
WEB RESEARCH IS DISABLED. Use general knowledge only. "sources" MUST be [].
"""

    return f"""
You are the Research Engine of a professional YouTube documentary and science-content production system.
Research topic: {topic}
Target audience: {audience}
Output language: {language}
{web_instruction}

Return ONLY valid JSON using exactly this structure:
{{
  "topic": "",
  "research_mode": "",
  "main_question": "",
  "short_answer": "",
  "executive_summary": [""],
  "key_facts": [{{"fact": "", "explanation": "", "importance": "", "confidence": "high"}}],
  "important_numbers": [{{"value": "", "context": "", "importance": "", "confidence": "high"}}],
  "timeline": [{{"date_or_period": "", "event": "", "importance": ""}}],
  "scientific_or_historical_context": [""],
  "surprising_facts": [""],
  "common_misconceptions": [{{"claim": "", "reality": ""}}],
  "uncertainties": [""],
  "story_opportunities": [{{"idea": "", "why_interesting": "", "potential_section": ""}}],
  "research_gaps": [""],
  "sources": [{{"title": "", "publisher": "", "url": "", "source_type": "", "relevance": ""}}]
}}
"""

def research_topic(topic, audience="General", language="English", web_search=False):
    if not topic:
        return empty_research(topic="", research_mode="web" if web_search else "knowledge")

    research_mode = "web" if web_search else "knowledge"
    prompt = build_research_prompt(topic=topic, audience=audience, language=language, web_enabled=web_search)
    actual_sources = []

    if not web_search:
        response = ask_ai(prompt)
    else:
        web_result = ask_ai_with_web_search_data(prompt)
        if not web_result:
            return empty_research(topic=topic, research_mode="web")
        response = web_result.get("text", "")
        actual_sources = web_result.get("sources", [])

    parsed = parse_json_response(response)
    research = normalize_research(parsed, topic=topic, research_mode=research_mode)

    if web_search:
        existing_urls = set()
        for source in research.get("sources", []):
            if isinstance(source, dict) and source.get("url"):
                existing_urls.add(str(source.get("url")).strip())

        for source in actual_sources:
            if not isinstance(source, dict):
                continue
            url = str(source.get("url", "")).strip()
            if not url or url in existing_urls:
                continue
            research["sources"].append({
                "title": source.get("title", ""),
                "publisher": "",
                "url": url,
                "source_type": "web",
                "relevance": ""
            })
            existing_urls.add(url)
    else:
        research["sources"] = []

    return research

def research_project(project, web_search=False):
    if not project:
        return empty_research()
    topic = project.get("topic") or project.get("title") or ""
    audience = project.get("audience") or "General"
    language = project.get("language") or "English"
    return research_topic(topic=topic, audience=audience, language=language, web_search=web_search)