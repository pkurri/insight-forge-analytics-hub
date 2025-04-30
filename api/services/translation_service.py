import aiohttp
import base64
from typing import Optional

from api.config.settings import get_settings

async def translate_text_internal(text: str, source_lang: str = "en", target_lang: str = "es") -> Optional[str]:
    """
    Translate text using internal API with basic authentication.
    Args:
        text: The text to translate.
        source_lang: Source language code (default 'en').
        target_lang: Target language code (default 'es').
    Returns:
        Translated text if successful, None otherwise.
    """
    settings = get_settings()
    api_url = settings.INTERNAL_TRANSLATION_API_URL
    username = settings.INTERNAL_TRANSLATION_API_USERNAME
    password = settings.INTERNAL_TRANSLATION_API_PASSWORD
    auth = base64.b64encode(f"{username}:{password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "source_lang": source_lang,
        "target_lang": target_lang
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("translated_text")
            else:
                return None
