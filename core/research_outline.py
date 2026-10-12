import json
from core.ai import ask_ai, parse_json_response

SCRIPT_SECTION_NAMES = [
    "HOOK", "INTRO", "SEGMENT 1", "SEGMENT 2", "SEGMENT 3", "TWIST", "CLOSING"
]

def empty_outline():
    return {
        "sections": [
            {"name": name, "purpose": "", "key_points": []}
            for name in SCRIPT_SECTION_NAMES
        ]
    }

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
            name = str(section.get("name", "")).strip().upper()
            if name == section_name:
                found = section
                break

        if found:
            key_points = found.get("key_points", [])
            if not isinstance(key_points, list):
                key_points = []
            normalized.append({
                "name": section_name,
                "purpose": str(found.get("purpose", "")).strip(),
                "key_points": [str(p).strip() for p in key_points if str(p).strip()]
            })
        else:
            normalized.append({"name": section_name, "purpose": "", "key_points": []})

    return {"sections": normalized}

def build_research_outline_prompt(project, research):
    topic = project.get("topic") or project.get("title") or ""
    audience = project.get("audience") or "General"
    language = project.get("language") or "English"
    research_json = json.dumps(research, ensure_ascii=False, indent=2)

    return f"""
You are the Outline Engine of Cosmic-AI, a professional YouTube documentary production system.
Transform the research dossier below into a strong narrative YouTube outline.
PROJECT TOPIC: {topic}
TARGET AUDIENCE: {audience}
LANGUAGE: {language}
RESEARCH DOSSIER:
{research_json}

Return ONLY valid JSON using exactly this structure:
{{
  "sections": [
    {{"name": "HOOK", "purpose": "", "key_points": []}},
    {{"name": "INTRO", "purpose": "", "key_points": []}},
    {{"name": "SEGMENT 1", "purpose": "", "key_points": []}},
    {{"name": "SEGMENT 2", "purpose": "", "key_points": []}},
    {{"name": "SEGMENT 3", "purpose": "", "key_points": []}},
    {{"name": "TWIST", "purpose": "", "key_points": []}},
    {{"name": "CLOSING", "purpose": "", "key_points": []}}
  ]
}}
"""

def generate_outline_from_research(project, research):
    if not project or not research:
        return empty_outline()
    prompt = build_research_outline_prompt(project=project, research=research)
    response = ask_ai(prompt)
    parsed = parse_json_response(response)
    return normalize_outline(parsed)