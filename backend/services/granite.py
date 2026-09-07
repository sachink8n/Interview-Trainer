"""
IBM Granite via watsonx.ai — thin wrapper around ibm-watsonx-ai SDK.
Raises RuntimeError if credentials are missing.
"""
from __future__ import annotations

from config import WATSONX_API_KEY, WATSONX_PROJECT_ID, WATSONX_URL, GRANITE_MODEL_ID


def _get_model():
    """Lazily initialise and return the watsonx Model instance."""
    if not WATSONX_API_KEY or not WATSONX_PROJECT_ID:
        raise RuntimeError(
            "WATSONX_API_KEY and WATSONX_PROJECT_ID must be set in .env"
        )

    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference

    credentials = Credentials(url=WATSONX_URL, api_key=WATSONX_API_KEY)
    model = ModelInference(
        model_id=GRANITE_MODEL_ID,
        credentials=credentials,
        project_id=WATSONX_PROJECT_ID,
        params={
            "max_new_tokens": 1024,
            "temperature": 0.7,
            "repetition_penalty": 1.1,
        },
    )
    return model


def generate(prompt: str) -> str:
    """
    Send *prompt* to Granite and return the generated text string.
    Uses the chat/messages API when supported, falls back to generate.
    """
    model = _get_model()

    # Try chat interface first (Granite instruct models)
    try:
        messages = [{"role": "user", "content": prompt}]
        response = model.chat(messages=messages)
        # response is a dict with choices list
        return response["choices"][0]["message"]["content"].strip()
    except Exception:
        pass

    # Fallback: plain generate
    response = model.generate_text(prompt=prompt)
    if isinstance(response, str):
        return response.strip()
    # SDK returns dict for some versions
    return response["results"][0]["generated_text"].strip()
