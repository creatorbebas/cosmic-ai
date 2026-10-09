import json

from core.ai import (
    ask_ai,
    ask_ai_with_web_search_data
)


RESEARCH_FIELDS = [
    "topic",
    "research_mode",
    "main_question",
    "short_answer",
    "executive_summary",
    "key_facts",
    "important_numbers",
    "timeline",
    "scientific_or_historical_context",
    "surprising_facts",
    "common_misconceptions",
    "uncertainties",
    "story_opportunities",
    "research_gaps",
    "sources"
]


def empty_research(
    topic="",
    research_mode="knowledge"
):

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


def parse_json_response(response):

    if not response:
        return None

    response = str(response).strip()

    # ---------------------------------------------------------
    # Direct JSON
    # ---------------------------------------------------------

    try:
        return json.loads(response)

    except Exception:
        pass

    # ---------------------------------------------------------
    # JSON code block
    # ---------------------------------------------------------

    if "```json" in response:

        try:

            content = response.split("```json", 1)[1]
            content = content.split("```", 1)[0]

            return json.loads(content.strip())

        except Exception:
            pass

    # ---------------------------------------------------------
    # Generic code block
    # ---------------------------------------------------------

    if "```" in response:

        try:

            content = response.split("```", 1)[1]
            content = content.split("```", 1)[0]

            return json.loads(content.strip())

        except Exception:
            pass

    # ---------------------------------------------------------
    # Find first JSON object
    # ---------------------------------------------------------

    start = response.find("{")
    end = response.rfind("}")

    if start != -1 and end != -1 and end > start:

        try:

            return json.loads(
                response[start:end + 1]
            )

        except Exception:
            pass

    return None


def normalize_research(
    research,
    topic,
    research_mode
):

    if not isinstance(research, dict):

        research = {}

    result = empty_research(
        topic=topic,
        research_mode=research_mode
    )

    for field in RESEARCH_FIELDS:

        if field in research:
            result[field] = research[field]

    result["topic"] = (
        result.get("topic")
        or topic
    )

    result["research_mode"] = (
        result.get("research_mode")
        or research_mode
    )

    # ---------------------------------------------------------
    # Safety normalization
    # ---------------------------------------------------------

    list_fields = [
        "executive_summary",
        "key_facts",
        "important_numbers",
        "timeline",
        "scientific_or_historical_context",
        "surprising_facts",
        "common_misconceptions",
        "uncertainties",
        "story_opportunities",
        "research_gaps",
        "sources"
    ]

    for field in list_fields:

        if not isinstance(result.get(field), list):
            result[field] = []

    return result


def build_research_prompt(
    topic,
    audience="General",
    language="English",
    web_enabled=False
):

    web_instruction = ""

    if web_enabled:

        web_instruction = """
WEB RESEARCH IS ENABLED.

Use the web search tool to research the topic.

Prioritize:
- peer-reviewed papers
- NASA / ESA / official scientific institutions
- universities
- recognized scientific organizations
- reputable science publications
- review papers
- authoritative databases

Do not invent papers, sources, authors, URLs, statistics,
or publication details.

When evidence conflicts, explicitly explain the disagreement.

Use current and historically important sources where relevant.

The final JSON "sources" field should contain sources that
were actually used during the research.
"""

    else:

        web_instruction = """
WEB RESEARCH IS DISABLED.

Use general model knowledge only.

Do NOT invent URLs or pretend that sources were checked.

The "sources" array must therefore remain empty.
"""

    prompt = f"""
You are the Research Engine of a professional YouTube
documentary and science-content production system.

Research topic:
{topic}

Target audience:
{audience}

Output language:
{language}

{web_instruction}

Your goal is NOT simply to explain the topic.

Build a research dossier that can later be converted into:
Research → Outline → Script → Scene Planner.

Requirements:

1. Separate established facts from speculation.
2. Identify important scientific or historical context.
3. Include important numbers only when meaningful.
4. Identify uncertainty and disagreements.
5. Identify common misconceptions.
6. Find surprising facts useful for storytelling.
7. Identify potential story structures and hooks.
8. Identify research gaps.
9. Avoid sensational claims that are unsupported.
10. Do not fabricate citations.
11. Do not fabricate URLs.
12. If an exact number is uncertain, say so.
13. If a claim is speculative, label it as speculative.
14. Prefer primary or authoritative sources.

Return ONLY valid JSON.

Use exactly this structure:

{{
  "topic": "",
  "research_mode": "",
  "main_question": "",
  "short_answer": "",
  "executive_summary": [
    ""
  ],
  "key_facts": [
    {{
      "fact": "",
      "explanation": "",
      "importance": "",
      "confidence": "high"
    }}
  ],
  "important_numbers": [
    {{
      "value": "",
      "context": "",
      "importance": "",
      "confidence": "high"
    }}
  ],
  "timeline": [
    {{
      "date_or_period": "",
      "event": "",
      "importance": ""
    }}
  ],
  "scientific_or_historical_context": [
    ""
  ],
  "surprising_facts": [
    ""
  ],
  "common_misconceptions": [
    {{
      "claim": "",
      "reality": ""
    }}
  ],
  "uncertainties": [
    ""
  ],
  "story_opportunities": [
    {{
      "idea": "",
      "why_interesting": "",
      "potential_section": ""
    }}
  ],
  "research_gaps": [
    ""
  ],
  "sources": [
    {{
      "title": "",
      "publisher": "",
      "url": "",
      "source_type": "",
      "relevance": ""
    }}
  ]
}}

Important:

If web research is disabled:
"sources" MUST be [].

If web research is enabled:
only include real sources actually used or returned
by the web research process.

Do not create fake URLs.
"""


    return prompt


def research_topic(
    topic,
    audience="General",
    language="English",
    web_search=False
):

    if not topic:
        return empty_research(
            topic="",
            research_mode=(
                "web"
                if web_search
                else "knowledge"
            )
        )

    research_mode = (
        "web"
        if web_search
        else "knowledge"
    )

    prompt = build_research_prompt(
        topic=topic,
        audience=audience,
        language=language,
        web_enabled=web_search
    )

    actual_sources = []

    # ---------------------------------------------------------
    # AI Knowledge Research
    # ---------------------------------------------------------

    if not web_search:

        response = ask_ai(prompt)

    # ---------------------------------------------------------
    # Web Research
    # ---------------------------------------------------------

    else:

        web_result = ask_ai_with_web_search_data(
            prompt
        )

        if not web_result:

            return empty_research(
                topic=topic,
                research_mode="web"
            )

        response = web_result.get(
            "text",
            ""
        )

        actual_sources = web_result.get(
            "sources",
            []
        )

    parsed = parse_json_response(
        response
    )

    research = normalize_research(
        parsed,
        topic=topic,
        research_mode=research_mode
    )

    # ---------------------------------------------------------
    # Merge actual web sources
    # ---------------------------------------------------------

    if web_search:

        existing_urls = set()

        for source in research.get("sources", []):

            if not isinstance(source, dict):
                continue

            url = str(
                source.get("url", "")
            ).strip()

            if url:
                existing_urls.add(url)

        for source in actual_sources:

            if not isinstance(source, dict):
                continue

            url = str(
                source.get("url", "")
            ).strip()

            if not url:
                continue

            if url in existing_urls:
                continue

            research["sources"].append({
                "title": source.get(
                    "title",
                    ""
                ),
                "publisher": "",
                "url": url,
                "source_type": "web",
                "relevance": ""
            })

            existing_urls.add(url)

    else:

        research["sources"] = []

    return research


def research_project(
    project,
    web_search=False
):

    if not project:
        return empty_research()

    topic = (
        project.get("topic")
        or project.get("title")
        or ""
    )

    audience = (
        project.get("audience")
        or "General"
    )

    language = (
        project.get("language")
        or "English"
    )

    return research_topic(
        topic=topic,
        audience=audience,
        language=language,
        web_search=web_search
    )