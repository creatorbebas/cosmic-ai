import json
from core.ai import ask_ai


# ============================================================
# HELPER: NORMALISASI OUTLINE & PRO ENGINE STRUCTURE
# ============================================================

def normalize_outline(outline):
    """
    Memastikan struktur outline & data engine pro selalu valid.
    """
    if not isinstance(outline, dict):
        return {
            "topic": "C-Drama Pro Production",
            "sections": [],
            "characters": [],
            "dynamics": {}
        }

    if "sections" not in outline:
        outline["sections"] = []

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


# ============================================================
# GENERATE C-DRAMA ENGINE SUITE PRO (OUTLINE, CHARACTERS, DYNAMICS)
# ============================================================

def generate_outline(topic, duration, audience, language):
    # Parameter tambahan yang dikirim dari form Engine Pro
    # audience parameter disini bisa menampung gabungan parameter pro
    prompt = f"""
You are an elite Chinese Drama (Dracin) Showrunner, Executive Producer, and Master Scriptwriter.

Create a comprehensive professional C-Drama Suite Pro production package.

PARAMETERS:
Topic / Initial Idea: {topic if topic else "Auto-generate high engagement viral C-Drama trope"}
Episode Scope: {duration}
Story Parameters / Tropes & Focus: {audience}
Script Language: {language}

Return ONLY valid JSON.
Use exactly this strict structure:

{{
  "topic": "{topic if topic else 'Custom C-Drama Production'}",
  "duration_minutes": "{duration}",
  "target_audience": "{audience}",
  "language": "{language}",
  "characters": [
    {{
      "name": "Character Name 1 (Mandarin character if applicable)",
      "age": "22-28",
      "appearance": "Detailed physical description, style, and aura.",
      "personality": "Core traits, core strengths, flaws, and emotional vulnerabilities.",
      "background": "Deep trauma, past betrayal, or social standing background.",
      "motivation": "Ultimate goal, hidden ambition, or driving revenge objective."
    },
    {{
      "name": "Character Name 2",
      "age": "25-32",
      "appearance": "Physical description and presence.",
      "personality": "Traits and flaws.",
      "background": "Background history.",
      "motivation": "Core objective."
    }}
  ],
  "dynamics": {{
    "core_conflict": "Detailed explanation of the primary dramatic conflict between main leads and antagonists.",
    "internal_lead": "Psychological friction and emotional barriers of the main characters.",
    "external_friction": "External pressure from toxic family, corporate rivals, or social status gaps.",
    "relationship_map": "Brief summary of character alliances and rivalries."
  }},
  "sections": [
    {{
      "name": "EPISODE 1: TABRAKAN TAKDIR & PENGHINAAN",
      "purpose": "Opening hook, establishing humiliation, and initial dramatic encounter.",
      "key_information": "Key plot events for episode 1.",
      "key_points": ["Key plot event 1", "Key plot event 2"],
      "narrative_goal": "Hook viewers instantly.",
      "approximate_duration": "2:00"
    }},
    {{
      "name": "EPISODE 2: IDENTITAS TERSEMBUNYI",
      "purpose": "Escalation of tension and secret power hints.",
      "key_information": "Key plot events for episode 2.",
      "key_points": ["Key plot event 1", "Key plot event 2"],
      "narrative_goal": "Build anticipation.",
      "approximate_duration": "2:00"
    }}
  ]
}}

RULES:
- Generate at least 5 to 10 detailed structural episode sections fitting the scope.
- Include deep psychological character profiles and rich relationship dynamics.
- Do not output markdown codeblocks outside JSON.
"""

    result = ask_ai(prompt)
    if not result:
        return None

    try:
        data = json.loads(result)
        return normalize_outline(data)
    except json.JSONDecodeError:
        return None


def regenerate_outline(topic, duration, audience, language):
    return generate_outline(topic, duration, audience, language)


# ============================================================
# GENERATE SCRIPT PRO (C-DRAMA ENGINE SUITE)
# ============================================================

def generate_script(topic, duration, audience, language, outline):
    normalized_outline = normalize_outline(outline)
    outline_json = json.dumps(normalized_outline, indent=2, ensure_ascii=False)

    prompt = f"""
You are an expert Chinese Drama (Dracin) master scriptwriter and dialogue director.

Write a gripping, highly emotional, and cinematic spoken narration script for all episodes/sections based on the structured C-Drama Engine Suite Pro outline below.

PRODUCTION PARAMETERS:
Drama Title: {topic}
Episode Scope: {duration}
Core Parameters: {audience}
Script Language: {language}

STRUCTURED OUTLINE & CHARACTERS:
{outline_json}

SCRIPT REQUIREMENTS:
- Write natural, dramatic, high-tension spoken narration optimized for TikTok, Reels, or Short-form drama apps.
- Include cinematic visual prompts (e.g., [VISUAL: Close up wajah terkejut...]) before dramatic lines.
- Follow section headers matching the outline exactly.
"""

    return ask_ai(prompt)


def regenerate_script(topic, duration, audience, language, outline):
    return generate_script(topic, duration, audience, language, outline)


# ============================================================
# GENERATE METADATA PRO
# ============================================================

def generate_metadata(topic, script, outline, language):
    prompt = f"""
You are a C-Drama marketing and social media viral strategist.

Generate viral hooks, catchy titles, and a video description optimized for C-Drama recap channels.

Topic/Drama: {topic}
Language: {language}

Return ONLY valid JSON matching this structure:

{{
  "hooks": [
    {{"type": "shocking", "text": "Hook text..."}},
    {{"type": "emotional", "text": "Hook text..."}},
    {{"type": "revenge", "text": "Hook text..."}},
    {{"type": "secret", "text": "Hook text..."}},
    {{"type": "cliffhanger", "text": "Hook text..."}}
  ],
  "titles": [
    {{"title": "Title 1", "text": "Title 1", "angle": "Viral TikTok Angle 1"}},
    {{"title": "Title 2", "text": "Title 2", "angle": "Viral YouTube Angle 2"}}
  ],
  "description": "Comprehensive viral video description with hashtags...",
  "call_to_action": "Like & follow untuk part selanjutnya..."
}}
"""
    result = ask_ai(prompt)
    if not result:
        return None

    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return None