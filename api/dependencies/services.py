"""Service Dependencies Module

This module provides dependency injection functions for services used in the API.
"""

from fastapi import Depends
from typing import Annotated

from api.services.vector_service import vector_service
from api.services.business_rules import business_rules_service
from api.services.cache_service import cache_service

# Create singleton instances
_business_rules_service = BusinessRulesService()

async def get_vector_service():
    """
    Dependency for the vector service.
    """
    return vector_service

async def get_business_rules_service():
    """Dependency for the business rules service."""
    return business_rules_service

async def get_cache_service():
    """
    Dependency for the cache service.
    """
    return cache_service

# Type annotations for easier dependency injection
VectorService = Annotated[vector_service.__class__, Depends(get_vector_service)]
BusinessRulesService = Annotated[BusinessRulesService, Depends(get_business_rules_service)]
CacheService = Annotated[cache_service.__class__, Depends(get_cache_service)]
