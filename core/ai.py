"""
Lapisan akses AI (OpenAI Responses API) + utilitas parsing JSON.

Environment variable yang dipakai:
- AI_API_KEY      : API key OpenAI (wajib)
- AI_MODEL        : nama model (opsional, default gpt-5-mini)
- AI_TIMEOUT      : batas waktu satu panggilan AI dalam detik (opsional, default 90)
- AI_MAX_RETRIES  : jumlah retry otomatis jika koneksi gagal (opsional, default 1)
"""

import json
import os
import re

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv tidak wajib di production
    pass


MODEL = os.getenv("AI_MODEL", "gpt-5-mini")
AI_TIMEOUT = float(os.getenv("AI_TIMEOUT", "90"))
AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "1"))

_client = None


def _get_client():
    """
    Client dibuat saat pertama kali dipakai (bukan saat import),
    supaya halaman yang tidak memakai AI tetap jalan walaupun
    AI_API_KEY belum diatur.
    """

    global _client

    if _client is None:
        from openai import OpenAI

        api_key = os.getenv("AI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "AI_API_KEY belum diatur di environment variable."
            )

        _client = OpenAI(
            api_key=api_key,
            timeout=AI_TIMEOUT,
            max_retries=AI_MAX_RETRIES
        )

    return _client


# ============================================================
# PARSING JSON DARI JAWABAN AI
# ============================================================

def parse_json_response(response):
    """
    Mengubah jawaban AI menjadi dict/list Python.

    Tahan terhadap:
    - JSON murni
    - JSON di dalam code fence ```json ... ```
    - teks pembuka/penutup di sekitar JSON

    Return None jika tidak ada JSON yang valid.
    """

    if response is None:
        return None

    if isinstance(response, (dict, list)):
        return response

    text = str(response).strip()

    if not text:
        return None

    candidates = [text]

    fence = re.search(
        r"```(?:json)?\s*(.*?)```",
        text,
        re.DOTALL | re.IGNORECASE
    )

    if fence:
        candidates.append(fence.group(1).strip())

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end > start:
        candidates.append(text[start:end + 1])

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except (ValueError, TypeError):
            continue

    return None


# ============================================================
# SUMBER WEB SEARCH
# ============================================================

def _annotation_to_dict(annotation):
    """
    Mengubah annotation URL citation dari SDK OpenAI
    menjadi dictionary sederhana.
    """

    if isinstance(annotation, dict):
        return {
            "type": annotation.get("type"),
            "title": annotation.get("title", ""),
            "url": annotation.get("url", "")
        }

    return {
        "type": getattr(annotation, "type", None),
        "title": getattr(annotation, "title", ""),
        "url": getattr(annotation, "url", "")
    }


def _extract_web_sources(response):
    """
    Mengambil sumber aktual dari hasil Web Search.

    Sumber bisa muncul sebagai:
    1. URL citations pada output text
    2. sources pada web_search_call
    """

    sources = []
    seen_urls = set()

    def add_source(title="", url=""):
        if not url:
            return

        url = str(url).strip()

        if not url:
            return

        if url in seen_urls:
            return

        seen_urls.add(url)

        sources.append({
            "title": str(title or "").strip(),
            "url": url
        })

    output = getattr(response, "output", None) or []

    for item in output:

        # ---------------------------------------------------------
        # 1. URL citations pada output message
        # ---------------------------------------------------------

        content_list = getattr(item, "content", None) or []

        if isinstance(item, dict):
            content_list = item.get("content", []) or []

        for content in content_list:

            if isinstance(content, dict):
                annotations = content.get("annotations", []) or []
            else:
                annotations = getattr(content, "annotations", None) or []

            for annotation in annotations:

                annotation_data = _annotation_to_dict(annotation)

                if annotation_data.get("type") == "url_citation":
                    add_source(
                        annotation_data.get("title"),
                        annotation_data.get("url")
                    )

        # ---------------------------------------------------------
        # 2. Web search call sources
        # ---------------------------------------------------------

        item_type = (
            item.get("type")
            if isinstance(item, dict)
            else getattr(item, "type", None)
        )

        if item_type == "web_search_call":

            action = (
                item.get("action")
                if isinstance(item, dict)
                else getattr(item, "action", None)
            )

            if action:

                if isinstance(action, dict):
                    action_sources = action.get("sources", []) or []
                else:
                    action_sources = getattr(action, "sources", None) or []

                for source in action_sources:

                    if isinstance(source, dict):
                        add_source(
                            source.get("title", ""),
                            source.get("url", "")
                        )
                    else:
                        add_source(
                            getattr(source, "title", ""),
                            getattr(source, "url", "")
                        )

    return sources


# ============================================================
# PANGGILAN AI
# ============================================================

def ask_ai(
    prompt,
    web_search=False
):
    """
    Fungsi AI utama.

    Tetap mengembalikan string (atau None jika gagal)
    agar semua fitur lama tetap kompatibel.
    Detail error dicetak ke log server.
    """

    if not prompt:
        return None

    prompt = str(prompt).strip()

    if not prompt:
        return None

    try:

        request = {
            "model": MODEL,
            "input": prompt
        }

        if web_search:
            request["tools"] = [
                {
                    "type": "web_search"
                }
            ]

        response = _get_client().responses.create(
            **request
        )

        text = response.output_text

        if not text or not text.strip():
            print("[AI ERROR] AI mengembalikan jawaban kosong.")
            return None

        return text

    except Exception as error:

        print(f"[AI ERROR] {error}")

        return None


def ask_ai_with_web_search(prompt):
    """
    Backward-compatible Web Search function.

    Tetap hanya mengembalikan text.
    """

    return ask_ai(
        prompt,
        web_search=True
    )


def ask_ai_with_web_search_data(prompt):
    """
    Web Search dengan metadata sumber.

    Return:
    {
        "text": "...",
        "sources": [
            {
                "title": "...",
                "url": "..."
            }
        ]
    }
    """

    if not prompt:
        return None

    prompt = str(prompt).strip()

    if not prompt:
        return None

    try:

        response = _get_client().responses.create(
            model=MODEL,
            input=prompt,
            tools=[
                {
                    "type": "web_search"
                }
            ]
        )

        text = response.output_text

        if not text or not text.strip():
            print("[AI WEB SEARCH ERROR] AI mengembalikan jawaban kosong.")
            return None

        return {
            "text": text,
            "sources": _extract_web_sources(response)
        }

    except Exception as error:

        print(f"[AI WEB SEARCH ERROR] {error}")

        return None