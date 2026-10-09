from core.ai import ask_ai
from core.content import generate_metadata

import json
import sys


# ============================================================
# OUTLINE GENERATOR
# ============================================================

def generate_outline(topic, duration, audience, language):

    prompt = f"""
You are an expert YouTube content strategist.

Create a detailed long-form YouTube video outline.

VIDEO INFORMATION

Topic:
{topic}

Target duration:
{duration} minutes

Target audience:
{audience}

Script language:
{language}


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
      "purpose": "",
      "key_information": "",
      "narrative_goal": "",
      "approximate_duration": ""
    }},
    {{
      "name": "INTRODUCTION",
      "purpose": "",
      "key_information": "",
      "narrative_goal": "",
      "approximate_duration": ""
    }},
    {{
      "name": "SEGMENT 1",
      "purpose": "",
      "key_information": "",
      "narrative_goal": "",
      "approximate_duration": ""
    }},
    {{
      "name": "SEGMENT 2",
      "purpose": "",
      "key_information": "",
      "narrative_goal": "",
      "approximate_duration": ""
    }},
    {{
      "name": "SEGMENT 3",
      "purpose": "",
      "key_information": "",
      "narrative_goal": "",
      "approximate_duration": ""
    }},
    {{
      "name": "TWIST",
      "purpose": "",
      "key_information": "",
      "narrative_goal": "",
      "approximate_duration": ""
    }},
    {{
      "name": "CLOSING",
      "purpose": "",
      "key_information": "",
      "narrative_goal": "",
      "approximate_duration": ""
    }}
  ]
}}

RULES:

- Use exactly 7 sections.
- The Hook must immediately create curiosity.
- Do not reveal the main conclusion in the Hook.
- Each section must introduce new information.
- Avoid repetition.
- Build curiosity progressively.
- The Twist should contain the most surprising information.
- The Closing should provide a satisfying conclusion.
- The total duration should approximately match the requested duration.
- Do not add explanations outside the JSON.
"""

    result = ask_ai(prompt)

    if result is None:
        return None

    try:
        return json.loads(result)

    except json.JSONDecodeError:
        print("\nAI menghasilkan format outline yang tidak valid.")
        print("Raw response:")
        print(result)
        return None


# ============================================================
# SCRIPT GENERATOR
# ============================================================

def generate_script(topic, duration, audience, language, outline):

    outline_json = json.dumps(
        outline,
        indent=2,
        ensure_ascii=False
    )

    prompt = f"""
You are an expert YouTube long-form scriptwriter.

Write a complete narration script based on the structured outline below.

VIDEO INFORMATION

Topic:
{topic}

Target duration:
{duration} minutes

Target audience:
{audience}

Script language:
{language}


STRUCTURED OUTLINE:

{outline_json}


SCRIPT REQUIREMENTS:

- Follow the outline in exactly the same order.
- Write natural spoken narration.
- Make the narration sound natural when read aloud.
- Start with a strong curiosity-driven Hook.
- Do not reveal everything immediately.
- Maintain curiosity throughout the video.
- Use smooth transitions.
- Every section must add meaningful new information.
- Avoid unnecessary repetition.
- Keep the pacing appropriate for the requested duration.
- Make the Twist meaningful and connected to earlier information.
- End with a satisfying Closing.
- Write ONLY the narration.

DO NOT INCLUDE:

- Visual directions.
- B-roll suggestions.
- Camera directions.
- Editing instructions.
- Production notes.
- Timestamps.
- Scene descriptions.
- Thumbnail ideas.
- SEO suggestions.
- Instructions for editors.
"""

    return ask_ai(prompt)


# ============================================================
# SAVE TEXT FILE
# ============================================================

def save_text(filename, content):

    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(content)

        print(f"File berhasil disimpan: {filename}")

    except Exception as error:
        print(f"Gagal menyimpan {filename}: {error}")


# ============================================================
# SAVE JSON FILE
# ============================================================

def save_json(filename, content):

    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(
                content,
                file,
                indent=2,
                ensure_ascii=False
            )

        print(f"File berhasil disimpan: {filename}")

    except Exception as error:
        print(f"Gagal menyimpan {filename}: {error}")


# ============================================================
# USER INPUT
# ============================================================

print("======================================")
print("        COSMIC AI SCRIPT GENERATOR")
print("======================================")
print()

topic = input("Masukkan topik video: ")
duration = input("Durasi video (menit): ")
audience = input("Target audience: ")
language = input("Bahasa script: ")


# ============================================================
# GENERATE OUTLINE
# ============================================================

print("\n[1/3] Sedang membuat outline...")

try:

    outline = generate_outline(
        topic,
        duration,
        audience,
        language
    )

except Exception as error:

    print("\nGagal membuat outline.")
    print("Detail:", error)
    sys.exit()


if outline is None:
    sys.exit()


print("\n======================================")
print("               OUTLINE")
print("======================================\n")

print(
    json.dumps(
        outline,
        indent=2,
        ensure_ascii=False
    )
)

save_json(
    "outline.json",
    outline
)


# ============================================================
# GENERATE SCRIPT
# ============================================================

print("\n[2/3] Sedang membuat full script...")

try:

    script = generate_script(
        topic,
        duration,
        audience,
        language,
        outline
    )

except Exception as error:

    print("\nGagal membuat script.")
    print("Detail:", error)
    sys.exit()


if script is None:
    sys.exit()


print("\n======================================")
print("             FULL SCRIPT")
print("======================================\n")

print(script)

save_text(
    "script.txt",
    script
)


# ============================================================
# GENERATE METADATA
# ============================================================

print("\n[3/3] Sedang membuat hooks, titles, dan description...")

try:

    metadata = generate_metadata(
        topic,
        script,
        outline,
        language
    )

except Exception as error:

    print("\nGagal membuat metadata.")
    print("Detail:", error)
    sys.exit()


if metadata is None:
    sys.exit()


# ============================================================
# DISPLAY HOOKS
# ============================================================

print("\n======================================")
print("                HOOKS")
print("======================================\n")

for number, hook in enumerate(metadata["hooks"], start=1):

    print(f"{number}. [{hook['type']}]")
    print(hook["text"])
    print()


# ============================================================
# DISPLAY TITLES
# ============================================================

print("\n======================================")
print("               TITLES")
print("======================================\n")

for number, title in enumerate(metadata["titles"], start=1):

    print(f"{number}. {title['title']}")
    print(f"   Angle: {title['angle']}")
    print()


# ============================================================
# DISPLAY DESCRIPTION
# ============================================================

print("\n======================================")
print("             DESCRIPTION")
print("======================================\n")

print(metadata["description"])
print()
print(metadata["call_to_action"])


# ============================================================
# SAVE METADATA
# ============================================================

save_json(
    "metadata.json",
    metadata
)


# ============================================================
# FINISHED
# ============================================================

print("\n======================================")
print("       COSMIC AI SELESAI")
print("======================================")

print()
print("File yang berhasil dibuat:")
print()
print("1. outline.json")
print("2. script.txt")
print("3. metadata.json")
print()
print("Total API call: 3")