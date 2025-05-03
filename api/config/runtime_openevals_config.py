import os
from enum import Enum
from typing import Dict, List, Optional, Any
from .openevals_config import ComponentType, EvaluationCategory, DEFAULT_CRITERIA, CATEGORY_THRESHOLDS

"""
Runtime OpenEvals Configuration

This module defines configuration settings for runtime OpenEvals code quality checking.
Runtime evaluation allows the application to evaluate and improve code quality while the application is running.
"""

# Define specific criteria for runtime evaluation
RUNTIME_CRITERIA = {
    ComponentType.UI.value: [
        {"name": "Performance", "description": "Evaluate if the component uses efficient algorithms, memoization, optimized rendering, and avoids unnecessary re-renders."},
        {"name": "Accessibility", "description": "Check if the component follows accessibility best practices such as semantic HTML, ARIA attributes, keyboard navigation, and screen reader support."},
        {"name": "Error Handling", "description": "Assess how well the component handles edge cases, errors, loading states, and empty states."},
        {"name": "State Management", "description": "Evaluate if the component follows proper state management patterns, avoids prop drilling, and uses context or other state management solutions appropriately."},
        {"name": "Component Structure", "description": "Assess if the component follows clean code principles, is properly modularized, and adheres to the single responsibility principle."},
    ],
    ComponentType.DASHBOARD.value: [
        {"name": "Data Visualization", "description": "Evaluate if the dashboard component uses appropriate chart types, has clear labels, and presents data in an understandable way."},
        {"name": "Interactivity", "description": "Check if the dashboard provides interactive features like filtering, sorting, and drill-down capabilities."},
        {"name": "Performance", "description": "Assess if the dashboard efficiently renders large datasets, uses pagination, virtualization, or other optimization techniques."},
        {"name": "Responsiveness", "description": "Evaluate if the dashboard adapts well to different screen sizes and device types."},
        {"name": "Error Handling", "description": "Check if the dashboard gracefully handles data loading errors, empty datasets, and other edge cases."},
    ],
    ComponentType.ANALYTICS.value: [
        {"name": "Data Accuracy", "description": "Evaluate if the analytics component correctly processes and displays data, with appropriate rounding, formatting, and units."},
        {"name": "Statistical Methods", "description": "Check if the component uses appropriate statistical methods for analysis, aggregation, and trend detection."},
        {"name": "Performance", "description": "Assess if the component efficiently handles large datasets and complex calculations."},
        {"name": "Interpretability", "description": "Evaluate if the analytics results are presented in a way that is easy to understand and interpret."},
        {"name": "Error Handling", "description": "Check if the component gracefully handles edge cases like missing data, outliers, and data quality issues."},
    ],
    ComponentType.API.value: [
        {"name": "Error Handling", "description": "Evaluate if the API endpoint properly handles and reports errors, validation failures, and edge cases."},
        {"name": "Performance", "description": "Check if the API is optimized for performance, uses caching appropriately, and avoids N+1 query problems."},
        {"name": "Security", "description": "Assess if the API follows security best practices like input validation, authentication, and authorization."},
        {"name": "Maintainability", "description": "Evaluate if the API code is well-organized, follows clean code principles, and is easy to maintain."},
        {"name": "Documentation", "description": "Check if the API is properly documented with clear parameter descriptions, return types, and examples."},
    ],
    ComponentType.AI.value: [
        {"name": "Model Integration", "description": "Evaluate if the AI component correctly integrates with AI models, with proper error handling and fallbacks."},
        {"name": "User Experience", "description": "Check if the AI component provides a good user experience, with appropriate loading states, feedback, and interactive elements."},
        {"name": "Performance", "description": "Assess if the component efficiently handles AI model queries and responses, with caching or batching where appropriate."},
        {"name": "Error Handling", "description": "Evaluate if the component gracefully handles API failures, timeouts, rate limits, and other possible AI-related errors."},
        {"name": "Contextual Awareness", "description": "Check if the AI component maintains and uses context appropriately in interactions."},
    ],
    # Default criteria for other component types
    "default": [
        {"name": "Code Quality", "description": "Evaluate the overall code quality, including organization, naming, and adherence to best practices."},
        {"name": "Performance", "description": "Check if the component is optimized for performance and avoids common performance pitfalls."},
        {"name": "Error Handling", "description": "Assess how well the component handles errors and edge cases."},
        {"name": "Maintainability", "description": "Evaluate if the code is well-organized, documented, and easy to maintain."},
        {"name": "Testing", "description": "Check if the component has appropriate unit tests, integration tests, or other testing mechanisms."},
    ],
}

# Runtime evaluation prompt templates
RUNTIME_EVALUATION_PROMPT = """
You are an expert code reviewer specialized in evaluating code quality during runtime.
You're given the following code for the component named '{component_name}' of type '{component_type}'.

CODE:
```{code_language}
{code}
```

Evaluate this code based on the following criteria:
{criteria_list}

For each criterion, provide:
1. A score from 0-100
2. Specific observations and issues found
3. Concrete suggestions for improvement

Finally, provide an overall score (0-100) and a summary of the main strengths and issues.
Format your response as a JSON object with the following structure:
{{
  "evaluations": [
    {{
      "criterion": "[Criterion Name]",
      "score": [0-100],
      "observations": "[Your observations]",
      "suggestions": "[Your suggestions]"
    }},
    // Additional criteria evaluations
  ],
  "overall_score": [0-100],
  "summary": "[Summary of evaluation]",
  "improvement_suggestions": [
    "[Specific improvement 1]",
    "[Specific improvement 2]",
    // Additional improvements
  ]
}}
"""

# Runtime improvement prompt template
RUNTIME_IMPROVEMENT_PROMPT = """
You are an expert code developer specialized in improving code quality. 
You're given the following code for a component named '{component_name}' of type '{component_type}'.

ORIGINAL CODE:
```{code_language}
{code}
```

The code has been evaluated and the following issues and improvement suggestions have been identified:
{suggestions}

Your task is to rewrite the code to address these issues while maintaining the component's functionality.
Make the improvements in a way that:
1. Maintains existing functionality and doesn't break any dependencies
2. Follows best practices for the language/framework being used
3. Is well-commented and maintainable
4. Addresses all the identified issues and suggestions

Provide the complete improved code (not just snippets) as a direct replacement for the original code.
"""

# Define thresholds for runtime evaluations
RUNTIME_THRESHOLDS = {
    "excellent": 90,   # Score >= 90 is considered excellent quality
    "good": 75,       # Score >= 75 is considered good quality
    "acceptable": 60, # Score >= 60 is considered acceptable quality
    "needs_improvement": 0  # Score < 60 needs improvement
}

# Runtime evaluation configuration
RUNTIME_CONFIG = {
    "enabled": True,  # Whether runtime evaluation is enabled
    "evaluation_frequency": {
        "on_mount": True,       # Evaluate when component mounts (client-side)
        "on_render": False,     # Evaluate on every render (might be expensive)
        "on_user_interaction": False,  # Evaluate after user interacts with component
        "on_api_request": True,  # Evaluate when API endpoints are called
    },
    "auto_improve": False,  # Whether to automatically apply improvements
    "suggestion_format": "inline",  # How to present suggestions: 'inline', 'modal', or 'console'
    "display_scores": True,  # Whether to display quality scores to developers
    "log_evaluations": True,  # Whether to log evaluations
    "evaluation_thresholds": RUNTIME_THRESHOLDS,
    "criteria": RUNTIME_CRITERIA,
}

# Runtime suggestions storage configuration
SUGGESTIONS_STORAGE = {
    "directory": os.path.join(os.getcwd(), "data", "openevals", "runtime"),
    "max_suggestions_per_component": 10,  # Maximum number of stored suggestions per component
    "retention_days": 30,  # How long to keep suggestions
    "backup_original_code": True,  # Whether to create backups before applying improvements
}

# UI component patterns to identify component types
UI_COMPONENT_PATTERNS = {
    ComponentType.DASHBOARD.value: [
        r"Dashboard",
        r"MetricCard",
        r"DashboardChart",
        r"KPI"
    ],
    ComponentType.ANALYTICS.value: [
        r"Analytics",
        r"Chart",
        r"Graph",
        r"Visualization",
        r"Metrics"
    ],
    ComponentType.PIPELINE.value: [
        r"Pipeline",
        r"DataFlow",
        r"Workflow",
        r"Processor"
    ],
    ComponentType.AI.value: [
        r"AI",
        r"Model",
        r"Machine Learning",
        r"Prediction",
        r"Intelligence"
    ],
}
