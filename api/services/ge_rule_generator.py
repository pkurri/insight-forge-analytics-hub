"""
Advanced Great Expectations rule generator for pipeline-ready rule creation.
Generates null, type, range, outlier, uniqueness, regex, and cross-column rules based on column metadata.
"""
import re

def generate_advanced_ge_rules(dataset_id, column_metadata):
    rules = []
    rule_id = 1
    for col_name, col_info in column_metadata.items():
        col_type = col_info.get('type', 'unknown')
        stats = col_info.get('stats', {})
        # Not null rule
        rules.append({
            "id": f"GE{rule_id}",
            "name": f"{col_name} Not Null",
            "condition": f"expect_column_values_to_not_be_null('{col_name}')",
            "severity": "high",
            "message": f"{col_name} should not contain null values",
            "dataset_id": dataset_id,
            "source": "great_expectations"
        })
        rule_id += 1
        # Type rule
        rules.append({
            "id": f"GE{rule_id}",
            "name": f"{col_name} Type",
            "condition": f"expect_column_values_to_be_of_type('{col_name}', '{col_type}')",
            "severity": "medium",
            "message": f"{col_name} should be of type {col_type}",
            "dataset_id": dataset_id,
            "source": "great_expectations"
        })
        rule_id += 1
        # Range rule for numeric
        if col_type == 'numeric':
            min_val = stats.get('min')
            max_val = stats.get('max')
            mean = stats.get('mean')
            std = stats.get('std')
            if min_val is not None and max_val is not None:
                rules.append({
                    "id": f"GE{rule_id}",
                    "name": f"{col_name} Range",
                    "condition": f"expect_column_values_to_be_between('{col_name}', {min_val}, {max_val})",
                    "severity": "medium",
                    "message": f"{col_name} should be between {min_val} and {max_val}",
                    "dataset_id": dataset_id,
                    "source": "great_expectations"
                })
                rule_id += 1
            if mean is not None and std is not None:
                rules.append({
                    "id": f"GE{rule_id}",
                    "name": f"{col_name} Outlier Detection",
                    "condition": f"expect_column_values_to_be_between('{col_name}', {mean-3*std}, {mean+3*std})",
                    "severity": "low",
                    "message": f"{col_name} should not have extreme outliers",
                    "dataset_id": dataset_id,
                    "source": "great_expectations"
                })
                rule_id += 1
        # Uniqueness rule
        rules.append({
            "id": f"GE{rule_id}",
            "name": f"{col_name} Unique",
            "condition": f"expect_column_values_to_be_unique('{col_name}')",
            "severity": "low",
            "message": f"{col_name} should be unique",
            "dataset_id": dataset_id,
            "source": "great_expectations"
        })
        rule_id += 1
        # Regex rule for string columns
        if col_type == 'string':
            regex = col_info.get('regex')
            if regex:
                rules.append({
                    "id": f"GE{rule_id}",
                    "name": f"{col_name} Regex",
                    "condition": f"expect_column_values_to_match_regex('{col_name}', r'{regex}')",
                    "severity": "medium",
                    "message": f"{col_name} should match regex {regex}",
                    "dataset_id": dataset_id,
                    "source": "great_expectations"
                })
                rule_id += 1
        # Cross-column rule example (e.g., if two columns must be equal)
        if col_info.get('cross_column_equal'):
            other_col = col_info['cross_column_equal']
            rules.append({
                "id": f"GE{rule_id}",
                "name": f"{col_name} equals {other_col}",
                "condition": f"expect_column_pair_values_to_be_equal('{col_name}', '{other_col}')",
                "severity": "medium",
                "message": f"{col_name} should equal {other_col}",
                "dataset_id": dataset_id,
                "source": "great_expectations"
            })
            rule_id += 1
    return rules
