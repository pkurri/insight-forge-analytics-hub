"""
Repository module initialization.
"""

from api.repositories.business_rules_repository import BusinessRulesRepository

# Create singleton instances
business_rules_repository = BusinessRulesRepository()
