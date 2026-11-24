import os
import requests


def get_voice_over_config():
    """Membaca konfigurasi endpoint voice cloning gratis/lokal dari environment."""
    endpoint_url = os.environ.get("VOICE_CLONE_ENDPOINT", "").strip()
    speaker_id = os.environ.get("VOICE_CLONE_SPEAKER", "default").strip()
    timeout_sec = int(os.environ.get("VOICE_CLONE_TIMEOUT", "120"))
    return {
        "endpoint_url": endpoint_url,
        "speaker_id": speaker_id,
        "timeout_sec": timeout_sec,
    }


def synthesize_voice_over(text, language="Indonesian"):
    """
    Mengirim teks narasi ke endpoint voice cloning lokal/open-source.
    Mengembalikan tuple: (audio_bytes_or_None, error_message_or_None).
    """
    clean_text = (text or "").strip()
    if not clean_text:
        return None, "Teks narasi/skrip masih kosong."

    cfg = get_voice_over_config()
    if not cfg["endpoint_url"]:
        return (
            None,
            "VOICE_CLONE_ENDPOINT belum diatur. Jalankan server voice cloning lokal/open-source lalu isi VOICE_CLONE_ENDPOINT di .env.",
        )

    payload = {
        "text": clean_text,
        "language": language or "Indonesian",
        "speaker": cfg["speaker_id"],
    }

    try:
        response = requests.post(
            cfg["endpoint_url"],
            json=payload,
            timeout=cfg["timeout_sec"],
        )
    except requests.RequestException as exc:
        return None, f"Gagal menghubungi server voice cloning: {exc}"

    if response.status_code != 200:
        detail = (response.text or "").strip()[:200]
        return (
            None,
            f"Server voice cloning mengembalikan status {response.status_code}: {detail}",
        )

    if not response.content:
        return None, "Server voice cloning mengembalikan audio kosong."

    return response.content, None