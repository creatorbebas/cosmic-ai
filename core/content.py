import json
import re

from core.ai import ask_ai, parse_json_response


# ============================================================
# PENGATURAN PANJANG SCRIPT
# ============================================================
# Kecepatan bicara narasi (kata per detik). Dipakai untuk mengubah
# durasi video menjadi target jumlah kata.
WORDS_PER_SECOND = 2.4

# Target jumlah kata untuk mode Dracin, berdasarkan jumlah episode
# yang direkap: {jumlah_episode: (kata_min, kata_max)}.
# Ubah angka di sini jika hasil dirasa terlalu panjang / pendek.
DRACIN_WORD_TARGETS = {
    10: (700, 900),
    20: (1000, 1300),
    30: (1300, 1600),
    50: (1600, 2000),
}


# ============================================================
# STRUKTUR SECTION OUTLINE
# ============================================================
# weight = porsi durasi section terhadap total durasi video.

DRACIN_SECTIONS = [
    {
        "name": "HOOK",
        "purpose": "Shocking opening scene or dramatic conflict preview to hook viewers instantly.",
        "key_information": "Most dramatic emotional peak from the episodes.",
        "narrative_goal": "Force the audience to stay.",
        "weight": 0.07,
    },
    {
        "name": "INTRODUCTION",
        "purpose": "Introduce main characters, status, and initial humiliation or premise.",
        "key_information": "Background setup and character dynamics.",
        "narrative_goal": "Establish the stakes clearly.",
        "weight": 0.13,
    },
    {
        "name": "CONFLICT BUILD-UP",
        "purpose": "Escalation of conflict, toxic antagonists, or hidden secrets pressure.",
        "key_information": "Key plot points leading to tension.",
        "narrative_goal": "Build anticipation for the reveal.",
        "weight": 0.30,
    },
    {
        "name": "THE CLIMAX / REVEAL",
        "purpose": "The core trope execution (e.g., identity revealed, revenge served, or contract twist).",
        "key_information": "Shocking turning point and emotional satisfaction.",
        "narrative_goal": "Deliver maximum emotional payoff.",
        "weight": 0.35,
    },
    {
        "name": "OUTRO / CTA",
        "purpose": "Cliffhanger ending or question for viewers, teasing the next part.",
        "key_information": "Call to action and engagement hook.",
        "narrative_goal": "Drive comments and shares.",
        "weight": 0.15,
    },
]

GENERAL_SECTIONS = [
    {
        "name": "HOOK",
        "purpose": "Grab attention immediately with curiosity.",
        "key_information": "Key facts or hooks to tease.",
        "narrative_goal": "Make viewers want to keep watching.",
        "weight": 0.08,
    },
    {
        "name": "INTRODUCTION",
        "purpose": "Define the topic and scope.",
        "key_information": "Background and thesis statement.",
        "narrative_goal": "Set up clear expectations.",
        "weight": 0.12,
    },
    {
        "name": "SEGMENT 1",
        "purpose": "First main subtopic.",
        "key_information": "Detailed explanations and facts.",
        "narrative_goal": "Build foundation.",
        "weight": 0.32,
    },
    {
        "name": "SEGMENT 2",
        "purpose": "Second main subtopic or deep dive.",
        "key_information": "Detailed explanations and evidence.",
        "narrative_goal": "Deepen the story.",
        "weight": 0.32,
    },
    {
        "name": "CLOSING",
        "purpose": "Summarize and conclude.",
        "key_information": "Final conclusions and call to action.",
        "narrative_goal": "Leave a lasting impression.",
        "weight": 0.16,
    },
]


# ============================================================
# HELPER: MODE & DURASI
# ============================================================

def is_dracin_mode(duration):
    """Mode Dracin ditandai dengan durasi berformat 'Rekap N Episode'."""
    text = str(duration or "")
    return "Rekap" in text or "Episode" in text


def _parse_minutes(text):
    """Mengubah teks durasi umum (mis. 'Medium (3-5 min)') menjadi menit."""

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)\s*(?:min|menit|m\b)",
        text
    )
    if match:
        return (float(match.group(1)) + float(match.group(2))) / 2

    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:min|menit)", text)
    if match:
        return float(match.group(1))

    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:s|sec|detik)\b", text)
    if match:
        return float(match.group(1)) / 60

    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*", text)
    if match:
        return float(match.group(1))

    return 5.0


def target_words_for(duration):
    """
    Return (kata_min, kata_max, total_detik) untuk durasi/format yang dipilih.
    """

    text = str(duration or "").lower()

    if is_dracin_mode(duration):
        match = re.search(r"(\d+)", text)
        episodes = int(match.group(1)) if match else 20
        key = min(DRACIN_WORD_TARGETS, key=lambda k: abs(k - episodes))
        low, high = DRACIN_WORD_TARGETS[key]
    else:
        words = _parse_minutes(text) * 60 * WORDS_PER_SECOND
        low, high = int(words * 0.88), int(words * 1.12)

    seconds = int(((low + high) / 2) / WORDS_PER_SECOND)

    return low, high, seconds


def _format_seconds(seconds):
    seconds = max(1, int(round(seconds)))
    return f"{seconds // 60}:{seconds % 60:02d}"


def _outline_example(topic, duration, audience, language, sections, total_seconds):
    """Membuat contoh struktur JSON outline lengkap dengan durasi per section."""

    example = {
        "topic": topic,
        "duration_minutes": duration,
        "target_audience": audience,
        "language": language,
        "sections": [
            {
                "name": section["name"],
                "purpose": section["purpose"],
                "key_information": section["key_information"],
                "key_points": [section["key_information"]],
                "narrative_goal": section["narrative_goal"],
                "approximate_duration": _format_seconds(total_seconds * section["weight"]),
            }
            for section in sections
        ],
    }

    return json.dumps(example, ensure_ascii=False, indent=2)


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

    sections = [
        section for section in (outline.get("sections") or [])
        if isinstance(section, dict)
    ]
    outline["sections"] = sections

    for section in sections:
        key_points = section.get("key_points")
        key_info = section.get("key_information")

        if key_points and isinstance(key_points, list) and not key_info:
            section["key_information"] = " ".join(str(point) for point in key_points)
        elif key_info and not key_points:
            section["key_points"] = [key_info]

        if "purpose" not in section:
            section["purpose"] = ""
        if "narrative_goal" not in section:
            section["narrative_goal"] = ""
        if "approximate_duration" not in section:
            section["approximate_duration"] = ""

    return outline


def _outline_section_names(outline):
    names = []

    if isinstance(outline, dict):
        for section in outline.get("sections") or []:
            if isinstance(section, dict) and section.get("name"):
                names.append(str(section["name"]).strip().upper())

    return names


# ============================================================
# GENERATE OUTLINE (MENDUKUNG DRACIN & KONTEN UMUM)
# ============================================================

def generate_outline(topic, duration, audience, language):
    dracin = is_dracin_mode(duration)
    sections = DRACIN_SECTIONS if dracin else GENERAL_SECTIONS
    low, high, total_seconds = target_words_for(duration)

    example = _outline_example(
        topic, duration, audience, language, sections, total_seconds
    )

    if dracin:
        prompt = f"""
You are an expert Chinese Drama (Dracin) content strategist and viral recap writer.

Create a detailed video outline for a Chinese Drama recap.

DRACIN INFORMATION:
Drama Title: {topic}
Episode Scope: {duration}
Core Trope / Focus Scene: {audience}
Script Language: {language}

Return ONLY valid JSON.
Use exactly this structure:

{example}

RULES:
- Exactly {len(sections)} structural sections tailored for high-engagement Dracin recap.
- Keep the section names exactly as shown in the structure.
- The approximate_duration values must add up to about {_format_seconds(total_seconds)} in total.
- Write purpose, key_information, key_points and narrative_goal specifically for this drama and trope, not as generic text.
- Do not output markdown codeblocks outside JSON.
"""
    else:
        prompt = f"""
You are an expert YouTube content strategist.

Create a detailed YouTube video outline.

VIDEO INFORMATION
Topic: {topic}
Target duration: {duration}
Target audience: {audience}
Script language: {language}

Return ONLY valid JSON.
Use exactly this structure:

{example}

RULES:
- Keep the section names exactly as shown in the structure.
- The approximate_duration values must add up to about {_format_seconds(total_seconds)} in total.
- Write purpose, key_information, key_points and narrative_goal specifically for this topic, not as generic text.
- Avoid repetition and build progressive curiosity.
- Do not output markdown codeblocks outside JSON.
"""

    result = ask_ai(prompt)
    data = parse_json_response(result)

    if (
        not isinstance(data, dict)
        or not isinstance(data.get("sections"), list)
        or not data["sections"]
    ):
        print("[OUTLINE] Jawaban AI bukan outline yang valid.")
        return None

    return normalize_outline(data)


def regenerate_outline(topic, duration, audience, language):
    return generate_outline(topic, duration, audience, language)


# ============================================================
# GENERATE SCRIPT (MENDUKUNG DRACIN & KONTEN UMUM)
# ============================================================

def generate_script(topic, duration, audience, language, outline):
    normalized_outline = normalize_outline(outline)
    outline_json = json.dumps(normalized_outline, indent=2, ensure_ascii=False)
    dracin = is_dracin_mode(duration)

    low, high, _ = target_words_for(duration)
    section_names = _outline_section_names(normalized_outline)

    header_rule = ""
    if section_names:
        header_rule = (
            "- Use EXACTLY these section headers, in this order: "
            + ", ".join(section_names)
            + ".\n"
            "- Put each header alone on its own line in capital letters, "
            "followed by a blank line and then the narration. "
            "Do not use markdown symbols (#, *, [ ]) in the headers.\n"
        )

    if dracin:
        prompt = f"""
You are an expert Chinese Drama (Dracin) recap scriptwriter.

Write a gripping, highly engaging, and emotional spoken narration script based on the structured outline below.

DRACIN INFORMATION:
Drama Title: {topic}
Episode Scope: {duration}
Core Trope: {audience}
Script Language: {language}

STRUCTURED OUTLINE:
{outline_json}

SCRIPT REQUIREMENTS:
- Write natural, dramatic, and compelling spoken narration optimized for TikTok, Reels, or YouTube recap videos.
- Avoid camera directions, visual cues, or technical production notes.
- Total length: between {low} and {high} words across all sections.
{header_rule}"""
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
- Total length: between {low} and {high} words across all sections.
- Only state well-established facts as fact. If something is uncertain, disputed, or speculative, say so clearly instead of presenting it as certain.
{header_rule}"""

    result = ask_ai(prompt)

    if not result or not result.strip():
        return None

    return result.strip()


def regenerate_script(topic, duration, audience, language, outline):
    return generate_script(topic, duration, audience, language, outline)


# ============================================================
# GENERATE METADATA
# ============================================================

METADATA_EXAMPLE = json.dumps(
    {
        "hooks": [
            {"type": "curiosity", "text": "Hook text..."},
            {"type": "question", "text": "Hook text..."},
            {"type": "surprising_fact", "text": "Hook text..."},
            {"type": "story", "text": "Hook text..."},
            {"type": "mystery", "text": "Hook text..."},
        ],
        "titles": [
            {"title": "Title 1", "text": "Title 1", "angle": "Angle description 1"},
            {"title": "Title 2", "text": "Title 2", "angle": "Angle description 2"},
        ],
        "description": "Comprehensive video description...",
        "call_to_action": "Subscribe for more...",
    },
    ensure_ascii=False,
    indent=2,
)


def normalize_metadata(data):
    """Merapikan metadata dari AI. Return None jika isinya tidak bisa dipakai."""

    if not isinstance(data, dict):
        return None

    hooks = []
    for hook in data.get("hooks") or []:
        if isinstance(hook, dict):
            text = str(hook.get("text", "")).strip()
            if text:
                hooks.append({
                    "type": str(hook.get("type", "")).strip() or "hook",
                    "text": text,
                })
        elif isinstance(hook, str) and hook.strip():
            hooks.append({"type": "hook", "text": hook.strip()})

    titles = []
    for item in data.get("titles") or []:
        if isinstance(item, dict):
            title = str(item.get("title") or item.get("text") or "").strip()
            if title:
                titles.append({
                    "title": title,
                    "text": title,
                    "angle": str(item.get("angle", "")).strip(),
                })
        elif isinstance(item, str) and item.strip():
            titles.append({"title": item.strip(), "text": item.strip(), "angle": ""})

    description = str(data.get("description") or "").strip()
    call_to_action = str(data.get("call_to_action") or "").strip()

    if not hooks and not titles and not description:
        return None

    return {
        "hooks": hooks,
        "titles": titles,
        "description": description,
        "call_to_action": call_to_action,
    }


def generate_metadata(topic, script, outline, language, duration=None, audience=None):
    script_text = (script or "").strip()
    if len(script_text) > 6000:
        script_text = script_text[:6000] + "..."

    outline_lines = []
    if isinstance(outline, dict):
        for section in outline.get("sections") or []:
            if isinstance(section, dict) and section.get("name"):
                purpose = str(section.get("purpose") or "").strip()
                outline_lines.append(f"- {section['name']}: {purpose}")
    outline_summary = "\n".join(outline_lines) or "(not available)"

    format_line = ""
    if duration:
        format_line = f"Video format: {duration}"
        if is_dracin_mode(duration):
            format_line += " (Chinese drama recap for TikTok / YouTube / Reels)"
    if audience:
        format_line += f"\nTarget audience / focus: {audience}"

    prompt = f"""
You are a YouTube SEO and social media metadata expert.

Generate engaging hooks, clickable titles, and a video description for the content below.
Base everything on the actual script, do not invent facts that are not in it.

Topic/Drama: {topic}
Language: {language}
{format_line}

OUTLINE:
{outline_summary}

SCRIPT:
{script_text or "(not available)"}

Return ONLY valid JSON matching this structure:

{METADATA_EXAMPLE}

RULES:
- Provide exactly 5 hooks, one for each type shown (curiosity, question, surprising_fact, story, mystery).
- Provide 10 different clickable titles, each with a short angle description.
- The description should be ready to paste into YouTube and end with 3-5 relevant hashtags.
- Write all text in {language}.
- Do not output markdown codeblocks outside JSON.
"""

    result = ask_ai(prompt)
    data = parse_json_response(result)

    return normalize_metadata(data)