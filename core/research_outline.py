import json

from core.ai import ask_ai


SCRIPT_SECTION_NAMES = [
    "HOOK",
    "INTRO",
    "SEGMENT 1",
    "SEGMENT 2",
    "SEGMENT 3",
    "TWIST",
    "CLOSING"
]


def empty_outline():
    return {
        "sections": [
            {
                "name": name,
                "purpose": "",
                "key_points": []
            }
            for name in SCRIPT_SECTION_NAMES
        ]
    }


def parse_json_response(response):
    if not response:
        return None

    response = str(response).strip()

    try:
        return json.loads(response)
    except Exception:
        pass

    if "```json" in response:
        try:
            content = response.split("```json", 1)[1]
            content = content.split("```", 1)[0]
            return json.loads(content.strip())
        except Exception:
            pass

    if "```" in response:
        try:
            content = response.split("```", 1)[1]
            content = content.split("```", 1)[0]
            return json.loads(content.strip())
        except Exception:
            pass

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


def normalize_outline(outline):
    if not isinstance(outline, dict):
        return empty_outline()

    sections = outline.get("sections")

    if not isinstance(sections, list):
        return empty_outline()

    normalized = []

    for section_name in SCRIPT_SECTION_NAMES:

        found = None

        for section in sections:

            if not isinstance(section, dict):
                continue

            name = str(
                section.get("name", "")
            ).strip().upper()

            if name == section_name:
                found = section
                break

        if found:

            key_points = found.get(
                "key_points",
                []
            )

            if not isinstance(key_points, list):
                key_points = []

            normalized.append({
                "name": section_name,
                "purpose": str(
                    found.get("purpose", "")
                ).strip(),
                "key_points": [
                    str(point).strip()
                    for point in key_points
                    if str(point).strip()
                ]
            })

        else:

            normalized.append({
                "name": section_name,
                "purpose": "",
                "key_points": []
            })

    return {
        "sections": normalized
    }


def build_research_outline_prompt(
    project,
    research
):
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

    research_json = json.dumps(
        research,
        ensure_ascii=False,
        indent=2
    )

    return f"""
You are the Outline Engine of Cosmic-AI,
a professional YouTube documentary production system.

Transform the research dossier below into a strong
narrative YouTube outline.

PROJECT TOPIC:
{topic}

TARGET AUDIENCE:
{audience}

LANGUAGE:
{language}

RESEARCH DOSSIER:
{research_json}

RULES:

1. Use the research dossier as the factual foundation.
2. Do not invent unsupported facts.
3. Prioritize established facts.
4. Distinguish uncertainty from established knowledge.
5. Do not turn the outline into a list of facts.
6. Build a narrative with escalating curiosity.
7. Avoid repeating the same information.
8. Use important numbers only when they strengthen the story.
9. Use surprising facts strategically.
10. Use scientific disagreements or uncertainties when they
    create meaningful tension.
11. The HOOK must immediately create curiosity.
12. The INTRO establishes the central mystery or question.
13. SEGMENT 1 establishes the foundation.
14. SEGMENT 2 develops the investigation and evidence.
15. SEGMENT 3 introduces a complication, conflict,
    competing explanation, or major discovery.
16. TWIST contains the strongest unexpected revelation
    supported by the research.
17. CLOSING resolves or reframes the central question.
18. Do not write the full script.
19. Produce an outline only.

STRUCTURE:

HOOK
Immediate curiosity and the strongest opening question/fact.

INTRO
Explain what the video investigates and establish
the central question.

SEGMENT 1
Scientific or historical foundation.

SEGMENT 2
Main investigation and evidence.

SEGMENT 3
Complication, uncertainty, conflict, or major discovery.

TWIST
Strongest unexpected insight supported by research.

CLOSING
Resolve or reframe the central question and leave
the viewer with a memorable final thought.

Return ONLY valid JSON.

Use exactly this structure:

{{
  "sections": [
    {{
      "name": "HOOK",
      "purpose": "",
      "key_points": []
    }},
    {{
      "name": "INTRO",
      "purpose": "",
      "key_points": []
    }},
    {{
      "name": "SEGMENT 1",
      "purpose": "",
      "key_points": []
    }},
    {{
      "name": "SEGMENT 2",
      "purpose": "",
      "key_points": []
    }},
    {{
      "name": "SEGMENT 3",
      "purpose": "",
      "key_points": []
    }},
    {{
      "name": "TWIST",
      "purpose": "",
      "key_points": []
    }},
    {{
      "name": "CLOSING",
      "purpose": "",
      "key_points": []
    }}
  ]
}}
"""


def generate_outline_from_research(
    project,
    research
):
    if not project:
        return empty_outline()

    if not research:
        return empty_outline()

    prompt = build_research_outline_prompt(
        project=project,
        research=research
    )

    response = ask_ai(prompt)

    parsed = parse_json_response(response)

    return normalize_outline(parsed)