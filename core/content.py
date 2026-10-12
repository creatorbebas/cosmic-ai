import json
from core.ai import ask_ai


# ============================================================
# HELPER: NORMALISASI OUTLINE
# ============================================================

def normalize_outline(outline):
    """
    Memastikan struktur outline selalu memiliki baik 'key_information' (string)
    maupun 'key_points' (list) agar kompatibel dengan seluruh template UI & script.
    """
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


# ============================================================
# GENERATE OUTLINE (2 JALUR: DRACIN PRO & KONTEN UMUM ASLI)
# ============================================================

def generate_outline(topic, duration, audience, language):
    # Pengecekan 2 jalur persis seperti kode asli lu
    is_dracin = "Rekap" in str(duration) or "Episode" in str(duration)

    if is_dracin:
        # JALUR 1: DRAMA CINA PRO (DISEMPURNAKAN DENGAN CHARACTERS & DYNAMICS)
        prompt = f"""
You are an elite Chinese Drama (Dracin) Showrunner, Executive Producer, and Master Scriptwriter.

Create a comprehensive professional C-Drama Suite Pro production package.

PARAMETERS:
Drama Title / Topic: {topic if topic else "Auto-generate high engagement viral C-Drama trope"}
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
      "name": "Character Name 1",
      "age": "22-28",
      "appearance": "Detailed physical description, style, and aura.",
      "personality": "Core traits, strengths, flaws, and vulnerabilities.",
      "background": "Deep trauma, past betrayal, or social standing.",
      "motivation": "Ultimate goal, hidden ambition, or revenge objective."
    }}
  ],
  "dynamics": {{
    "core_conflict": "Detailed explanation of the primary dramatic conflict.",
    "internal_lead": "Psychological friction and emotional barriers.",
    "external_friction": "External pressure from toxic family or corporate rivals.",
    "relationship_map": "Brief summary of alliances and rivalries."
  }},
  "sections": [
    {{
      "name": "HOOK",
      "purpose": "Shocking opening scene or dramatic conflict preview to hook viewers instantly.",
      "key_information": "Most dramatic emotional peak from the episodes.",
      "key_points": ["Most dramatic emotional peak from the episodes."],
      "narrative_goal": "Force the audience to stay.",
      "approximate_duration": "0:30"
    }},
    {{
      "name": "INTRODUCTION",
      "purpose": "Introduce main characters, status, and initial humiliation or premise.",
      "key_information": "Background setup and character dynamics.",
      "key_points": ["Background setup and character dynamics."],
      "narrative_goal": "Establish the stakes clearly.",
      "approximate_duration": "1:00"
    }},
    {{
      "name": "CONFLICT BUILD-UP",
      "purpose": "Escalation of conflict, toxic antagonists, or hidden secrets pressure.",
      "key_information": "Key plot points leading to tension.",
      "key_points": ["Key plot points leading to tension."],
      "narrative_goal": "Build anticipation for the reveal.",
      "approximate_duration": "2:00"
    }},
    {{
      "name": "THE CLIMAX / REVEAL",
      "purpose": "The core trope execution (e.g., identity revealed, revenge served, or contract twist).",
      "key_information": "Shocking turning point and emotional satisfaction.",
      "key_points": ["Shocking turning point and emotional satisfaction."],
      "narrative_goal": "Deliver maximum emotional payoff.",
      "approximate_duration": "2:00"
    }},
    {{
      "name": "OUTRO / CTA",
      "purpose": "Cliffhanger ending or question for viewers, teasing the next part.",
      "key_information": "Call to action and engagement hook.",
      "key_points": ["Call to action and engagement hook."],
      "narrative_goal": "Drive comments and shares.",
      "approximate_duration": "0:45"
    }}
  ]
}}

RULES:
- Exactly 5 structural sections tailored for high-engagement Dracin recap, plus deep psychological character profiles and relationship dynamics.
- Do not output markdown codeblocks outside JSON.
"""
    else:
        # JALUR 2: KONTEN UMUM ASLI (100% SESUAI KODE ASLI LU SEBELUM PEROMBAKAN)
        prompt = f"""
You are an expert YouTube content strategist.

Create a detailed long-form YouTube video outline.

VIDEO INFORMATION
Topic: {topic}
Target duration: {duration}
Target audience: {audience}
Script language: {language}

Return ONLY valid JSON.
Use exactly this structure:

{{
  "topic": "{topic}",
  "duration_minutes": "{duration}",
  "target_audience": "{audience}",
  "language": "{language}",
  "sections": [
    {{
      "name": "HOOK",
      "purpose": "Grab attention immediately with curiosity.",
      "key_information": "Key facts or hooks to tease.",
      "key_points": ["Key facts or hooks to tease."],
      "narrative_goal": "Make viewers want to keep watching.",
      "approximate_duration": "0:30"
    }},
    {{
      "name": "INTRODUCTION",
      "purpose": "Define the topic and scope.",
      "key_information": "Background and thesis statement.",
      "key_points": ["Background and thesis statement."],
      "narrative_goal": "Set up clear expectations.",
      "approximate_duration": "1:00"
    }},
    {{
      "name": "SEGMENT 1",
      "purpose": "First main subtopic.",
      "key_information": "Detailed explanations and facts.",
      "key_points": ["Detailed explanations and facts."],
      "narrative_goal": "Build foundation.",
      "approximate_duration": "2:00"
    }},
    {{
      "name": "SEGMENT 2",
      "purpose": "Second main subtopic or deep dive.",
      "key_information": "Detailed explanations and evidence.",
      "key_points": ["Detailed explanations and evidence."],
      "narrative_goal": "Deepen the story.",
      "approximate_duration": "2:00"
    }},
    {{
      "name": "CLOSING",
      "purpose": "Summarize and conclude.",
      "key_information": "Final conclusions and call to action.",
      "key_points": ["Final conclusions and call to action."],
      "narrative_goal": "Leave a lasting impression.",
      "approximate_duration": "1:00"
    }}
  ]
}}

RULES:
- Avoid repetition and build progressive curiosity.
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
# GENERATE SCRIPT (2 JALUR: DRACIN PRO & KONTEN UMUM ASLI)
# ============================================================

def generate_script(topic, duration, audience, language, outline):
    normalized_outline = normalize_outline(outline)
    outline_json = json.dumps(normalized_outline, indent=2, ensure_ascii=False)
    is_dracin = "Rekap" in str(duration) or "Episode" in str(duration)

    if is_dracin:
        # SCRIPT JALUR 1: DRAMA CINA PRO
        prompt = f"""
You are an expert Chinese Drama (Dracin) recap scriptwriter and dialogue director.

Write a gripping, highly engaging, and emotional spoken narration script based on the structured outline below.

DRACIN INFORMATION:
Drama Title: {topic}
Episode Scope: {duration}
Core Trope & Parameters: {audience}
Script Language: {language}

STRUCTURED OUTLINE & CHARACTERS:
{outline_json}

SCRIPT REQUIREMENTS:
- Write natural, dramatic, and compelling spoken narration optimized for TikTok, Reels, or YouTube recap videos.
- Avoid camera directions, visual cues, or technical production notes.
- Use section headers matching the outline exactly.
"""
    else:
        # SCRIPT JALUR 2: KONTEN UMUM ASLI (100% SESUAI KODE ASLI LU)
        prompt = f"""
You are an expert YouTube scriptwriter.

Write a complete narration script based on the structured outline below.

VIDEO INFORMATION:
Topic: {topic}
Target duration: {duration}
Target audience: {audience}
Script language: {language}

STRUCTURED OUTLINE:
{outline_json}

SCRIPT REQUIREMENTS:
- Follow the outline order exactly.
- Write natural spoken narration without visual/camera cues or editing notes.
- Use clear section headers matching the outline.
"""
    return ask_ai(prompt)


def regenerate_script(topic, duration, audience, language, outline):
    return generate_script(topic, duration, audience, language, outline)


# ============================================================
# GENERATE METADATA
# ============================================================

def generate_metadata(topic, script, outline, language):
    prompt = f"""
You are a YouTube SEO and social media metadata expert.

Generate engaging hooks, clickable titles, and a video description for this content.

Topic/Drama: {topic}
Language: {language}

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
    if not result:
        return None

    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return None