import re


SCRIPT_SECTIONS = [
    "HOOK",
    "INTRO",
    "SEGMENT 1",
    "SEGMENT 2",
    "SEGMENT 3",
    "TWIST",
    "CLOSING"
]


def normalize_section_name(name):
    """
    Menyamakan berbagai variasi nama section
    menjadi nama standar yang digunakan editor.
    """

    name = re.sub(
        r"\s+",
        " ",
        name.strip().upper()
    )

    if name == "INTRODUCTION":
        return "INTRO"

    return name


def split_script(script):
    """
    Memecah script menjadi section.

    Mendukung format:

    HOOK
    HOOK:
    ## HOOK
    ### HOOK

    INTRO
    INTRO:
    INTRODUCTION
    INTRODUCTION:

    SEGMENT 1
    SEGMENT 1:
    SEGMENT 1 - ...

    TWIST
    TWIST:

    CLOSING
    CLOSING:
    """

    if not script or not script.strip():
        return []

    text = script.strip()

    pattern = (
        r"(?im)^\s*"
        r"(?:#{1,6}\s*)?"
        r"(HOOK|INTRO|INTRODUCTION|SEGMENT\s+1|SEGMENT\s+2|SEGMENT\s+3|TWIST|CLOSING)"
        r"(?:\s*[:\-—–].*)?"
        r"\s*$"
    )

    matches = list(
        re.finditer(
            pattern,
            text
        )
    )

    if not matches:
        return [
            {
                "name": "SCRIPT",
                "content": text
            }
        ]

    sections = []

    for index, match in enumerate(matches):

        name = normalize_section_name(
            match.group(1)
        )

        start = match.end()

        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(text)

        content = text[
            start:end
        ].strip()

        sections.append(
            {
                "name": name,
                "content": content
            }
        )

    return sections


def combine_sections(sections):
    """
    Menggabungkan semua section menjadi satu script.
    """

    if not sections:
        return ""

    parts = []

    for section in sections:

        name = section.get(
            "name",
            ""
        ).strip()

        content = section.get(
            "content",
            ""
        ).strip()

        if not name and not content:
            continue

        if name:
            parts.append(name)

        if content:
            parts.append(content)

    return "\n\n".join(parts)


def get_section(
    sections,
    section_name
):
    target = normalize_section_name(
        section_name
    )

    for section in sections:

        current_name = normalize_section_name(
            section.get(
                "name",
                ""
            )
        )

        if current_name == target:
            return section

    return None


def update_section(
    sections,
    section_name,
    new_content
):
    target = normalize_section_name(
        section_name
    )

    updated = []

    for section in sections:

        current_name = normalize_section_name(
            section.get(
                "name",
                ""
            )
        )

        if current_name == target:

            updated.append(
                {
                    "name": section["name"],
                    "content": new_content.strip()
                }
            )

        else:
            updated.append(
                section
            )

    return updated