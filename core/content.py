import json
from core.ai import ask_ai


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
            return json.loads(response[start:end + 1])
        except Exception:
            pass
    return None


def normalize_outline(outline):
    if not isinstance(outline, dict) or "sections" not in outline:
        return outline

    for section in outline.get("sections", []):
        key_points = section.get("key_points")
        key_info = section.get("key_information")

        if key_points and isinstance(key_points, list) and not key_info:
            section["key_information"] = " ".join(key_points)
        elif key_info and not key_points:
            section["key_points"] = [key_info]

        if "purpose" not in section:
            section["purpose"] = ""
        if "narrative_goal" not in section:
            section["narrative_goal"] = ""
        if "approximate_duration" not in section:
            section["approximate_duration"] = ""

    return outline


def generate_outline(topic, duration, audience, language):
    is_dracin = "Rekap" in str(duration) or "Episode" in str(duration)

    if is_dracin:
        prompt = f"""
You are an expert Chinese Drama (Dracin) content strategist and viral recap writer.
Create a detailed video outline for a Chinese Drama recap.
DRACIN INFORMATION:
Drama Title: {topic}
Episode Scope: {duration}
Core Trope / Focus Scene: {audience}
Script Language: {language}
Return ONLY valid JSON with structure:
{{
  "topic": "{topic}",
  "duration_minutes": "{duration}",
  "target_audience": "{audience}",
  "language": "{language}",
  "sections": [
    {{
      "name": "HOOK",
      "purpose": "Shocking opening scene or dramatic conflict preview.",
      "key_information": "Most dramatic emotional peak.",
      "key_points": ["Most dramatic emotional peak."],
      "narrative_goal": "Force audience to stay.",
      "approximate_duration": "0:30"
    }},
    {{
      "name": "INTRODUCTION",
      "purpose": "Introduce main characters and premise.",
      "key_information": "Background setup.",
      "key_points": ["Background setup."],
      "narrative_goal": "Establish stakes.",
      "approximate_duration": "1:00"
    }},
    {{
      "name": "CONFLICT BUILD-UP",
      "purpose": "Escalation of conflict.",
      "key_information": "Key plot points leading to tension.",
      "key_points": ["Key plot points leading to tension."],
      "narrative_goal": "Build anticipation.",
      "approximate_duration": "2:00"
    }},
    {{
      "name": "THE CLIMAX / REVEAL",
      "purpose": "Core trope execution.",
      "key_information": "Shocking turning point.",
      "key_points": ["Shocking turning point."],
      "narrative_goal": "Deliver emotional payoff.",
      "approximate_duration": "2:00"
    }},
    {{
      "name": "OUTRO / CTA",
      "purpose": "Cliffhanger ending.",
      "key_information": "Call to action.",
      "key_points": ["Call to action."],
      "narrative_goal": "Drive comments.",
      "approximate_duration": "0:45"
    }}
  ]
}}
"""
    else:
        prompt = f"""
You are an expert YouTube content strategist.
Create a detailed long-form YouTube video outline.
VIDEO INFORMATION
Topic: {topic}
Target duration: {duration}
Target audience: {audience}
Script language: {language}
Return ONLY valid JSON with structure:
{{
  "topic": "{topic}",
  "duration_minutes": "{duration}",
  "target_audience": "{audience}",
  "language": "{language}",
  "sections": [
    {{
      "name": "HOOK",
      "purpose": "Grab attention.",
      "key_information": "Key facts.",
      "key_points": ["Key facts."],
      "narrative_goal": "Keep watching.",
      "approximate_duration": "0:30"
    }},
    {{
      "name": "INTRODUCTION",
      "purpose": "Define topic.",
      "key_information": "Background.",
      "key_points": ["Background."],
      "narrative_goal": "Set expectations.",
      "approximate_duration": "1:00"
    }},
    {{
      "name": "SEGMENT 1",
      "purpose": "First main subtopic.",
      "key_information": "Detailed explanation.",
      "key_points": ["Detailed explanation."],
      "narrative_goal": "Build foundation.",
      "approximate_duration": "2:00"
    }},
    {{
      "name": "SEGMENT 2",
      "purpose": "Second main subtopic.",
      "key_information": "Deep dive.",
      "key_points": ["Deep dive."],
      "narrative_goal": "Deepen story.",
      "approximate_duration": "2:00"
    }},
    {{
      "name": "CLOSING",
      "purpose": "Conclusion.",
      "key_information": "Final conclusion.",
      "key_points": ["Final conclusion."],
      "narrative_goal": "Impression.",
      "approximate_duration": "1:00"
    }}
  ]
}}
"""

    result = ask_ai(prompt)
    parsed = parse_json_response(result)
    return normalize_outline(parsed) if parsed else None


def regenerate_outline(topic, duration, audience, language):
    return generate_outline(topic, duration, audience, language)


def generate_script(topic, duration, audience, language, outline):
    normalized_outline = normalize_outline(outline)
    outline_json = json.dumps(normalized_outline, indent=2, ensure_ascii=False)
    is_dracin = "Rekap" in str(duration) or "Episode" in str(duration)

    if is_dracin:
        prompt = f"""
You are an expert Chinese Drama recap scriptwriter.
Write a gripping narration script based on the outline:
Title: {topic} | Scope: {duration} | Trope: {audience} | Language: {language}
OUTLINE:
{outline_json}
Return the narration script cleanly with section headers.
"""
    else:
        prompt = f"""
You are an expert YouTube scriptwriter.
Write a complete script based on the outline:
Topic: {topic} | Duration: {duration} | Audience: {audience} | Language: {language}
OUTLINE:
{outline_json}
Return narration script cleanly with section headers.
"""
    return ask_ai(prompt)


def regenerate_script(topic, duration, audience, language, outline):
    return generate_script(topic, duration, audience, language, outline)


def generate_metadata(topic, script, outline, language):
    outline_summary = json.dumps(normalize_outline(outline), ensure_ascii=False) if outline else ""
    prompt = f"""
You are a YouTube SEO and social media metadata expert.
Generate engaging hooks, clickable titles, and video description based on the actual script and outline provided.

Topic/Drama: {topic}
Language: {language}
Script Excerpt: {str(script)[:1500]}
Outline Summary: {outline_summary}

Return ONLY valid JSON matching this structure:
{{
  "hooks": [
    {{"type": "curiosity", "text": "Hook text..."}},
    {{"type": "question", "text": "Hook text..."}},
    {{"type": "surprising_fact", "text": "Hook text..."}},
    {{"type": "story", "text": "Hook text..."}},
    {{"type": "mystery", "text": "Hook text..."}}
  ],
  "titles": [
    {{"title": "Title 1", "text": "Title 1", "angle": "Angle description 1"}},
    {{"title": "Title 2", "text": "Title 2", "angle": "Angle description 2"}}
  ],
  "description": "Comprehensive video description...",
  "call_to_action": "Subscribe for more..."
}}
"""
    result = ask_ai(prompt)
    return parse_json_response(result)