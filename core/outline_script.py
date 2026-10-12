import json
from core.ai import ask_ai, parse_json_response

SCRIPT_SECTION_NAMES = [
    "HOOK", "INTRO", "SEGMENT 1", "SEGMENT 2", "SEGMENT 3", "TWIST", "CLOSING",
]

def normalize_script(data):
    if not isinstance(data, dict):
        return None
    sections = data.get("sections")
    if not isinstance(sections, list):
        return None

    normalized = []
    for section_name in SCRIPT_SECTION_NAMES:
        found = None
        for item in sections:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip().upper()
            if name == section_name:
                found = item
                break

        if found is None:
            return None
        content = str(found.get("content", "")).strip()
        if not content:
            return None
        normalized.append({"name": section_name, "content": content})

    return {"sections": normalized}

def generate_script_from_outline(project, outline):
    if not outline:
        return None
    
    topic = project.get("topic", "")
    duration = project.get("duration", "")
    audience = project.get("audience", "")
    language = project.get("language", "")
    outline_text = json.dumps(outline, ensure_ascii=False, indent=2)

    prompt = f"""
You are the senior documentary scriptwriter for Cosmic AI. Transform the provided VIDEO OUTLINE into a complete YouTube documentary script.
PROJECT: Topic: {topic}, Target duration: {duration}, Audience: {audience}, Language: {language}

Return ONLY valid JSON using exactly this structure:
{{
  "sections": [
    {{"name": "HOOK", "content": "..."}},
    {{"name": "INTRO", "content": "..."}},
    {{"name": "SEGMENT 1", "content": "..."}},
    {{"name": "SEGMENT 2", "content": "..."}},
    {{"name": "SEGMENT 3", "content": "..."}},
    {{"name": "TWIST", "content": "..."}},
    {{"name": "CLOSING", "content": "..."}}
  ]
}}
VIDEO OUTLINE:
{outline_text}
"""
    response = ask_ai(prompt)
    data = parse_json_response(response)
    return normalize_script(data)

def script_to_text(script):
    if not isinstance(script, dict):
        return ""
    sections = script.get("sections", [])
    output = []
    for section in sections:
        name = section.get("name", "")
        content = section.get("content", "")
        if not name or not content:
            continue
        output.extend([name, "", content, ""])
    return "\n".join(output).strip()