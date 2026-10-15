import re


# ============================================================
# DAFTAR HEADER SECTION YANG DIKENALI
# ============================================================
# Mencakup alur konten umum (HOOK, INTRO, SEGMENT, TWIST, CLOSING)
# dan alur Dracin (CONFLICT BUILD-UP, THE CLIMAX / REVEAL, OUTRO / CTA).
# Header yang lebih panjang ditulis lebih dulu.

HEADER_NAMES = [
    r"THE\s+CLIMAX\s*/\s*REVEAL",
    r"CLIMAX\s*/\s*REVEAL",
    r"CONFLICT\s+BUILD[\s\-]*UP",
    r"OUTRO\s*/\s*CTA",
    r"CALL\s+TO\s+ACTION",
    r"INTRO(?:DUCTION)?",
    r"SEGMENT(?:\s*\d+)?",
    r"BODY(?:\s*\d+)?",
    r"POINT(?:\s*\d+)?",
    r"SECTION(?:\s*\d+)?",
    r"HOOK",
    r"PROBLEM",
    r"SOLUTION",
    r"TWIST",
    r"CTA",
    r"OUTRO",
    r"CLOSING",
    r"SUMMARY",
    r"CLIMAX",
]

# Satu header = satu baris penuh. Boleh diawali "1.", "#", "**", "[" dan
# diakhiri ":", "**", "]" atau keterangan waktu dalam kurung, misalnya "(0:00-0:30)".
HEADER_PATTERN = re.compile(
    r"^[ \t]*(?:\d+[.)][ \t]*)?[#*\[]*[ \t]*("
    + "|".join(HEADER_NAMES)
    + r")[ \t]*(?:\([^)\n]*\))?[ \t]*[\]*:\-]*[ \t]*$",
    re.IGNORECASE | re.MULTILINE
)


def normalize_section_name(name):
    """Menyeragamkan nama section: huruf besar dan satu spasi."""
    return re.sub(r"\s+", " ", str(name or "")).strip().upper()


def split_script(script_text):
    """
    Memecah teks skrip menjadi daftar dictionary section secara presisi.
    """
    if not script_text or not str(script_text).strip():
        return [{"name": "FULL SCRIPT", "content": ""}]

    script_text = str(script_text).replace("\r\n", "\n").strip()

    matches = list(HEADER_PATTERN.finditer(script_text))

    if not matches:
        # Fallback jika tidak ada header, pecah berdasarkan paragraf
        paragraphs = [p.strip() for p in script_text.split("\n\n") if p.strip()]
        if len(paragraphs) > 1:
            sections = []
            for i, p in enumerate(paragraphs):
                name = "HOOK" if i == 0 else ("CLOSING" if i == len(paragraphs) - 1 else f"SEGMENT {i}")
                sections.append({"name": name, "content": p})
            return sections

        return [{"name": "FULL SCRIPT", "content": script_text}]

    sections = []

    # Tangkap teks sebelum header pertama jika ada
    if matches[0].start() > 0:
        preface = script_text[:matches[0].start()].strip()
        if preface:
            sections.append({"name": "PREFACE", "content": preface})

    for i, match in enumerate(matches):
        sec_name = normalize_section_name(match.group(1))

        start_idx = match.end()
        end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(script_text)

        sec_content = script_text[start_idx:end_idx].strip()

        sections.append({
            "name": sec_name,
            "content": sec_content
        })

    return sections


def combine_sections(sections):
    """
    Menggabungkan kembali list of sections menjadi satu string script utuh.

    Format keluaran sama dengan script yang dibuat generator:
    NAMA SECTION, baris kosong, isi section.
    """
    combined = []
    for sec in sections:
        name = str(sec.get("name", "")).strip()
        content = str(sec.get("content", "")).strip()

        if name and name.upper() not in ("FULL SCRIPT", "PREFACE"):
            combined.append(f"{name}\n\n{content}")
        else:
            combined.append(content)

    return "\n\n".join(combined)