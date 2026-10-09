import json

from core.ai import ask_ai


SCRIPT_SECTION_NAMES = [
    "HOOK",
    "INTRO",
    "SEGMENT 1",
    "SEGMENT 2",
    "SEGMENT 3",
    "TWIST",
    "CLOSING",
]


def parse_json_response(text):
    if not text:
        return None

    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    if "```json" in text:
        text = text.split("```json", 1)[1]

        if "```" in text:
            text = text.split("```", 1)[0]

        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

    if "```" in text:
        parts = text.split("```")

        for part in parts:
            part = part.strip()

            if not part:
                continue

            try:
                return json.loads(part)
            except json.JSONDecodeError:
                continue

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


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

            name = str(
                item.get("name", "")
            ).strip().upper()

            if name == section_name:
                found = item
                break

        if found is None:
            return None

        content = str(
            found.get("content", "")
        ).strip()

        if not content:
            return None

        normalized.append(
            {
                "name": section_name,
                "content": content,
            }
        )

    return {
        "sections": normalized
    }


def build_script_prompt(project, outline):
    topic = project.get("topic", "")
    duration = project.get("duration", "")
    audience = project.get("audience", "")
    language = project.get("language", "")

    outline_text = json.dumps(
        outline,
        ensure_ascii=False,
        indent=2
    )

    return f"""
You are the senior documentary scriptwriter for Cosmic AI.

Your task is to transform the provided VIDEO OUTLINE into a complete
YouTube documentary script.

PROJECT
Topic: {topic}
Target duration: {duration}
Audience: {audience}
Language: {language}

IMPORTANT RULES

1. Use the outline as the structural source of truth.
2. Do not invent unsupported facts.
3. Do not simply copy the outline.
4. Expand every important key point into natural spoken narration.
5. Write for voice-over, not for an article.
6. Use clear, natural sentences that sound good when spoken aloud.
7. Maintain a strong curiosity gap throughout the video.
8. The HOOK must immediately create curiosity.
9. The INTRO must establish the central question.
10. Each segment should naturally lead into the next.
11. Use mini-hooks and transitions where appropriate.
12. The TWIST must deliver a meaningful revelation or reframing.
13. The CLOSING must resolve the central question and leave a memorable
    final thought.
14. Avoid repetitive wording.
15. Avoid generic filler.
16. Do not use bullet points inside the script.
17. Do not use section numbers inside the narration.
18. Do not write production directions such as [B-ROLL], [MUSIC], or
    [PAUSE].
19. Do not address the audience excessively with phrases like
    "guys", "you won't believe", or "let's dive in".
20. Keep the scientific meaning accurate.
21. If the outline marks something as speculative, preserve that
    uncertainty in the narration.
22. The final script must feel like one continuous documentary story.

SCRIPT STRUCTURE

The script MUST contain exactly these seven sections:

HOOK
INTRO
SEGMENT 1
SEGMENT 2
SEGMENT 3
TWIST
CLOSING

Return ONLY valid JSON.

Use exactly this structure:

{{
  "sections": [
    {{
      "name": "HOOK",
      "content": "..."
    }},
    {{
      "name": "INTRO",
      "content": "..."
    }},
    {{
      "name": "SEGMENT 1",
      "content": "..."
    }},
    {{
      "name": "SEGMENT 2",
      "content": "..."
    }},
    {{
      "name": "SEGMENT 3",
      "content": "..."
    }},
    {{
      "name": "TWIST",
      "content": "..."
    }},
    {{
      "name": "CLOSING",
      "content": "..."
    }}
  ]
}}

VIDEO OUTLINE:

{outline_text}
"""



def generate_script_from_outline(project, outline):
    if not outline:
        return None

    prompt = build_script_prompt(
        project,
        outline
    )

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

        output.append(name)
        output.append("")
        output.append(content)
        output.append("")

    return "\n".join(output).strip()