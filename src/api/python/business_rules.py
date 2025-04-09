
"""
Business Rules Module

This module provides functionality for defining, managing, and enforcing
business rules on data. It supports both manual rule definition and
AI-powered rule generation.

In a production environment, this would be deployed as an API endpoint or microservice.
"""

import pandas as pd
import numpy as np
import json
from typing import Dict, List, Any, Union, Optional, Callable
import logging
import re
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RuleEngine:
    """Class for managing and executing business rules"""
    
    def __init__(self):
        """Initialize the rule engine"""
        self.rules = []
        logger.info("RuleEngine initialized")
    
    def load_rules(self, rules_json: Union[str, Dict, List]) -> Dict[str, Any]:
        """
        Load rules from JSON string or dict
        
        Args:
            rules_json: JSON string, dictionary, or list of rule objects
            
        Returns:
            Dict with success status and loaded rules count
        """
        try:
            # Handle different input types
            if isinstance(rules_json, str):
                rules = json.loads(rules_json)
            else:
                rules = rules_json
                
            # Handle single rule or list of rules
            if isinstance(rules, dict) and "rules" in rules:
                rules = rules["rules"]
            elif isinstance(rules, dict):
                rules = [rules]
                
            # Validate and add each rule
            valid_rules = []
            invalid_rules = []
            
            for rule in rules:
                try:
                    # Validate rule format
                    required_fields = ["id", "name", "condition"]
                    if not all(field in rule for field in required_fields):
                        invalid_rules.append({
                            "rule": rule,
                            "error": f"Missing required fields. Required: {required_fields}"
                        })
                        continue
                    
                    # Try to compile the condition to validate it
                    try:
                        self._compile_condition(rule["condition"])
                        valid_rules.append(rule)
                    except Exception as e:
                        invalid_rules.append({
                            "rule": rule,
                            "error": f"Invalid condition: {str(e)}"
                        })
                        
                except Exception as e:
                    invalid_rules.append({
                        "rule": rule,
                        "error": str(e)
                    })
            
            # Store valid rules
            self.rules = valid_rules
            
            return {
                "success": True,
                "loaded_rules": len(valid_rules),
                "invalid_rules": len(invalid_rules),
                "invalid_rule_details": invalid_rules
            }
            
        except Exception as e:
            logger.error(f"Error loading rules: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _compile_condition(self, condition: str) -> Callable:
        """
        Compile a rule condition into an executable function
        
        Args:
            condition: String representation of the rule condition
            
        Returns:
            Compiled function that can evaluate the condition
        """
        # First, replace common operators for better readability
        condition = condition.replace('==', '==').replace('!=', '!=')
        condition = condition.replace('<=', '<=').replace('>=', '>=')
        
        # Create a function that accepts a data context and evaluates the condition
        try:
            # Create the function code
            fn_code = f"""
def evaluate_condition(data):
    try:
        return bool({condition})
    except Exception as e:
        return False
"""
            # Create a local namespace
            local_namespace = {}
            
            # Execute the function definition in the local namespace
            exec(fn_code, {'re': re, 'np': np, 'pd': pd}, local_namespace)
            
            # Return the compiled function
            return local_namespace['evaluate_condition']
            
        except Exception as e:
            logger.error(f"Error compiling condition '{condition}': {str(e)}")
            raise ValueError(f"Invalid condition syntax: {str(e)}")
    
    def apply_rules(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Apply rules to a dataframe and get violations
        
        Args:
            data: Pandas DataFrame to apply rules to
            
        Returns:
            Dict with rule application results and violations
        """
        try:
            if not self.rules:
                return {
                    "success": True,
                    "message": "No rules to apply",
                    "rules_applied": 0,
                    "violations": []
                }
            
            violations = []
            rules_applied = 0
            
            # Apply each rule to the data
            for rule in self.rules:
                rules_applied += 1
                rule_id = rule["id"]
                rule_name = rule["name"]
                condition = rule["condition"]
                severity = rule.get("severity", "medium")
                message = rule.get("message", f"Violated rule: {rule_name}")
                
                try:
                    # Compile the condition
                    evaluate_fn = self._compile_condition(condition)
                    
                    # Apply the rule to each row
                    for index, row in data.iterrows():
                        # Create data context
                        context = row.to_dict()
                        
                        # Evaluate the condition
                        result = evaluate_fn(context)
                        
                        # If condition is False, it's a violation
                        if not result:
                            violations.append({
                                "rule_id": rule_id,
                                "rule_name": rule_name,
                                "row_index": int(index),
                                "severity": severity,
                                "message": message
                            })
                            
                            # Limit to 1000 violations for performance
                            if len(violations) >= 1000:
                                break
                    
                except Exception as e:
                    logger.error(f"Error applying rule '{rule_name}': {str(e)}")
                    violations.append({
                        "rule_id": rule_id,
                        "rule_name": rule_name,
                        "row_index": None,
                        "severity": "error",
                        "message": f"Error evaluating rule: {str(e)}"
                    })
            
            return {
                "success": True,
                "rules_applied": rules_applied,
                "total_rows": len(data),
                "violation_count": len(violations),
                "violations": violations
            }
            
        except Exception as e:
            logger.error(f"Error applying rules: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_rules(self, data: pd.DataFrame, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate business rules from data using heuristics and patterns
        
        Args:
            data: Pandas DataFrame to generate rules from
            options: Options for rule generation
            
        Returns:
            Dict with generated rules
        """
        try:
            if options is None:
                options = {}
                
            generated_rules = []
            rule_id_counter = 1
            
            # Generate rules for each column based on data patterns
            for column in data.columns:
                column_data = data[column]
                dtype = column_data.dtype
                
                # Skip columns with too many unique values
                unique_ratio = len(column_data.dropna().unique()) / len(column_data.dropna()) if len(column_data.dropna()) > 0 else 0
                if unique_ratio > 0.9 and len(column_data) > 10:
                    continue
                
                # Generate rules based on data type
                if pd.api.types.is_numeric_dtype(dtype):
                    # Numeric column rules
                    rules = self._generate_numeric_rules(column, column_data, rule_id_counter)
                    generated_rules.extend(rules)
                    rule_id_counter += len(rules)
                    
                elif pd.api.types.is_string_dtype(dtype):
                    # String column rules
                    rules = self._generate_string_rules(column, column_data, rule_id_counter)
                    generated_rules.extend(rules)
                    rule_id_counter += len(rules)
                    
                elif pd.api.types.is_datetime64_dtype(dtype):
                    # Date column rules
                    rules = self._generate_date_rules(column, column_data, rule_id_counter)
                    generated_rules.extend(rules)
                    rule_id_counter += len(rules)
            
            # Generate cross-column rules if requested
            if options.get("cross_column_rules", True):
                # Find potential correlations or relationships
                corr_rules = self._generate_correlation_rules(data, rule_id_counter)
                generated_rules.extend(corr_rules)
                rule_id_counter += len(corr_rules)
            
            return {
                "success": True,
                "rules_generated": len(generated_rules),
                "rules": generated_rules
            }
            
        except Exception as e:
            logger.error(f"Error generating rules: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_numeric_rules(self, column: str, data: pd.Series, start_id: int) -> List[Dict[str, Any]]:
        """Generate rules for numeric columns"""
        rules = []
        data = data.dropna()
        
        if len(data) == 0:
            return rules
        
        # Get basic statistics
        min_val = data.min()
        max_val = data.max()
        q1 = data.quantile(0.01)  # 1st percentile
        q99 = data.quantile(0.99)  # 99th percentile
        
        # Range rule
        rules.append({
            "id": f"R{start_id}",
            "name": f"{column} Range Check",
            "condition": f"data['{column}'] >= {min_val} and data['{column}'] <= {max_val}",
            "severity": "high",
            "message": f"{column} must be between {min_val} and {max_val}"
        })
        
        # Outlier rule (more lenient)
        if q1 < q99:
            rules.append({
                "id": f"R{start_id + 1}",
                "name": f"{column} Outlier Check",
                "condition": f"data['{column}'] >= {q1} and data['{column}'] <= {q99}",
                "severity": "medium",
                "message": f"{column} has potential outlier value"
            })
        
        # If integers, check for specific values
        if pd.api.types.is_integer_dtype(data.dtype):
            # Check if column might be categorical
            unique_vals = data.unique()
            if len(unique_vals) <= 10:
                vals_str = ", ".join(map(str, unique_vals))
                rules.append({
                    "id": f"R{start_id + 2}",
                    "name": f"{column} Allowed Values",
                    "condition": f"data['{column}'] in [{vals_str}]",
                    "severity": "medium",
                    "message": f"{column} must be one of: {vals_str}"
                })
        
        return rules
    
    def _generate_string_rules(self, column: str, data: pd.Series, start_id: int) -> List[Dict[str, Any]]:
        """Generate rules for string columns"""
        rules = []
        data = data.dropna().astype(str)
        
        if len(data) == 0:
            return rules
        
        # Check if column looks like an email
        if any('@' in str(x) and '.' in str(x).split('@')[-1] for x in data.sample(min(10, len(data)))):
            rules.append({
                "id": f"R{start_id}",
                "name": f"{column} Email Format",
                "condition": f"re.match(r'^[\\w.-]+@[\\w.-]+\\.[a-zA-Z]{{2,}}$', str(data['{column}']))",
                "severity": "high",
                "message": f"{column} must be a valid email address"
            })
            
        # Length rules
        min_len = min(len(str(x)) for x in data)
        max_len = max(len(str(x)) for x in data)
        
        rules.append({
            "id": f"R{start_id + 1}",
            "name": f"{column} Length Check",
            "condition": f"len(str(data['{column}'])) >= {min_len} and len(str(data['{column}'])) <= {max_len}",
            "severity": "medium",
            "message": f"{column} length must be between {min_len} and {max_len} characters"
        })
        
        # Check if column might be categorical
        if len(data.unique()) <= 20 and len(data.unique()) < len(data) / 2:
            # Create allowed values rule
            vals = list(data.unique())
            vals_str = ", ".join(f"'{x}'" for x in vals)
            
            rules.append({
                "id": f"R{start_id + 2}",
                "name": f"{column} Allowed Values",
                "condition": f"str(data['{column}']) in [{vals_str}]",
                "severity": "medium",
                "message": f"{column} must be one of the allowed values"
            })
        
        return rules
    
    def _generate_date_rules(self, column: str, data: pd.Series, start_id: int) -> List[Dict[str, Any]]:
        """Generate rules for date columns"""
        rules = []
        data = data.dropna()
        
        if len(data) == 0:
            return rules
        
        # Get min and max dates
        min_date = data.min()
        max_date = data.max()
        
        # Convert to string format for rule
        min_date_str = min_date.strftime('%Y-%m-%d')
        max_date_str = max_date.strftime('%Y-%m-%d')
        
        rules.append({
            "id": f"R{start_id}",
            "name": f"{column} Date Range",
            "condition": f"pd.to_datetime(data['{column}']) >= pd.to_datetime('{min_date_str}') and " + 
                        f"pd.to_datetime(data['{column}']) <= pd.to_datetime('{max_date_str}')",
            "severity": "medium",
            "message": f"{column} must be between {min_date_str} and {max_date_str}"
        })
        
        # Future date rule if max date is recent
        today = pd.Timestamp.now().floor('D')
        if (max_date - today).days < 30:  # If max date is within a month of today
            rules.append({
                "id": f"R{start_id + 1}",
                "name": f"{column} No Future Dates",
                "condition": f"pd.to_datetime(data['{column}']) <= pd.Timestamp.now()",
                "severity": "high", 
                "message": f"{column} cannot be in the future"
            })
            
        return rules
    
    def _generate_correlation_rules(self, data: pd.DataFrame, start_id: int) -> List[Dict[str, Any]]:
        """Generate rules based on column correlations and relationships"""
        rules = []
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        # Skip if too few numeric columns
        if len(numeric_cols) < 2:
            return rules
        
        try:
            # Calculate correlation matrix
            corr_matrix = data[numeric_cols].corr()
            
            # Find highly correlated pairs
            for i in range(len(numeric_cols)):
                for j in range(i+1, len(numeric_cols)):
                    col1 = numeric_cols[i]
                    col2 = numeric_cols[j]
                    corr = corr_matrix.iloc[i, j]
                    
                    # Strong positive correlation
                    if corr > 0.8:
                        rules.append({
                            "id": f"R{start_id}",
                            "name": f"{col1} - {col2} Correlation",
                            "condition": f"data['{col1}'] * 0.5 <= data['{col2}'] <= data['{col1}'] * 1.5",
                            "severity": "low",
                            "message": f"Expected correlation between {col1} and {col2} not maintained"
                        })
                        start_id += 1
                        
                    # Strong negative correlation
                    elif corr < -0.8:
                        rules.append({
                            "id": f"R{start_id}",
                            "name": f"{col1} - {col2} Inverse Correlation",
                            "condition": f"(data['{col1}'] > 0 and data['{col2}'] < 0) or " + 
                                      f"(data['{col1}'] < 0 and data['{col2}'] > 0) or " +
                                      f"(data['{col1}'] == 0 and data['{col2}'] == 0)",
                            "severity": "low",
                            "message": f"Expected inverse correlation between {col1} and {col2} not maintained"
                        })
                        start_id += 1
        except Exception as e:
            logger.warning(f"Error generating correlation rules: {str(e)}")
            
        return rules

# Example usage (would be called via API endpoint in production)
if __name__ == "__main__":
    import json
    
    # Create sample data
    data = pd.DataFrame({
        'age': [25, 30, 150, 40],  # 150 violates reasonable age
        'income': [50000, 75000, 90000, -1000],  # -1000 is invalid
        'state': ['CA', 'NY', 'TX', 'ZZ'],  # ZZ is invalid
        'registration_date': pd.to_datetime(['2020-01-01', '2021-05-15', '2022-12-31', '2030-01-01'])  # future date
    })
    
    # Create rule engine
    engine = RuleEngine()
    
    # Generate rules
    generated = engine.generate_rules(data)
    print(f"Generated {generated['rules_generated']} rules")
    
    # Load rules
    sample_rules = [
        {
            "id": "R1",
            "name": "Valid Age",
            "condition": "data['age'] >= 0 and data['age'] < 120",
            "severity": "high",
            "message": "Age must be between 0 and 120"
        },
        {
            "id": "R2",
            "name": "Positive Income",
            "condition": "data['income'] >= 0",
            "severity": "medium",
            "message": "Income must be positive"
        },
        {
            "id": "R3",
            "name": "Valid State",
            "condition": "data['state'] in ['CA', 'NY', 'TX', 'FL']",
            "severity": "low",
            "message": "State must be valid"
        }
    ]
    
    engine.load_rules(sample_rules)
    
    # Apply rules
    results = engine.apply_rules(data)
    
    # Output summary
    print("\nRule Validation Results:")
    print(f"Applied {results['rules_applied']} rules to {results['total_rows']} rows")
    print(f"Found {results['violation_count']} violations")
    
    for violation in results['violations']:
        print(f"- Rule: {violation['rule_name']}, Row: {violation['row_index']}, Severity: {violation['severity']}")
