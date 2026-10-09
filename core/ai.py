from dotenv import load_dotenv
from openai import OpenAI
import os


load_dotenv()

MODEL = "gpt-5-mini"

client = OpenAI(
    api_key=os.getenv("AI_API_KEY")
)


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


def ask_ai(
    prompt,
    web_search=False
):
    """
    Fungsi AI utama.

    Tetap mengembalikan string agar semua fitur lama
    tetap kompatibel.
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

        response = client.responses.create(
            **request
        )

        return response.output_text

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

        response = client.responses.create(
            model=MODEL,
            input=prompt,
            tools=[
                {
                    "type": "web_search"
                }
            ]
        )

        return {
            "text": response.output_text,
            "sources": _extract_web_sources(response)
        }

    except Exception as error:

        print(f"[AI WEB SEARCH ERROR] {error}")

        return None