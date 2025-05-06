"""
Internal AI Service Module

This module provides internal AI services for text generation and processing.
"""

import logging
from typing import Dict, Any, Optional, List
import json
import re

from api.utils.openai_client import get_openai_client
from api.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

async def generate_text_internal(
    prompt: str,
    model: str = "Mistral-3.2-instruct",
    max_tokens: int = 1000,
    temperature: float = 0.7,
    stop: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate text using internal AI models.
    
    Args:
        prompt: The prompt to generate text from
        model: The model to use for generation
        max_tokens: Maximum number of tokens to generate
        temperature: Sampling temperature
        stop: Optional list of stop sequences
        
    Returns:
        Dict containing generated text and metadata
    """
    try:
        # Validate model
        if model not in settings.ALLOWED_TEXT_GEN_MODELS:
            logger.warning(f"Model {model} not in allowed list, using default")
            model = settings.ALLOWED_TEXT_GEN_MODELS[0]
            
        # Get OpenAI client
        client = get_openai_client()
        if not client:
            return {
                "success": False,
                "error": "OpenAI client not available"
            }
            
        # Generate text
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop
        )
        
        # Extract generated text
        generated_text = response.choices[0].message.content
        
        # Try to parse as JSON if it looks like JSON
        if generated_text.strip().startswith("{") or generated_text.strip().startswith("["):
            try:
                parsed = json.loads(generated_text)
                return {
                    "success": True,
                    "text": generated_text,
                    "parsed": parsed,
                    "model": model,
                    "usage": response.usage._asdict()
                }
            except json.JSONDecodeError:
                pass
                
        return {
            "success": True,
            "text": generated_text,
            "model": model,
            "usage": response.usage._asdict()
        }
    except Exception as e:
        logger.error(f"Error generating text: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def generate_structured_text(
    prompt: str,
    structure: Dict[str, Any],
    model: str = "Mistral-3.2-instruct",
    max_tokens: int = 1000,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Generate structured text following a specific format.
    
    Args:
        prompt: The prompt to generate text from
        structure: Dictionary describing the expected structure
        model: The model to use for generation
        max_tokens: Maximum number of tokens to generate
        temperature: Sampling temperature
        
    Returns:
        Dict containing generated structured text and metadata
    """
    try:
        # Add structure guidance to prompt
        structure_guidance = f"""
        Generate a response following this structure:
        {json.dumps(structure, indent=2)}
        
        Ensure the response matches the structure exactly.
        """
        
        full_prompt = f"{prompt}\n\n{structure_guidance}"
        
        # Generate text
        result = await generate_text_internal(
            full_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        if not result["success"]:
            return result
            
        # Try to parse as JSON
        try:
            parsed = json.loads(result["text"])
            return {
                "success": True,
                "text": result["text"],
                "parsed": parsed,
                "model": model,
                "usage": result["usage"]
            }
        except json.JSONDecodeError:
            # Try to extract JSON from text
            json_pattern = r'\{[\s\S]*?\}|\[[\s\S]*?\]'
            matches = re.finditer(json_pattern, result["text"])
            
            for match in matches:
                try:
                    parsed = json.loads(match.group(0))
                    return {
                        "success": True,
                        "text": result["text"],
                        "parsed": parsed,
                        "model": model,
                        "usage": result["usage"]
                    }
                except json.JSONDecodeError:
                    continue
                    
            return {
                "success": False,
                "error": "Could not parse generated text as structured data",
                "text": result["text"]
            }
    except Exception as e:
        logger.error(f"Error generating structured text: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def validate_generated_text(
    text: str,
    validation_rules: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate generated text against rules.
    
    Args:
        text: The text to validate
        validation_rules: Dictionary of validation rules
        
    Returns:
        Dict containing validation results
    """
    try:
        # Try to parse as JSON
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Text is not valid JSON"
            }
            
        # Validate against rules
        validation_results = []
        for rule_name, rule in validation_rules.items():
            try:
                # Apply validation rule
                if rule["type"] == "required_field":
                    if rule["field"] not in parsed:
                        validation_results.append({
                            "rule": rule_name,
                            "passed": False,
                            "error": f"Required field {rule['field']} missing"
                        })
                    else:
                        validation_results.append({
                            "rule": rule_name,
                            "passed": True
                        })
                elif rule["type"] == "field_type":
                    if rule["field"] not in parsed:
                        validation_results.append({
                            "rule": rule_name,
                            "passed": False,
                            "error": f"Field {rule['field']} missing"
                        })
                    elif not isinstance(parsed[rule["field"]], eval(rule["type"])):
                        validation_results.append({
                            "rule": rule_name,
                            "passed": False,
                            "error": f"Field {rule['field']} has wrong type"
                        })
                    else:
                        validation_results.append({
                            "rule": rule_name,
                            "passed": True
                        })
            except Exception as e:
                validation_results.append({
                    "rule": rule_name,
                    "passed": False,
                    "error": str(e)
                })
                
        # Check if all rules passed
        all_passed = all(r["passed"] for r in validation_results)
        
        return {
            "success": True,
            "valid": all_passed,
            "results": validation_results
        }
    except Exception as e:
        logger.error(f"Error validating generated text: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

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
