"""Lazy IBM Watson Speech-to-Text integration."""
from __future__ import annotations

from config import IBM_STT_API_KEY, IBM_STT_MODEL, IBM_STT_URL


def transcribe(audio: bytes, content_type: str = "audio/webm") -> str:
    """Transcribe audio bytes with IBM Watson Speech-to-Text."""
    if not IBM_STT_API_KEY:
        raise RuntimeError("IBM_STT_API_KEY must be set in .env")

    from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
    from ibm_watson import SpeechToTextV1

    service = SpeechToTextV1(authenticator=IAMAuthenticator(IBM_STT_API_KEY))
    if IBM_STT_URL:
        service.set_service_url(IBM_STT_URL)

    result = service.recognize(
        audio=audio,
        content_type=content_type or "audio/webm",
        model=IBM_STT_MODEL,
    ).get_result()
    alternatives = [
        alternative.get("transcript", "")
        for item in result.get("results", [])
        for alternative in item.get("alternatives", [])
    ]
    return " ".join(text.strip() for text in alternatives if text.strip()).strip()