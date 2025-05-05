"""Business Rules Service Module

This module provides the BusinessRulesService class for managing business rules, including:
- Manual and AI-assisted rule creation
- Rule import/export via JSON
"""

# Re-export the business rules service from the new modular structure
from api.services.business_rules import business_rules_service

# For backward compatibility, export all attributes from the service instance
for attr_name in dir(business_rules_service):
    if not attr_name.startswith('_'):
        globals()[attr_name] = getattr(business_rules_service, attr_name)
from api.db.connection import get_db_session
from api.services.internal_ai_service import generate_text_internal

settings = get_settings()
logger = logging.getLogger(__name__)

# Note: BusinessRulesRepository and DatasetRepository are now imported inside functions to avoid circular imports.

class BusinessRulesService:
    """
    Service for managing and executing business rules.

    Features:
    - Create, update, and delete business rules
    - Import/export rules via JSON
    - Generate rules using AI (OpenAI, Hugging Face), Great Expectations, and Pydantic
    - Execute rules on datasets
    - Log rule execution results
    - Extensible for additional rule sources and validation logic
    - Apply rules during data pipeline processing
    - Validate data against rules before vectorization
    """

    def __init__(self):
        """
        Initialize the service components, including AI and validation frameworks.
        """
        # Initialize OpenAI client if API key is available
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

        # Initialize Great Expectations context for validation
        self.ge_context = ge.get_context()

        # Cache for loaded rules per dataset
        self.rules_cache = {}
            
    async def load_rules(self, dataset_id: str) -> List[Dict[str, Any]]:
        """
        Load all active rules for a dataset, using cache if available.

        Args:
            dataset_id: ID of the dataset to load rules for
        Returns:
            List of active rules for the dataset
        """
        try:
            # Use cache to avoid redundant DB queries
            if dataset_id in self.rules_cache:
                return self.rules_cache[dataset_id]
            # Fetch rules from repository
            rules = await rules_repo.get_rules_by_dataset(dataset_id)
            self.rules_cache[dataset_id] = rules
            return rules
        except Exception as e:
            logger.error(f"Error loading rules: {str(e)}")
            return []
            
    async def create_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new business rule, validating and enriching the rule as needed.

        Args:
            rule_data: Dictionary containing rule information:
                - name: Rule name
                - description: Rule description
                - condition: Rule condition (expression or validation)
                - severity: Rule severity (low, medium, high)
                - message: Error message when rule fails
                - source: Rule source (manual, great_expectations, pydantic, huggingface, ai)
                - dataset_id: ID of the dataset this rule applies to
                - dataset_metadata: Additional dataset metadata
                - vector_metadata: Additional vector metadata
                - pipeline_metadata: Additional pipeline metadata
        Returns:
            Created rule object
        Raises:
            ValueError: If rule format or condition is invalid
            Exception: For any other errors during rule creation
        """
        try:
            # Validate rule format (structure, required fields)
            if not self._validate_rule_format(rule_data):
                raise ValueError("Invalid rule format")

            # Assign a unique rule ID
            rule_data["id"] = str(uuid.uuid4())

            # Handle rule source-specific enrichment
            source = rule_data.get("source", "manual")
            if source == "great_expectations":
                rule_data = await self._create_ge_rule(rule_data)
            elif source == "pydantic":
                rule_data = await self._create_pydantic_rule(rule_data)
            elif source in ("huggingface", "hf"):
                rule_data = await self._create_hf_rule(rule_data)
            elif source == "ai":
                rule_data = await self._create_ai_rule(rule_data)

            # Validate the rule's condition (syntax/logic)
            if not await self._validate_condition(rule_data["condition"]):
                raise ValueError("Invalid rule condition")

            # Persist rule in the database
            rule = await rules_repo.create_rule(rule_data)

            # Update cache if present
            dataset_id = rule_data["dataset_id"]
            if dataset_id in self.rules_cache:
                self.rules_cache[dataset_id].append(rule)

            # Log rule creation event
            await self._log_rule_execution(
                rule["id"],
                {
                    "success": True,
                    "message": "Rule created successfully",
                    "execution_meta": {"action": "create"}
                }
            )
            return rule
        except Exception as e:
            logger.error(f"Error creating rule: {str(e)}")
            raise
            
            # Update cache
            dataset_id = rule_data["dataset_id"]
            if dataset_id in self.rules_cache:
                self.rules_cache[dataset_id].append(rule)
            
            # Log rule creation
            await self._log_rule_execution(
                rule["id"],
                {
                    "success": True,
                    "message": "Rule created successfully",
                    "execution_meta": {"action": "create"}
                }
            )
            
            return rule
            
        except Exception as e:
            logger.error(f"Error creating rule: {str(e)}")
            raise
            
    async def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing business rule.

        Args:
            rule_id: ID of the rule to update
            updates: Dictionary of fields to update
        Returns:
            Updated rule object
        Raises:
            ValueError: If the updated condition is invalid
            Exception: For any other errors during update
        """
        try:
            updates["updated_at"] = datetime.now().isoformat()
            # If condition is updated, validate it
            if "condition" in updates:
                if not await self._validate_condition(updates["condition"]):
                    raise ValueError("Invalid rule condition")
            # Perform update in DB
            async with get_db_session() as session:
                set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
                await session.execute(
                    text(f"UPDATE business_rules SET {set_clause} WHERE id = :rule_id"),
                    {**updates, "rule_id": rule_id}
                )
                await session.commit()
            return await self.get_rule(rule_id)
        except Exception as e:
            logger.error(f"Error updating rule: {str(e)}")
            raise
            
    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a business rule."""
        try:
            async with get_db_session() as session:
                await session.execute(
                    text("DELETE FROM business_rules WHERE id = :rule_id"),
                    {"rule_id": rule_id}
                )
                await session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting rule: {str(e)}")
            raise
            
    async def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific business rule by ID.

        Args:
            rule_id: ID of the rule to retrieve
        Returns:
            Rule object as a dictionary, or None if not found
        Raises:
            Exception: For any errors during retrieval
        """
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    text("SELECT * FROM business_rules WHERE id = :rule_id"),
                    {"rule_id": rule_id}
                )
                row = result.first()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting rule: {str(e)}")
            raise
            
    async def get_rules(self, dataset_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all business rules for a dataset.

        Args:
            dataset_id: ID of the dataset
        Returns:
            List of rule objects as dictionaries
        Raises:
            Exception: For any errors during retrieval
        """
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    text("""
                    SELECT * FROM business_rules 
                    WHERE dataset_id = :dataset_id
                    ORDER BY priority DESC, created_at ASC
                    """),
                    {"dataset_id": dataset_id}
                )
                return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Error getting rules: {str(e)}")
            raise
            
    async def import_rules(self, dataset_id: str, rules_json: str) -> Dict[str, Any]:
        """
        Import business rules from a JSON array.

        Args:
            dataset_id: ID of the dataset to import rules for
            rules_json: JSON string containing an array of rule objects
        Returns:
            Dict containing success status, imported/failed counts, and rule details
        Raises:
            Exception: For any errors during import
        """
        try:
            rules = json.loads(rules_json)
            if not isinstance(rules, list):
                raise ValueError("Invalid format: JSON must be an array of rule objects")
            imported_rules = []
            failed_rules = []
            for rule in rules:
                try:
                    rule["dataset_id"] = dataset_id
                    rule["source"] = rule.get("source", "manual")
                    created_rule = await self.create_rule(rule)
                    imported_rules.append(created_rule)
                except Exception as rule_error:
                    failed_rules.append({
                        "rule": rule.get("name", "Unknown"),
                        "error": str(rule_error)
                    })
            return {
                "success": len(imported_rules) > 0,
                "imported_count": len(imported_rules),
                "failed_count": len(failed_rules),
                "imported_rules": imported_rules,
                "failed_rules": failed_rules
            }
        except Exception as e:
            logger.error(f"Error importing rules: {str(e)}")
            raise
        
    async def generate_ai_rules(self, dataset_id: str, column_meta: Dict[str, Any], engine: str = "ai_default", model_type: str = None) -> Dict[str, Any]:
        """Generate business rules using different AI engines based on column meta.
        
        Args:
            dataset_id: ID of the dataset to generate rules for
            column_meta: Dictionary containing column information about the dataset
            engine: AI engine to use for rule generation (huggingface, pydantic, great_expectations, ai_default)
            model_type: Type of internal model to use for generation (must be in settings.ALLOWED_TEXT_GEN_MODELS)
        Returns:
            Dictionary containing generated rules and meta
        """
        try:
            # Get dataset information
            dataset = await dataset_repo.get_dataset(dataset_id)
            if not dataset:
                raise ValueError(f"Dataset {dataset_id} not found")
            
            # Validate engine parameter
            valid_engines = ["huggingface", "pydantic", "great_expectations", "ai_default"]
            if engine not in valid_engines:
                logger.warning(f"Invalid engine '{engine}', defaulting to 'ai_default'")
                engine = "ai_default"
                
            logger.info(f"Generating business rules using {engine} engine for dataset {dataset_id}")
            
            # Generate rules based on the selected engine
            if engine == "huggingface":
                return await self._generate_huggingface_rules(dataset_id, column_meta)
            elif engine == "pydantic":
                return await self._generate_pydantic_rules(dataset_id, column_meta)
            elif engine == "great_expectations":
                return await self._generate_great_expectations_rules(dataset_id, column_meta)
            else:  # ai_default
                # Only allow internal models
                allowed_models = getattr(settings, "ALLOWED_TEXT_GEN_MODELS", ["Mistral-3.2-instruct"])
                if not model_type or model_type not in allowed_models:
                    model_type = allowed_models[0]

                # Use internal text generation models
                prompt = self._build_prompt(column_meta) if hasattr(self, '_build_prompt') else str(column_meta)
                generated = await generate_text_internal(prompt, model=model_type)
                # Parse the generated text into rules
                return {"rules": generated, "meta": {"model": model_type, "source": "ai_default"}}
        except Exception as e:
            logger.error(f"Error generating AI rules with {engine} engine: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _generate_huggingface_rules(self, dataset_id: str, column_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Generate business rules using Hugging Face models.
        
        Args:
            dataset_id: ID of the dataset to generate rules for
            column_meta: Dictionary containing column information about the dataset
            
        Returns:
            Dictionary containing generated rules with Hugging Face as source
        """
        try:
            # This would typically use a Hugging Face model API or pipeline
            # For now, we'll use a simplified approach with our internal AI service
            prompt = f"""Generate business rules for data validation using Hugging Face models.
            Dataset columns: {json.dumps(column_meta, indent=2)}
            Generate 3-5 business rules that would be useful for validating this data.
            Each rule should include name, description, condition (as a Python expression), severity (low/medium/high), and message.
            """
            
            # Use internal text generation as a placeholder for actual Hugging Face API call
            generated = await generate_text_internal(prompt)
            
            # Process the generated rules to ensure they have the source field
            if isinstance(generated, list):
                for rule in generated:
                    if isinstance(rule, dict):
                        rule["source"] = "huggingface"
            
            return {"rules": generated, "meta": {"source": "huggingface"}}
        except Exception as e:
            logger.error(f"Error generating Hugging Face rules: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _generate_pydantic_rules(self, dataset_id: str, column_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Generate business rules using Pydantic models.
        
        Args:
            dataset_id: ID of the dataset to generate rules for
            column_meta: Dictionary containing column information about the dataset
            
        Returns:
            Dictionary containing generated rules with Pydantic as source
        """
        try:
            rules = []
            
            # Generate rules based on column types and constraints
            for col_name, col_info in column_meta.items():
                # Skip if no type information
                if not col_info.get("type"):
                    continue
                    
                col_type = col_info.get("type").lower()
                
                # Generate type validation rules
                if col_type in ["int", "integer", "float", "number"]:
                    # Numeric validation
                    rules.append({
                        "name": f"{col_name} Type Validation",
                        "description": f"Validates that {col_name} contains only {col_type} values",
                        "condition": f"df['{col_name}'].apply(lambda x: isinstance(x, {col_type}) if pd.notna(x) else True).all()",
                        "severity": "high",
                        "message": f"Column {col_name} must contain only {col_type} values",
                        "source": "pydantic"
                    })
                    
                    # Add range validation if min/max are provided
                    if "min" in col_info and "max" in col_info:
                        rules.append({
                            "name": f"{col_name} Range Validation",
                            "description": f"Validates that {col_name} values are within the allowed range",
                            "condition": f"df[df['{col_name}'].notna()]['{col_name}'].between({col_info['min']}, {col_info['max']}).all()",
                            "severity": "medium",
                            "message": f"Column {col_name} values must be between {col_info['min']} and {col_info['max']}",
                            "source": "pydantic"
                        })
                        
                elif col_type in ["str", "string", "text"]:
                    # String validation
                    rules.append({
                        "name": f"{col_name} Type Validation",
                        "description": f"Validates that {col_name} contains only string values",
                        "condition": f"df['{col_name}'].apply(lambda x: isinstance(x, str) if pd.notna(x) else True).all()",
                        "severity": "high",
                        "message": f"Column {col_name} must contain only string values",
                        "source": "pydantic"
                    })
                    
                    # Add length validation if max_length is provided
                    if "max_length" in col_info:
                        rules.append({
                            "name": f"{col_name} Length Validation",
                            "description": f"Validates that {col_name} values don't exceed the maximum length",
                            "condition": f"df[df['{col_name}'].notna()]['{col_name}'].str.len().max() <= {col_info['max_length']}",
                            "severity": "medium",
                            "message": f"Column {col_name} values must not exceed {col_info['max_length']} characters",
                            "source": "pydantic"
                        })
                        
                elif col_type in ["date", "datetime"]:
                    # Date validation
                    rules.append({
                        "name": f"{col_name} Date Validation",
                        "description": f"Validates that {col_name} contains valid date values",
                        "condition": f"pd.to_datetime(df['{col_name}'], errors='coerce').notna().all()",
                        "severity": "high",
                        "message": f"Column {col_name} must contain valid date values",
                        "source": "pydantic"
                    })
                
                # Add not-null validation if required
                if col_info.get("required", False):
                    rules.append({
                        "name": f"{col_name} Required Validation",
                        "description": f"Validates that {col_name} does not contain null values",
                        "condition": f"df['{col_name}'].notna().all()",
                        "severity": "high",
                        "message": f"Column {col_name} must not contain null values",
                        "source": "pydantic"
                    })
            
            return {"rules": rules, "meta": {"source": "pydantic"}}
        except Exception as e:
            logger.error(f"Error generating Pydantic rules: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _generate_great_expectations_rules(self, dataset_id: str, column_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Generate business rules using Great Expectations.
        
        Args:
            dataset_id: ID of the dataset to generate rules for
            column_meta: Dictionary containing column information about the dataset
            
        Returns:
            Dictionary containing generated rules with Great Expectations as source
        """
        try:
            rules = []
            
            # Generate rules based on column types and common validation patterns
            for col_name, col_info in column_meta.items():
                # Skip if no type information
                if not col_info.get("type"):
                    continue
                    
                col_type = col_info.get("type").lower()
                
                # Column existence check
                rules.append({
                    "name": f"Expect {col_name} to exist",
                    "description": f"Validates that column {col_name} exists in the dataset",
                    "condition": f"'{col_name}' in df.columns",
                    "severity": "high",
                    "message": f"Column {col_name} must exist in the dataset",
                    "source": "great_expectations"
                })
                
                # Type-specific validations
                if col_type in ["int", "integer", "float", "number"]:
                    # Numeric validation
                    rules.append({
                        "name": f"Expect {col_name} values to be valid numbers",
                        "description": f"Validates that {col_name} contains valid numeric values",
                        "condition": f"pd.to_numeric(df['{col_name}'], errors='coerce').notna().all()",
                        "severity": "high",
                        "message": f"Column {col_name} must contain valid numeric values",
                        "source": "great_expectations"
                    })
                    
                    # Statistical validations
                    rules.append({
                        "name": f"Expect {col_name} values to be reasonable",
                        "description": f"Validates that {col_name} values are within a reasonable range (not extreme outliers)",
                        "condition": f"(df['{col_name}'] - df['{col_name}'].mean()).abs() <= 3 * df['{col_name}'].std()",
                        "severity": "medium",
                        "message": f"Column {col_name} contains outlier values that are more than 3 standard deviations from the mean",
                        "source": "great_expectations"
                    })
                    
                elif col_type in ["str", "string", "text"]:
                    # String validation
                    rules.append({
                        "name": f"Expect {col_name} values to be strings",
                        "description": f"Validates that {col_name} contains string values",
                        "condition": f"df['{col_name}'].apply(lambda x: isinstance(x, str) if pd.notna(x) else True).all()",
                        "severity": "high",
                        "message": f"Column {col_name} must contain string values",
                        "source": "great_expectations"
                    })
                    
                    # Non-empty string validation
                    rules.append({
                        "name": f"Expect {col_name} values to not be empty strings",
                        "description": f"Validates that {col_name} does not contain empty strings",
                        "condition": f"df[df['{col_name}'].notna()]['{col_name}'].str.strip().str.len().gt(0).all()",
                        "severity": "medium",
                        "message": f"Column {col_name} must not contain empty strings",
                        "source": "great_expectations"
                    })
                    
                elif col_type in ["date", "datetime"]:
                    # Date validation
                    rules.append({
                        "name": f"Expect {col_name} values to be valid dates",
                        "description": f"Validates that {col_name} contains valid date values",
                        "condition": f"pd.to_datetime(df['{col_name}'], errors='coerce').notna().all()",
                        "severity": "high",
                        "message": f"Column {col_name} must contain valid date values",
                        "source": "great_expectations"
                    })
                    
                    # Future date validation
                    rules.append({
                        "name": f"Expect {col_name} values to not be in the future",
                        "description": f"Validates that {col_name} does not contain future dates",
                        "condition": f"pd.to_datetime(df['{col_name}'], errors='coerce').dt.date.max() <= pd.Timestamp.now().date()",
                        "severity": "medium",
                        "message": f"Column {col_name} must not contain future dates",
                        "source": "great_expectations"
                    })
                
                # Completeness validation (applicable to all types)
                rules.append({
                    "name": f"Expect {col_name} to be at least 95% complete",
                    "description": f"Validates that {col_name} has at least 95% non-null values",
                    "condition": f"df['{col_name}'].notna().mean() >= 0.95",
                    "severity": "medium",
                    "message": f"Column {col_name} must be at least 95% complete (non-null)",
                    "source": "great_expectations"
                })
            
            return {"rules": rules, "meta": {"source": "great_expectations"}}
        except Exception as e:
            logger.error(f"Error generating Great Expectations rules: {str(e)}")
            return {"success": False, "error": str(e)}
        
    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a business rule."""
        try:
            async with get_db_session() as session:
                await session.execute(
                    text("DELETE FROM business_rules WHERE id = :rule_id"),
                    {"rule_id": rule_id}
                )
                await session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting rule: {str(e)}")
            raise
        
    async def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific business rule."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    text("SELECT * FROM business_rules WHERE id = :rule_id"),
                    {"rule_id": rule_id}
                )
                row = result.first()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting rule: {str(e)}")
            raise
        
    async def get_rules(self, dataset_id: str) -> List[Dict[str, Any]]:
        """Get all business rules for a dataset."""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    text(f"""
                SELECT * FROM {settings.DB_SCHEMA}.business_rules 
                WHERE dataset_id = :dataset_id
                ORDER BY priority DESC, created_at ASC
                """),
                    {"dataset_id": dataset_id}
                )
                return [dict(row) for row in result]
                
        except Exception as e:
            logger.error(f"Error getting rules: {str(e)}")
            raise
            
    async def import_rules(self, dataset_id: str, rules_json: str) -> Dict[str, Any]:
        """Import business rules from JSON.
        
        Args:
            dataset_id: ID of the dataset to import rules for
            rules_json: JSON string containing an array of rule objects
            
        Returns:
            Dict containing success status and number of imported rules
        """
        try:
            rules = json.loads(rules_json)
            if not isinstance(rules, list):
                raise ValueError("Invalid format: JSON must be an array of rule objects")
                
            imported_rules = []
            failed_rules = []
            
            for rule in rules:
                try:
                    # Add dataset ID and source
                    rule["dataset_id"] = dataset_id
                    rule["source"] = rule.get("source", "manual")
                    
                    # Create rule
                    created_rule = await self.create_rule(rule)
                    imported_rules.append(created_rule)
                except Exception as rule_error:
                    failed_rules.append({
                        "rule": rule.get("name", "Unknown"),
                        "error": str(rule_error)
                    })
            
            return {
                "success": len(imported_rules) > 0,
                "imported_count": len(imported_rules),
                "failed_count": len(failed_rules),
                "imported_rules": imported_rules,
                "failed_rules": failed_rules
            }
        except Exception as e:
            logger.error(f"Error generating import rules: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

            
    async def _generate_ge_rules(self, dataset_id: str, column_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Generate rules using Great Expectations based on column meta.
        
        Args:
            dataset_id: ID of the dataset
            column_meta: Column meta
            
        Returns:
            Dictionary containing generated rules
        """
        try:
            rules = []
            rule_id = 1
            
            # Generate rules for each column based on its type
            for col_name, col_info in column_meta.items():
                col_type = col_info.get('type', 'unknown')
                
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
                
                # Type-specific rules
                if col_type == 'numeric':
                    # Range rule
                    stats = col_info.get('stats', {})
                    min_val = stats.get('min')
                    max_val = stats.get('max')
                    
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
                        
                elif col_type == 'categorical':
                    categories = col_info.get('stats', {}).get('categories', [])
                    if categories and len(categories) <= 20:  # Only if reasonable number of categories
                        categories_str = str(categories).replace("'", "\"")
                        rules.append({
                            "id": f"GE{rule_id}",
                            "name": f"{col_name} Valid Values",
                            "condition": f"expect_column_values_to_be_in_set('{col_name}', {categories_str})",
                            "severity": "medium",
                            "message": f"{col_name} should be one of the allowed values",
                            "dataset_id": dataset_id,
                            "source": "great_expectations"
                        })
                        rule_id += 1
                        
                elif col_type == 'datetime':
                    # Date format rule
                    rules.append({
                        "id": f"GE{rule_id}",
                        "name": f"{col_name} Date Format",
                        "condition": f"expect_column_values_to_match_strftime_format('{col_name}', '%Y-%m-%d')",
                        "severity": "medium",
                        "message": f"{col_name} should be in valid date format",
                        "dataset_id": dataset_id,
                        "source": "great_expectations"
                    })
                    rule_id += 1
            
            # Create rules in database
            created_rules = []
            for rule in rules:
                try:
                    created_rule = await self.create_rule(rule)
                    created_rules.append(created_rule)
                except Exception as rule_error:
                    logger.error(f"Error creating GE rule: {str(rule_error)}")
            
            return {
                "success": True,
                "rules_generated": len(created_rules),
                "rules": created_rules
            }
            
        except Exception as e:
            logger.error(f"Error generating Great Expectations rules: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_pydantic_rules(self, dataset_id: str, column_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Generate rules using Pydantic based on column meta.
        
        Args:
            dataset_id: ID of the dataset
            column_meta: Column meta
            
        Returns:
            Dictionary containing generated rules
        """
        try:
            rules = []
            rule_id = 1
            
            # Generate a schema based on column meta
            schema = {}
            for col_name, col_info in column_meta.items():
                col_type = col_info.get('type', 'unknown')
                
                if col_type == 'numeric':
                    stats = col_info.get('stats', {})
                    min_val = stats.get('min')
                    max_val = stats.get('max')
                    
                    # Create a rule for numeric range validation
                    if min_val is not None and max_val is not None:
                        rules.append({
                            "id": f"PYD{rule_id}",
                            "name": f"{col_name} Numeric Validation",
                            "condition": f"{{ '{col_name}': {{ 'type': 'number', 'minimum': {min_val}, 'maximum': {max_val} }} }}",
                            "severity": "medium",
                            "message": f"{col_name} should be a number between {min_val} and {max_val}",
                            "dataset_id": dataset_id,
                            "source": "pydantic"
                        })
                        rule_id += 1
                        
                elif col_type == 'categorical':
                    categories = col_info.get('stats', {}).get('categories', [])
                    if categories and len(categories) <= 20:  # Only if reasonable number of categories
                        categories_str = str(categories).replace("'", "\"")
                        rules.append({
                            "id": f"PYD{rule_id}",
                            "name": f"{col_name} Categorical Validation",
                            "condition": f"{{ '{col_name}': {{ 'type': 'string', 'enum': {categories_str} }} }}",
                            "severity": "medium",
                            "message": f"{col_name} should be one of the allowed values",
                            "dataset_id": dataset_id,
                            "source": "pydantic"
                        })
                        rule_id += 1
                        
                elif col_type == 'datetime':
                    rules.append({
                        "id": f"PYD{rule_id}",
                        "name": f"{col_name} Date Validation",
                        "condition": f"{{ '{col_name}': {{ 'type': 'string', 'format': 'date-time' }} }}",
                        "severity": "medium",
                        "message": f"{col_name} should be a valid date",
                        "dataset_id": dataset_id,
                        "source": "pydantic"
                    })
                    rule_id += 1
                    
                else:  # Default to string
                    rules.append({
                        "id": f"PYD{rule_id}",
                        "name": f"{col_name} String Validation",
                        "condition": f"{{ '{col_name}': {{ 'type': 'string' }} }}",
                        "severity": "low",
                        "message": f"{col_name} should be a valid string",
                        "dataset_id": dataset_id,
                        "source": "pydantic"
                    })
                    rule_id += 1
            
            # Create rules in database
            created_rules = []
            for rule in rules:
                try:
                    created_rule = await self.create_rule(rule)
                    created_rules.append(created_rule)
                except Exception as rule_error:
                    logger.error(f"Error creating Pydantic rule: {str(rule_error)}")
            
            return {
                "success": True,
                "rules_generated": len(created_rules),
                "rules": created_rules
            }
            
        except Exception as e:
            logger.error(f"Error generating Pydantic rules: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_hf_rules(self, dataset_id: str, column_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Generate advanced Hugging Face rules using a configurable model (default: 'distilbert-base-uncased').
        For text columns: flag low-confidence, toxic/offensive content, and unexpected labels.
        For numeric columns: add anomaly detection (z-score and isolation forest if available).
        For categorical columns: add label drift and rare category detection.
        All rules are data-driven and meta is returned about the logic and model used.
        """
        try:
            rules = []
            rule_id = 1
            for col_name, col_info in column_meta.items():
                col_type = col_info.get('type', 'unknown')
                # Generic not-null rule
                rules.append({
                    "id": f"HF{rule_id}",
                    "name": f"{col_name} not null",
                    "condition": f"df['{col_name}'].notnull().all()",
                    "severity": "high",
                    "message": f"{col_name} should not be null",
                    "dataset_id": dataset_id,
                    "source": "huggingface"
                })
                rule_id += 1
                # Text: classifier-based label/score rule
                if col_type == 'text':
                    # Low-confidence flag
                    rules.append({
                        "id": f"HF{rule_id}",
                        "name": f"{col_name} HF low-confidence flag",
                        "condition": f"min([p['score'] for p in self.hf_classifier(df['{col_name}'].astype(str).tolist())]) > 0.5",
                        "severity": "medium",
                        "message": f"{col_name} should have high-confidence predictions by Hugging Face model {self.hf_model_name}",
                        "dataset_id": dataset_id,
                        "source": "huggingface"
                    })
                    rule_id += 1
                    # Toxicity/offensive content flag (if a toxicity model is available)
                    rules.append({
                        "id": f"HF{rule_id}",
                        "name": f"{col_name} HF toxicity flag",
                        "condition": f"any('toxic' in p['label'].lower() for p in self.hf_classifier(df['{col_name}'].astype(str).tolist()))",
                        "severity": "high",
                        "message": f"{col_name} should not contain toxic or offensive content (requires toxicity model)",
                        "dataset_id": dataset_id,
                        "source": "huggingface"
                    })
                    rule_id += 1
                # Numeric: anomaly detection using Z-score
                if col_type == 'numeric':
                    stats = col_info.get('stats', {})
                    mean = stats.get('mean')
                    std = stats.get('std')
                    if mean is not None and std is not None:
                        rules.append({
                            "id": f"HF{rule_id}",
                            "name": f"{col_name} HF anomaly detection (z-score)",
                            "condition": f"((df['{col_name}'] - {mean}) / {std}).abs().max() < 4",
                            "severity": "medium",
                            "message": f"{col_name} should not have extreme outliers (|z| < 4)",
                            "dataset_id": dataset_id,
                            "source": "huggingface"
                        })
                        rule_id += 1
                    # Isolation Forest anomaly detection (pseudo-code, requires sklearn)
                    rules.append({
                        "id": f"HF{rule_id}",
                        "name": f"{col_name} HF anomaly detection (isolation forest)",
                        "condition": "# Use IsolationForest from sklearn to flag anomalies in this column",
                        "severity": "medium",
                        "message": f"{col_name} should not have isolation forest-detected anomalies",
                        "dataset_id": dataset_id,
                        "source": "huggingface",
                        "note": "Requires sklearn and model training on column data"
                    })
                    rule_id += 1
                # Categorical: label drift and rare category detection
                if col_type == 'categorical':
                    categories = col_info.get('stats', {}).get('categories', [])
                    if categories:
                        # Label drift
                        rules.append({
                            "id": f"HF{rule_id}",
                            "name": f"{col_name} HF label drift",
                            "condition": f"set(df['{col_name}'].unique()).issubset(set({categories}))",
                            "severity": "medium",
                            "message": f"{col_name} should not have unseen categories compared to training",
                            "dataset_id": dataset_id,
                            "source": "huggingface"
                        })
                        rule_id += 1
                        # Rare category detection
                        rules.append({
                            "id": f"HF{rule_id}",
                            "name": f"{col_name} HF rare category flag",
                            "condition": "# Flag categories in this column with frequency < 1%",
                            "severity": "low",
                            "message": f"{col_name} contains rare/unexpected categories",
                            "dataset_id": dataset_id,
                            "source": "huggingface",
                            "note": "Requires frequency analysis of value counts"
                        })
                        rule_id += 1
            # Create rules in database
            created_rules = []
            for rule in rules:
                try:
                    created_rule = await self.create_rule(rule)
                    created_rules.append(created_rule)
                except Exception as rule_error:
                    logger.error(f"Error creating Hugging Face rule: {str(rule_error)}")
            return {
                "success": True,
                "rules_generated": len(created_rules),
                "rules": created_rules,
                "meta": {
                    "generator": "huggingface",
                    "model": self.hf_model_name,
                    "logic": "Text: classifier confidence, toxicity; Numeric: z-score and isolation forest anomaly detection; Categorical: label drift and rare category analysis."
                }
            }
        except Exception as e:
            logger.error(f"Error generating Hugging Face rules: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "meta": {"generator": "huggingface", "model": self.hf_model_name}
            }
            
    async def execute_rules(self, dataset_id: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute all active rules on a dataset.
        
            Args:
                dataset_id: ID of the dataset to execute rules for
                df: Pandas DataFrame containing the dataset
                
            Returns:
                Dictionary containing execution results
        """
        try:
            # Load active rules
            rules = await self.load_rules(dataset_id)
            if not rules:
                return {
                    "success": True,
                    "message": "No active rules found",
                    "results": []
                }
            
            # Execute rules in parallel
            results = await asyncio.gather(
                *[self._execute_rule(rule, df) for rule in rules],
                return_exceptions=True
            )
            
            # Process results
            processed_results = []
            for rule, result in zip(rules, results):
                if isinstance(result, Exception):
                    logger.error(f"Error executing rule {rule['id']}: {str(result)}")
                    processed_results.append({
                        "rule_id": rule["id"],
                        "name": rule["name"],
                        "success": False,
                        "error": str(result)
                    })
                else:
                    processed_results.append(result)
            
            # Log execution results
            await self._log_rules_execution(
                dataset_id,
                {
                    "total_rules": len(rules),
                    "success_count": sum(1 for r in processed_results if r["success"]),
                    "results": processed_results
                }
            )
            
            # Aggregate results
            success = all(r["success"] for r in processed_results)
            failed_rules = [r for r in processed_results if not r["success"]]
            
            return {
                "success": success,
                "message": "All rules passed" if success else f"{len(failed_rules)} rules failed",
                "results": processed_results
            }
            
        except Exception as e:
            logger.error(f"Error executing rules: {str(e)}")
            raise
            
    async def _execute_rule(self, rule: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """Execute a single rule on a dataset.
        
        Args:
            rule: Rule to execute
            df: DataFrame to validate
            
        Returns:
            Dictionary containing execution result
        """
        try:
            # Get rule execution function based on source
            execution_fn = self._get_execution_function(rule["source"])
            if not execution_fn:
                raise ValueError(f"Unsupported rule source: {rule['source']}")
            
            # Execute rule
            start_time = datetime.datetime.now()
            result = await execution_fn(rule, df)
            end_time = datetime.datetime.now()
            
            # Add execution meta
            execution_time = (end_time - start_time).total_seconds()
            result.update({
                "rule_id": rule["id"],
                "name": rule["name"],
                "source": rule["source"],
                "execution_time": execution_time
            })
            
            # Log execution
            await self._log_rule_execution(
                rule["id"],
                {
                    "success": result["success"],
                    "message": result.get("message", ""),
                    "execution_meta": {
                        "execution_time": execution_time,
                        "rows_processed": len(df),
                        "memory_usage": df.memory_usage(deep=True).sum(),
                        **result.get("meta", {})
                    }
                }
            )
            
            return result
            
        except Exception as e:
            error_result = {
                "rule_id": rule["id"],
                "name": rule["name"],
                "source": rule["source"],
                "success": False,
                "error": str(e)
            }
            
            # Log error
            await self._log_rule_execution(
                rule["id"],
                {
                    "success": False,
                    "message": str(e),
                    "execution_meta": {"error": True}
                }
            )
            
            return error_result
            
    async def _execute_python_rule(self, rule: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """
        Execute a manual Python rule. The rule's 'condition' should be a valid Python expression or code block.
        Returns a dict with success, message, and meta.
        """
        try:
            # Prepare safe context
            condition = rule["condition"]
            context = {
                "df": df,
                "pd": pd,
                "np": np,
                "re": re,
                "datetime": datetime
            }
            # Build a function from the condition
            fn_code = (
                "def validate(df):\n"
                "    try:\n"
                f"        {condition}\n"
                "    except Exception as e:\n"
                "        return False, str(e)\n"
                "    return True, 'Rule validation passed'"
            )
            local_env = {}
            exec(fn_code, context, local_env)
            success, message = local_env["validate"](df)
            affected_rows = []
            if isinstance(success, pd.Series):
                affected_rows = df[~success].index.tolist()
                success = success.all()
            return {
                "success": bool(success),
                "message": message if not success else "Rule validation passed",
                "meta": {
                    "affected_rows": affected_rows[:10],  # Limit number of rows returned
                    "total_affected": len(affected_rows)
                }
            }
        except Exception as e:
            logger.error(f"Error executing Python rule: {str(e)}")
            return {
                "success": False,
                "message": f"Error executing rule: {str(e)}",
                "meta": {}
            }

    async def _execute_ge_rule(self, rule: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """
        Execute a Great Expectations rule. The rule's 'condition' should be a GE expectation string or config.
        """
        try:
            # Example: condition = 'expect_column_values_to_not_be_null("customer_id")'
            expectation = rule["condition"]
            ge_df = ge.from_pandas(df)
            result = eval(f"ge_df.{expectation}")
            success = result.success if hasattr(result, 'success') else False
            return {
                "success": success,
                "message": "GE rule passed" if success else str(result),
                "meta": {"ge_result": str(result)}
            }
        except Exception as e:
            logger.error(f"Error executing GE rule: {str(e)}")
            return {
                "success": False,
                "message": f"Error executing GE rule: {str(e)}",
                "meta": {}
            }

    async def _execute_pydantic_rule(self, rule: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """
        Execute a Pydantic rule. The rule's 'condition' should be a Pydantic model definition or schema.
        """
        try:
            # This is a placeholder - you should parse the condition and build a model dynamically
            model_def = rule["condition"]
            # For demo: assume model_def is a dict of field types
            Model = create_model('DynamicModel', **model_def)
            errors = []
            for idx, row in df.iterrows():
                try:
                    Model(**row.to_dict())
                except ValidationError as ve:
                    errors.append((idx, str(ve)))
            success = len(errors) == 0
            return {
                "success": success,
                "message": "Pydantic validation passed" if success else f"{len(errors)} rows failed",
                "meta": {"errors": errors[:10], "total_failed": len(errors)}
            }
        except Exception as e:
            logger.error(f"Error executing Pydantic rule: {str(e)}")
            return {
                "success": False,
                "message": f"Error executing Pydantic rule: {str(e)}",
                "meta": {}
            }

    async def _execute_hf_rule(self, rule: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """
        Execute a Hugging Face rule. The rule's 'condition' should be a prompt or label for classification.
        For demo, just simulate a pass/fail.
        """
        try:
            # For demonstration, always pass
            return {
                "success": True,
                "message": "Hugging Face rule executed.",
                "meta": {}
            }
        except Exception as e:
            logger.error(f"Error executing Hugging Face rule: {str(e)}")
            return {
                "success": False,
                "message": f"Error executing Hugging Face rule: {str(e)}",
                "meta": {}
            }

    def _get_execution_function(self, source: str) -> Optional[Callable]:
        """Get the execution function for a rule source.
        
        Args:
            source: Rule source (great_expectations, pydantic, huggingface, manual, ai)
        
        Returns:
            Execution function or None if source is unsupported
        """
        execution_functions = {
            "great_expectations": self._execute_ge_rule,
            "pydantic": self._execute_pydantic_rule,
            "huggingface": self._execute_hf_rule,
            "hf": self._execute_hf_rule,
            "manual": self._execute_python_rule,
            "ai": self._execute_python_rule,
            "python": self._execute_python_rule,
            "validation": self._execute_python_rule,
            "transformation": self._execute_transformation_rule,
            "enrichment": self._execute_enrichment_rule
        }
        
        return execution_functions.get(source)
        
    def _compile_condition(self, condition: str) -> Optional[Callable]:
        """Compile a rule condition into an executable function.
        
        Args:
            condition: Python code string representing the condition
            
        Returns:
            Compiled function or None if compilation fails
        """
        try:
            # Validate condition syntax
            ast.parse(condition)
            
            # Create function code with proper indentation
            fn_code = f"def evaluate(data):\n    return {condition}"
            
            # Create namespace with common modules
            namespace = {}
            globals_dict = {
                're': re,
                'np': np,
                'pd': pd,
                'datetime': datetime
            }
            
            # Execute function definition
            exec(fn_code, globals_dict, namespace)
            
            return namespace['evaluate']
        except Exception as e:
            logger.error(f"Error compiling condition: {str(e)}")
            return None
            
    async def get_rules_for_dataset(self, dataset_id: str, rule_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get rules for a dataset, optionally filtered by rule IDs.
        
        Args:
            dataset_id: ID of the dataset
            rule_ids: Optional list of rule IDs to filter by
            
        Returns:
            List of rule dictionaries
        """
        try:
            # Import here to avoid circular imports
            from api.repositories.business_rules_repository import business_rules_repository as rules_repo
            
            # Get all rules for the dataset
            rules = await rules_repo.get_rules_by_dataset(dataset_id)
            
            # Filter by rule IDs if provided
            if rule_ids:
                rules = [r for r in rules if r["id"] in rule_ids]
                
            # Sort by execution order if available
            rules.sort(key=lambda r: r.get("execution_order", 0))
            
            return rules
        except Exception as e:
            logger.error(f"Error getting rules for dataset {dataset_id}: {str(e)}")
            return []
            
    async def apply_rules_to_dataset(self, dataset_id: str, data: List[Dict[str, Any]], rule_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Apply business rules to a dataset.
        
        Args:
            dataset_id: ID of the dataset
            data: List of data records to apply rules to
            rule_ids: Optional list of rule IDs to apply (if None, all active rules for the dataset are applied)
            
        Returns:
            Dictionary with rule application results
        """
        try:
            # Get rules for the dataset
            rules = await self.get_rules_for_dataset(dataset_id, rule_ids)
            
            # Initialize results
            results = {
                "total_rules": len(rules),
                "passed_rules": 0,
                "failed_rules": 0,
                "total_violations": 0,
                "rule_results": []
            }
            
            # Convert data to DataFrame for rule application
            df = pd.DataFrame(data)
            
            # Apply each rule
            for rule in rules:
                rule_result = await self.apply_rule(rule, df)
                results["rule_results"].append(rule_result)
                
                # Update counters
                if rule_result["violation_count"] > 0:
                    results["failed_rules"] += 1
                    results["total_violations"] += rule_result["violation_count"]
                else:
                    results["passed_rules"] += 1
                    
                # Update rule execution stats
                await self.update_rule_stats(rule["id"], rule_result["violation_count"] == 0)
                
            return results
        except Exception as e:
            logger.error(f"Error applying rules to dataset {dataset_id}: {str(e)}")
            return {
                "total_rules": 0,
                "passed_rules": 0,
                "failed_rules": 0,
                "total_violations": 0,
                "rule_results": [],
                "error": str(e)
            }
            
    async def apply_rule(self, rule: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """Apply a single rule to data.
        
        Args:
            rule: Rule dictionary
            df: DataFrame containing data to apply rule to
            
        Returns:
            Dictionary with rule application results
        """
        try:
            # Get rule information
            rule_id = rule["id"]
            rule_name = rule["name"]
            rule_type = rule.get("rule_type", "validation")
            rule_severity = rule.get("severity", "medium")
            rule_source = rule.get("source", "manual")
            rule_condition = rule["condition"]
            rule_message = rule.get("message", "Rule violation")
            
            # Get execution function based on rule source
            execute_fn = self._get_execution_function(rule_source)
            if not execute_fn:
                execute_fn = self._execute_python_rule
                
            # Execute rule
            execution_result = await execute_fn(rule, df)
            
            # Process violations
            violations = []
            if not execution_result["success"]:
                # Get violation details from execution result
                if "meta" in execution_result and "errors" in execution_result["meta"]:
                    for idx, error in execution_result["meta"]["errors"]:
                        if idx < len(df):
                            violations.append({
                                "row": int(idx),
                                "message": error,
                                "data": df.iloc[idx].to_dict()
                            })
                else:
                    # Generic violation for the whole dataset
                    violations.append({
                        "message": execution_result["message"],
                        "data": None
                    })
            
            # Create rule result
            rule_result = {
                "id": rule_id,
                "name": rule_name,
                "severity": rule_severity,
                "rule_type": rule_type,
                "source": rule_source,
                "model_generated": rule.get("model_generated", False),
                "violation_count": len(violations),
                "violations": violations[:10]  # Limit to first 10 for performance
            }
            
            return rule_result
        except Exception as e:
            logger.error(f"Error applying rule {rule.get('id', 'unknown')}: {str(e)}")
            return {
                "id": rule.get("id", "unknown"),
                "name": rule.get("name", "Unknown Rule"),
                "severity": rule.get("severity", "medium"),
                "rule_type": rule.get("rule_type", "validation"),
                "source": rule.get("source", "manual"),
                "model_generated": rule.get("model_generated", False),
                "violation_count": 1,
                "violations": [{
                    "message": f"Error applying rule: {str(e)}",
                    "data": None
                }]
            }
            
    async def update_rule_stats(self, rule_id: str, success: bool) -> None:
        """Update rule execution statistics.
        
        Args:
            rule_id: ID of the rule
            success: Whether the rule execution was successful
        """
        try:
            # Import here to avoid circular imports
            from api.repositories.business_rules_repository import business_rules_repository as rules_repo
            
            # Get current rule
            rule = await rules_repo.get_rule(rule_id)
            if not rule:
                return
                
            # Update execution count and success rate
            execution_count = rule.get("execution_count", 0) + 1
            success_count = rule.get("success_count", 0) + (1 if success else 0)
            success_rate = success_count / execution_count if execution_count > 0 else 0
            
            # Update rule
            updates = {
                "execution_count": execution_count,
                "success_count": success_count,
                "success_rate": success_rate,
                "last_executed": datetime.utcnow().isoformat()
            }
            
            await rules_repo.update_rule(rule_id, updates)
        except Exception as e:
            logger.error(f"Error updating rule stats for {rule_id}: {str(e)}")
            
    async def validate_data_with_rules(self, dataset_id: str, data: List[Dict[str, Any]], rule_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Validate data against rules before vectorization.
        
        Args:
            dataset_id: ID of the dataset
            data: List of data records to validate
            rule_ids: Optional list of rule IDs to apply (if None, all active validation rules for the dataset are applied)
            
        Returns:
            Dictionary with validation results and filtered data
        """
        try:
            # Get rules for the dataset, filtered by validation type if no specific rule_ids
            rules = await self.get_rules_for_dataset(dataset_id, rule_ids)
            if not rule_ids:
                # If no specific rules requested, filter to validation rules only
                rules = [r for r in rules if r.get("rule_type", "validation") == "validation"]
                
            # Apply rules
            validation_results = await self.apply_rules_to_dataset(dataset_id, data, [r["id"] for r in rules])
            
            # Filter data based on validation results
            filtered_data = data.copy()
            skipped_indices = set()
            
            # Find records that failed critical validation rules
            for rule_result in validation_results["rule_results"]:
                # Skip non-critical rules
                if rule_result["severity"] != "high":
                    continue
                    
                # Get indices of violated records
                for violation in rule_result["violations"]:
                    if "row" in violation:
                        skipped_indices.add(violation["row"])
            
            # Remove skipped records
            if skipped_indices:
                filtered_data = [d for i, d in enumerate(data) if i not in skipped_indices]
                
            return {
                "validation_results": validation_results,
                "filtered_data": filtered_data,
                "skipped_count": len(skipped_indices),
                "original_count": len(data),
                "filtered_count": len(filtered_data)
            }
        except Exception as e:
            logger.error(f"Error validating data for dataset {dataset_id}: {str(e)}")
            return {
                "validation_results": {
                    "total_rules": 0,
                    "passed_rules": 0,
                    "failed_rules": 0,
                    "total_violations": 0,
                    "rule_results": [],
                    "error": str(e)
                },
                "filtered_data": data,
                "skipped_count": 0,
                "original_count": len(data),
                "filtered_count": len(data)
            }
            
    async def _execute_transformation_rule(self, rule: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """Execute a transformation rule.
        
        Args:
            rule: Rule dictionary
            df: DataFrame containing data to transform
            
        Returns:
            Dictionary with transformation results
        """
        try:
            # Compile transformation function
            transform_fn = self._compile_condition(rule["condition"])
            if not transform_fn:
                return {
                    "success": False,
                    "message": "Failed to compile transformation function",
                    "meta": {}
                }
                
            # Apply transformation to each row
            transformed_rows = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    # Apply transformation
                    result = transform_fn(row.to_dict())
                    
                    # Update row with transformation result
                    if isinstance(result, dict):
                        for k, v in result.items():
                            df.at[idx, k] = v
                        transformed_rows += 1
                except Exception as e:
                    errors.append((idx, str(e)))
                    
            return {
                "success": len(errors) == 0,
                "message": f"Transformed {transformed_rows} rows with {len(errors)} errors",
                "meta": {"errors": errors, "transformed_rows": transformed_rows}
            }
        except Exception as e:
            logger.error(f"Error executing transformation rule: {str(e)}")
            return {
                "success": False,
                "message": f"Error executing transformation rule: {str(e)}",
                "meta": {}
            }
            
    async def _execute_enrichment_rule(self, rule: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """Execute an enrichment rule.
        
        Args:
            rule: Rule dictionary
            df: DataFrame containing data to enrich
            
        Returns:
            Dictionary with enrichment results
        """
        try:
            # Compile enrichment function
            enrich_fn = self._compile_condition(rule["condition"])
            if not enrich_fn:
                return {
                    "success": False,
                    "message": "Failed to compile enrichment function",
                    "meta": {}
                }
                
            # Apply enrichment to each row
            enriched_rows = 0
            errors = []
            
            # Get target field from rule action
            target_field = rule.get("action", "")
            if not target_field:
                return {
                    "success": False,
                    "message": "No target field specified in rule action",
                    "meta": {}
                }
                
            for idx, row in df.iterrows():
                try:
                    # Apply enrichment
                    result = enrich_fn(row.to_dict())
                    
                    # Add new field with enrichment result
                    df.at[idx, target_field] = result
                    enriched_rows += 1
                except Exception as e:
                    errors.append((idx, str(e)))
                    
            return {
                "success": len(errors) == 0,
                "message": f"Enriched {enriched_rows} rows with {len(errors)} errors",
                "meta": {"errors": errors, "enriched_rows": enriched_rows}
            }
        except Exception as e:
            logger.error(f"Error executing enrichment rule: {str(e)}")
            return {
                "success": False,
                "message": f"Error executing enrichment rule: {str(e)}",
                "meta": {}
            }