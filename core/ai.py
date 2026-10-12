from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

MODEL = "gpt-5-mini"

client = OpenAI(
    api_key=os.getenv("AI_API_KEY")
)


def _annotation_to_dict(annotation):
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
    sources = []
    seen_urls = set()

    def add_source(title="", url=""):
        if not url:
            return
        url = str(url).strip()
        if not url or url in seen_urls:
            return
        seen_urls.add(url)
        sources.append({
            "title": str(title or "").strip(),
            "url": url
        })

    output = getattr(response, "output", None) or []
    for item in output:
        content_list = getattr(item, "content", None) or []
        if isinstance(item, dict):
            content_list = item.get("content", []) or []

        for content in content_list:
            annotations = content.get("annotations", []) if isinstance(content, dict) else getattr(content, "annotations", None) or []
            for annotation in annotations:
                annotation_data = _annotation_to_dict(annotation)
                if annotation_data.get("type") == "url_citation":
                    add_source(annotation_data.get("title"), annotation_data.get("url"))

        item_type = item.get("type") if isinstance(item, dict) else getattr(item, "type", None)
        if item_type == "web_search_call":
            action = item.get("action") if isinstance(item, dict) else getattr(item, "action", None)
            if action:
                action_sources = action.get("sources", []) if isinstance(action, dict) else getattr(action, "sources", None) or []
                for source in action_sources:
                    if isinstance(source, dict):
                        add_source(source.get("title", ""), source.get("url", ""))
                    else:
                        add_source(getattr(source, "title", ""), getattr(source, "url", ""))

    return sources


def ask_ai(prompt, web_search=False):
    if not prompt or not str(prompt).strip():
        return None

    try:
        request = {
            "model": MODEL,
            "input": str(prompt).strip()
        }

        if web_search:
            request["tools"] = [{"type": "web_search"}]

        response = client.responses.create(**request)
        return response.output_text

    except Exception as error:
        print(f"[AI ERROR] {error}")
        return None


def ask_ai_with_web_search(prompt):
    return ask_ai(prompt, web_search=True)


def ask_ai_with_web_search_data(prompt):
    if not prompt or not str(prompt).strip():
        return None

    try:
        response = client.responses.create(
            model=MODEL,
            input=str(prompt).strip(),
            tools=[{"type": "web_search"}]
        )

        return {
            "text": response.output_text,
            "sources": _extract_web_sources(response)
        }

    except Exception as error:
        print(f"[AI WEB SEARCH ERROR] {error}")
        return None