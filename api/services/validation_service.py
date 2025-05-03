from typing import Dict, Any, List, Optional
import pandas as pd
import json
from pydantic import BaseModel, create_model, validator
from datetime import datetime
import great_expectations as ge
from transformers import pipeline

class ValidationRule(BaseModel):
    field: str
    rule_type: str
    parameters: Dict[str, Any]

class ValidationService:
    def __init__(self):
        self.sentiment_analyzer = pipeline("sentiment-analysis")
        
    def load_rules_from_json(self, json_path: str) -> List[ValidationRule]:
        """Load validation rules from a JSON file"""
        with open(json_path, 'r') as f:
            rules_data = json.load(f)
        return [ValidationRule(**rule) for rule in rules_data]

    def create_dynamic_model(self, df: pd.DataFrame, rules: List[ValidationRule]) -> BaseModel:
        """Create a Pydantic model dynamically based on DataFrame schema and rules"""
        field_types = {}
        validators = {}

        for column in df.columns:
            dtype = df[column].dtype
            if dtype == 'object':
                field_types[column] = (str, ...)
            elif dtype == 'int64':
                field_types[column] = (int, ...)
            elif dtype == 'float64':
                field_types[column] = (float, ...)
            else:
                field_types[column] = (str, ...)

        # Add validators based on rules
        for rule in rules:
            if rule.rule_type == 'range':
                validators[f'validate_{rule.field}'] = validator(
                    rule.field,
                    allow_reuse=True
                )(lambda v, field: self._validate_range(v, field, rule.parameters))

        return create_model('DynamicModel', **field_types)

    async def validate_data(
        self,
        df: pd.DataFrame,
        rules_path: Optional[str] = None,
        custom_rules: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Validate data using multiple approaches:
        1. Pydantic schema validation
        2. Great Expectations for data quality
        3. Custom business rules
        4. AI-based validation using Hugging Face
        """
        validation_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_rows': len(df),
            'validation_summary': {},
            'failed_rows': [],
            'ai_insights': []
        }

        # 1. Schema Validation with Pydantic
        rules = []
        if rules_path:
            rules.extend(self.load_rules_from_json(rules_path))
        if custom_rules:
            rules.extend([ValidationRule(**rule) for rule in custom_rules])

        if rules:
            dynamic_model = self.create_dynamic_model(df, rules)
            schema_errors = []
            for idx, row in df.iterrows():
                try:
                    dynamic_model(**row.to_dict())
                except Exception as e:
                    schema_errors.append({'row': idx, 'error': str(e)})
            validation_results['schema_validation'] = {
                'passed': len(schema_errors) == 0,
                'errors': schema_errors
            }

        # 2. Great Expectations Validation
        ge_df = ge.from_pandas(df)
        ge_results = {}

        # Basic column expectations
        for column in df.columns:
            if df[column].dtype in ['int64', 'float64']:
                ge_results[column] = {
                    'not_null': ge_df.expect_column_values_to_not_be_null(column).success,
                    'in_range': ge_df.expect_column_values_to_be_between(
                        column,
                        min_value=df[column].min(),
                        max_value=df[column].max()
                    ).success
                }
            else:
                ge_results[column] = {
                    'not_null': ge_df.expect_column_values_to_not_be_null(column).success,
                    'unique_count': ge_df.expect_column_unique_value_count_to_be_between(
                        column,
                        min_value=1
                    ).success
                }

        validation_results['data_quality_validation'] = ge_results

        # 3. Custom Business Rules
        for rule in rules:
            if rule.rule_type == 'custom':
                validation_results['custom_rules'] = self._apply_custom_rule(
                    df,
                    rule.field,
                    rule.parameters
                )

        # 4. AI-based Validation (sample for text columns)
        text_columns = df.select_dtypes(include=['object']).columns
        for column in text_columns[:3]:  # Limit to first 3 text columns for performance
            sample_texts = df[column].dropna().head(5).tolist()
            sentiments = self.sentiment_analyzer(sample_texts)
            validation_results['ai_insights'].append({
                'column': column,
                'sentiment_analysis': sentiments
            })

        return validation_results

    def _validate_range(self, value: Any, field: str, params: Dict[str, Any]) -> Any:
        """Validate if a value is within specified range"""
        if not params.get('min') <= value <= params.get('max'):
            raise ValueError(f"{field} must be between {params['min']} and {params['max']}")
        return value

    def _apply_custom_rule(
        self,
        df: pd.DataFrame,
        field: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply custom business rule to the data"""
        if parameters.get('rule_name') == 'unique_combination':
            fields = parameters.get('fields', [])
            is_unique = df.groupby(fields).size().reset_index().shape[0] == df.shape[0]
            return {
                'rule': 'unique_combination',
                'fields': fields,
                'passed': is_unique
            }
        # Add more custom rules as needed
        return {'error': 'Unknown custom rule'}
