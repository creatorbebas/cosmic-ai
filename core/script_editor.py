import re

def split_script(script_text):
    """
    Memecah teks skrip menjadi daftar dictionary section secara presisi.
    """
    if not script_text or not script_text.strip():
        return [{"name": "FULL SCRIPT", "content": ""}]

    script_text = script_text.strip()

    # Pattern yang diperluas untuk mencakup seluruh variasi heading: HOOK, INTRODUCTION, SEGMENT 1-3, TWIST, CLOSING, OUTRO, dll.
    pattern = r'(?i)(?:^|\n)(?:[#*\[\s]*)(HOOK|INTRO(?:DUCTION)?|PROBLEM|SOLUTION|SEGMENT(?:\s*\d+)?|BODY(?:\s*\d+)?|POINT(?:\s*\d+)?|TWIST|SECTION(?:\s*\d+)?|CALL TO ACTION|CTA|OUTRO|CLOSING|SUMMARY)(?:[\]*:\s]*)(?=\n|$)'

    matches = list(re.finditer(pattern, script_text))

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