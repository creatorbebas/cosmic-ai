import re

# List nama section standar yang umum dipakai dalam skrip AI/konten
SECTION_KEYWORDS = [
    "HOOK", "INTRO", "INTRODUCTION", "PROBLEM", "SOLUTION", 
    "BODY", "POINT", "SECTION", "CALL TO ACTION", "CTA", 
    "OUTRO", "CONCLUSION", "SUMMARY"
]


def split_script(script_text):
    """
    Memecah teks skrip menjadi daftar dictionary section:
    [{ "name": "HOOK", "content": "..." }, { "name": "INTRO", "content": "..." }]
    """
    if not script_text or not script_text.strip():
        return [{"name": "FULL SCRIPT", "content": ""}]

    script_text = script_text.strip()

    # Pattern 1: Deteksi header seperti [HOOK], ### HOOK, **HOOK**, HOOK:
    pattern = r'(?i)(?:^|\n)(?:[#*\[\s]*)(HOOK|INTRO|INTRODUCTION|PROBLEM|SOLUTION|BODY(?:\s*\d+)?|POINT(?:\s*\d+)?|SECTION(?:\s*\d+)?|CALL TO ACTION|CTA|OUTRO|CONCLUSION|SUMMARY)(?:[\]*:\s]*)(?=\n|$)'

    matches = list(re.finditer(pattern, script_text))

    if not matches:
        # Jika tidak ada header standar, coba pecah berdasarkan baris kosong (paragraf)
        paragraphs = [p.strip() for p in script_text.split("\n\n") if p.strip()]
        if len(paragraphs) > 1:
            sections = []
            for i, p in enumerate(paragraphs):
                name = "HOOK" if i == 0 else ("CTA / OUTRO" if i == len(paragraphs) - 1 else f"SECTION {i}")
                sections.append({"name": name, "content": p})
            return sections
        
        # Jika benar-benar 1 blok teks utuh
        return [{"name": "FULL SCRIPT", "content": script_text}]

    sections = []
    
    # Tangkap teks sebelum header pertama jika ada
    if matches[0].start() > 0:
        preface = script_text[:matches[0].start()].strip()
        if preface:
            sections.append({"name": "INTRO / PREFACE", "content": preface})

    for i in range(len(matches)):
        match = matches[i]
        sec_name = match.group(1).upper()

        start_idx = match.end()
        end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(script_text)

        sec_content = script_text[start_idx:end_idx].strip()
        
        # Bersihkan sisa simbol pembatas di awal konten
        sec_content = re.sub(r'^[\]*:\s-]+', '', sec_content).strip()

        sections.append({
            "name": sec_name,
            "content": sec_content
        })

    return sections


def combine_sections(sections):
    """
    Menggabungkan kembali list of sections menjadi satu string script utuh.
    """
    combined = []
    for sec in sections:
        name = sec.get("name", "").strip()
        content = sec.get("content", "").strip()
        
        if name and name.upper() != "FULL SCRIPT":
            combined.append(f"[{name}]\n{content}")
        else:
            combined.append(content)

    return "\n\n".join(combined)