"""OpenEvals configuration for project-wide code evaluation and improvement.

This module defines evaluation criteria, thresholds, and rules for different parts of the codebase.
"""

import os
import logging
from enum import Enum
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComponentType(str, Enum):
    """Types of components that can be evaluated."""
    API_ENDPOINT = "api_endpoint"
    UI_COMPONENT = "ui_component"
    DATA_PROCESSOR = "data_processor"
    AUTH_SYSTEM = "auth_system"
    DATABASE = "database"
    UTILS = "utils"
    AI_MODEL = "ai_model"

class EvaluationCategory(str, Enum):
    """Categories for evaluation criteria."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    CODE_QUALITY = "code_quality"
    USER_EXPERIENCE = "user_experience"
    ACCESSIBILITY = "accessibility"
    RESPONSIVENESS = "responsiveness"
    DATA_QUALITY = "data_quality"
    ERROR_HANDLING = "error_handling"
    DOCUMENTATION = "documentation"

# Default evaluation criteria for each component type
DEFAULT_CRITERIA = {
    ComponentType.API_ENDPOINT: [
        EvaluationCategory.SECURITY,
        EvaluationCategory.PERFORMANCE,
        EvaluationCategory.ERROR_HANDLING,
        EvaluationCategory.DOCUMENTATION,
    ],
    ComponentType.UI_COMPONENT: [
        EvaluationCategory.USER_EXPERIENCE,
        EvaluationCategory.ACCESSIBILITY,
        EvaluationCategory.RESPONSIVENESS,
        EvaluationCategory.ERROR_HANDLING,
    ],
    ComponentType.DATA_PROCESSOR: [
        EvaluationCategory.PERFORMANCE,
        EvaluationCategory.DATA_QUALITY,
        EvaluationCategory.ERROR_HANDLING,
    ],
    ComponentType.AUTH_SYSTEM: [
        EvaluationCategory.SECURITY,
        EvaluationCategory.ERROR_HANDLING,
    ],
    ComponentType.DATABASE: [
        EvaluationCategory.SECURITY,
        EvaluationCategory.PERFORMANCE,
        EvaluationCategory.DATA_QUALITY,
    ],
    ComponentType.UTILS: [
        EvaluationCategory.CODE_QUALITY,
        EvaluationCategory.ERROR_HANDLING,
    ],
    ComponentType.AI_MODEL: [
        EvaluationCategory.PERFORMANCE,
        EvaluationCategory.DATA_QUALITY,
        EvaluationCategory.ERROR_HANDLING,
    ],
}

# Evaluation thresholds for each category
CATEGORY_THRESHOLDS = {
    EvaluationCategory.SECURITY: 95,  # Security has highest threshold
    EvaluationCategory.PERFORMANCE: 85,
    EvaluationCategory.CODE_QUALITY: 80,
    EvaluationCategory.USER_EXPERIENCE: 90,
    EvaluationCategory.ACCESSIBILITY: 85,
    EvaluationCategory.RESPONSIVENESS: 85,
    EvaluationCategory.DATA_QUALITY: 90,
    EvaluationCategory.ERROR_HANDLING: 90,
    EvaluationCategory.DOCUMENTATION: 80,
}

# File path patterns for component types
COMPONENT_FILE_PATTERNS = {
    ComponentType.API_ENDPOINT: ["api/routes/*.py", "api/endpoints/*.py"],
    ComponentType.UI_COMPONENT: ["src/components/**/*.tsx", "src/components/**/*.jsx"],
    ComponentType.DATA_PROCESSOR: ["api/services/dataset_*.py", "api/data/**/*.py"],
    ComponentType.AUTH_SYSTEM: ["api/auth/*.py", "src/auth/**/*.ts"],
    ComponentType.DATABASE: ["api/db/*.py", "api/models/*.py"],
    ComponentType.UTILS: ["api/utils/*.py", "src/utils/*.ts"],
    ComponentType.AI_MODEL: ["api/services/ai_*.py", "api/services/*_model.py"],
}

class OpenEvalsConfig:
    """Configuration for OpenEvals project-wide evaluation."""
    
    def __init__(self):
        """Initialize with default configuration."""
        self.criteria = DEFAULT_CRITERIA.copy()
        self.thresholds = CATEGORY_THRESHOLDS.copy()
        self.file_patterns = COMPONENT_FILE_PATTERNS.copy()
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.evaluation_log_path = os.path.join(self.project_root, "logs", "openevals")
        os.makedirs(self.evaluation_log_path, exist_ok=True)
    
    def get_component_criteria(self, component_type: ComponentType) -> List[EvaluationCategory]:
        """Get evaluation criteria for a component type."""
        return self.criteria.get(component_type, [])
    
    def get_category_threshold(self, category: EvaluationCategory) -> int:
        """Get evaluation threshold for a category."""
        return self.thresholds.get(category, 80)  # Default 80% threshold
    
    def get_file_patterns(self, component_type: ComponentType) -> List[str]:
        """Get file patterns for a component type."""
        return self.file_patterns.get(component_type, [])
    
    def get_all_component_types(self) -> List[ComponentType]:
        """Get all component types."""
        return list(ComponentType)
    
    def get_all_evaluation_categories(self) -> List[EvaluationCategory]:
        """Get all evaluation categories."""
        return list(EvaluationCategory)
    
    def customize_criteria(self, component_type: ComponentType, categories: List[EvaluationCategory]) -> None:
        """Customize evaluation criteria for a component type."""
        self.criteria[component_type] = categories
        logger.info(f"Customized criteria for {component_type}: {categories}")
    
    def customize_threshold(self, category: EvaluationCategory, threshold: int) -> None:
        """Customize evaluation threshold for a category."""
        if 0 <= threshold <= 100:
            self.thresholds[category] = threshold
            logger.info(f"Customized threshold for {category}: {threshold}")
        else:
            logger.error(f"Invalid threshold value {threshold}. Must be between 0 and 100.")

# Create singleton instance
openevals_config = OpenEvalsConfig()
