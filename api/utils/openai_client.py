"""
OpenAI Client Utility Module

This module provides utilities for interacting with OpenAI's API, including client initialization
and configuration management.
"""

import logging
from typing import Optional
import openai
from openai import AsyncOpenAI

from api.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def get_openai_client() -> Optional[AsyncOpenAI]:
    """
    Get an initialized OpenAI client instance.
    
    Returns:
        AsyncOpenAI client instance or None if initialization fails
    """
    try:
        # Get API key from settings
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            logger.error("OpenAI API key not found in settings")
            return None
            
        # Initialize client
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=settings.OPENAI_API_BASE_URL,
            timeout=settings.OPENAI_API_TIMEOUT,
            max_retries=settings.OPENAI_API_MAX_RETRIES
        )
        
        return client
    except Exception as e:
        logger.error(f"Error initializing OpenAI client: {str(e)}")
        return None

async def validate_openai_connection() -> bool:
    """
    Validate the OpenAI connection by making a test API call.
    
    Returns:
        bool: True if connection is valid, False otherwise
    """
    try:
        client = get_openai_client()
        if not client:
            return False
            
        # Make a test API call
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        
        return bool(response)
    except Exception as e:
        logger.error(f"Error validating OpenAI connection: {str(e)}")
        return False

async def get_available_models() -> list:
    """
    Get list of available OpenAI models.
    
    Returns:
        list: List of available model IDs
    """
    try:
        client = get_openai_client()
        if not client:
            return []
            
        # Get models
        response = await client.models.list()
        return [model.id for model in response.data]
    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
        return [] 