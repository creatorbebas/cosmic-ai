from core.ai import ask_ai


def rewrite_section(
    section_name,
    section_content,
    style,
    language
):
    """
    Menulis ulang satu section script.

    AI hanya menerima section yang dipilih,
    bukan seluruh script.
    """

    prompt = f"""
You are an expert YouTube script editor.

Rewrite ONLY the selected section below.

SECTION:
{section_name}

ORIGINAL CONTENT:
{section_content}

REWRITE STYLE:
{style}

LANGUAGE:
{language}

Rules:
- Keep the original meaning and factual intent.
- Do not rewrite other sections.
- Do not add section headings.
- Do not add explanations.
- Do not add quotation marks around the result.
- Make the writing natural and engaging for YouTube.
- Improve clarity, flow, and audience retention.
- Return ONLY the rewritten section.
"""

    try:
        result = ask_ai(prompt)

        if not result:
            return None

        return result.strip()

    except Exception as error:
        print(f"Rewrite error: {error}")
        return None