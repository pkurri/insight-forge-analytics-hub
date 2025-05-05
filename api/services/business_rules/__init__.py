"""
Business Rules package for managing rule creation, validation, and execution.

This package provides a modular approach to business rules management,
separating concerns into different modules:
- core.py: Core BusinessRulesService class and main functionality
- generators.py: Rule generation logic (AI, Great Expectations, Pydantic)
- executors.py: Rule execution logic for different rule types
- validators.py: Rule validation logic
"""

from api.services.business_rules.core import BusinessRulesService

# Create singleton instance
business_rules_service = BusinessRulesService()

# Export the service instance as the main interface
__all__ = ['business_rules_service']
