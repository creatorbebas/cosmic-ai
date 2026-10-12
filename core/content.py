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
# GENERATE OUTLINE (PEMISAHAN TOTAL C-DRAMA & KONTEN UMUM)
# ============================================================

def generate_outline(topic, duration, audience, language):
    is_dracin = "Rekap" in str(duration) or "Episode" in str(duration)

    if is_dracin:
        prompt = f"""
You are the Master Showrunner and Executive Producer for C-Drama Engine Suite Pro.
Create a professional pre-production dossier and multi-episode outline for a Chinese Drama based on these parameters:

Drama Title / Concept: {topic}
Episode Scope: {duration}
Core Trope / Focus: {audience}
Script Language: {language}

Return ONLY valid JSON.
Use exactly this structure with these exact section names:

{{
  "topic": "{topic}",
  "duration_minutes": "{duration}",
  "target_audience": "{audience}",
  "language": "{language}",
  "sections": [
    {{
      "name": "Draf Karakter Utama",
      "purpose": "Detailed character profiles including background, core motivation, strengths, and flaws.",
      "key_information": "1. [Nama Karakter Utama 1]\n- Nama: ...\n- Umur: ...\n- Penampilan: ...\n- Kepribadian: ...\n- Latar Belakang: ...\n- Motivasi: ...\n- Kelebihan: ...\n- Kekurangan: ...\n\n2. [Nama Karakter Utama 2]\n- Nama: ...\n- Umur: ...\n- Penampilan: ...\n- Kepribadian: ...\n- Latar Belakang: ...\n- Motivasi: ...\n- Kelebihan: ...\n- Kekurangan: ..."
    }},
    {{
      "name": "Konflik & Dinamika Hubungan",
      "purpose": "Core narrative friction, internal/external conflicts, and relationship progression web.",
      "key_information": "Konflik Utama: ...\nInternal Karakter: ...\nEksternal & Antagonis: ...\nBagan Hubungan Antar Karakter: ..."
    }},
    {{
      "name": "Outline Episode Utama",
      "purpose": "Structured episode breakdown with hooks, dramatic turning points, and cliffhangers.",
      "key_information": "Jumlah Episode: {duration}\n\nEpisode 1:\n- Judul & Premis:\n- Alur Adegan Utama:\n- Cliffhanger:\n\nEpisode 2:\n- Judul & Premis:\n- Alur Adegan Utama:\n- Cliffhanger:"
    }}
  ]
}}

RULES:
- Rich, highly engaging, professional C-Drama pre-production dossier format matching the user reference.
- Do not output markdown codeblocks outside JSON.
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
# GENERATE SCRIPT (PEMISAHAN TOTAL C-DRAMA & KONTEN UMUM)
# ============================================================

def generate_script(topic, duration, audience, language, outline):
    normalized_outline = normalize_outline(outline)
    outline_json = json.dumps(normalized_outline, indent=2, ensure_ascii=False)
    is_dracin = "Rekap" in str(duration) or "Episode" in str(duration)

    if is_dracin:
        prompt = f"""
You are an elite C-Drama Master Screenwriter and Dialogue Director for C-Drama Engine Suite Pro.
Write a breathtaking, emotionally charged professional screenplay script based on the dossier and outline below.

DRACIN INFORMATION:
Drama Title: {topic}
Episode Scope: {duration}
Core Trope: {audience}
Script Language: {language}

OUTLINE & DOSSIER:
{outline_json}

SCRIPT REQUIREMENTS:
- Write vivid visual cinematography notes (e.g., [Visual Cinematik], lighting, camera angle, atmospheric tension).
- Write professional scene headers (e.g., INT. KANTOR - SIANG).
- Write gripping, emotional dialogue with subtext and character expressions.
- Structure it cleanly into immersive scenes.
"""
    else:
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