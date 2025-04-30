import aiohttp
import base64
from typing import Optional, List
from api.config.settings import get_settings

async def generate_text_internal(prompt: str, model: str = None) -> Optional[str]:
    """
    Generate text using the internal text generation API (centralized, replaces direct Hugging Face/OpenAI calls).
    Args:
        prompt: The text prompt to generate from.
        model: The model name to use (e.g., 'mistral', 'llama', 'pythia', etc.)
    Returns:
        Generated text if successful, None otherwise.
    """
    settings = get_settings()
    api_url = getattr(settings, "INTERNAL_TEXT_GEN_API_URL", None)
    username = getattr(settings, "INTERNAL_TEXT_GEN_API_USER", None)
    password = getattr(settings, "INTERNAL_TEXT_GEN_API_PASS", None)
    if not api_url or not username or not password:
        return None
    auth = base64.b64encode(f"{username}:{password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    model_name = model or getattr(settings, "INTERNAL_TEXT_GEN_MODEL", "internal-default")
    # Enforce allowed models
    if model_name not in settings.ALLOWED_TEXT_GEN_MODELS:
        raise ValueError(f"Model '{model_name}' is not an allowed text generation model. Allowed: {settings.ALLOWED_TEXT_GEN_MODELS}")
    payload = {"prompt": prompt, "model": model_name}
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("generated_text")
            else:
                return None

async def embed_text_internal(texts: List[str], model: str = "internal-embedding") -> Optional[List[List[float]]]:
    """
    Get embeddings for a list of texts using the internal embedding API.
    Args:
        texts: List of texts to embed.
        model: The embedding model name to use.
    Returns:
        List of embeddings (list of float lists) if successful, None otherwise.
    """
    settings = get_settings()
    api_url = getattr(settings, "INTERNAL_EMBEDDING_API_URL", None)
    username = getattr(settings, "INTERNAL_TEXT_GEN_API_USER", None)
    password = getattr(settings, "INTERNAL_TEXT_GEN_API_PASS", None)
    if not api_url or not username or not password:
        return None
    # Enforce allowed embedding models
    if model not in settings.ALLOWED_EMBEDDING_MODELS:
        raise ValueError(f"Model '{model}' is not an allowed embedding model. Allowed: {settings.ALLOWED_EMBEDDING_MODELS}")
    auth = base64.b64encode(f"{username}:{password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    payload = {"texts": texts, "model": model}
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("embeddings")
            else:
                return None

# Translation API is not exposed. Only embedding and text generation functions are available.
