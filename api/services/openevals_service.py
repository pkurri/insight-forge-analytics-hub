import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
import uuid
import asyncio
import time
from enum import Enum

# Import other services
from .ai_agent_service import get_agent_response
from .business_rules_service import BusinessRulesService
from .conversation_memory import conversation_memory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Evaluation types
class EvalType(str, Enum):
    DATA_QUALITY = "data_quality"
    BUSINESS_RULE = "business_rule"
    MODEL_PERFORMANCE = "model_performance"
    CONSISTENCY = "consistency"
    ANOMALY = "anomaly"
    VALIDITY = "validity"
    CONVERSATION = "conversation"
    USER_FEEDBACK = "user_feedback"
    INSIGHT_QUALITY = "insight_quality"

# Result status
class EvalStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    ERROR = "error"
    EXCELLENT = "excellent"
    IMPROVEMENT_NEEDED = "improvement_needed"

# Initialize business rules service
business_rules_service = BusinessRulesService()

class OpenEvalsService:
    """
    OpenEvals Service for evaluating and validating data and AI-generated content
    This service integrates with the business rules service and AI agents to provide
    evaluation and self-correction capabilities.
    """
    
    def __init__(self):
        """
        Initialize the OpenEvals service
        """
        self.evaluation_history = {}
        self.eval_logs_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'evaluation_logs')
        os.makedirs(self.eval_logs_path, exist_ok=True)
    
    async def evaluate_business_rules(self, dataset_id: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluate and validate business rules against a dataset
        
        Args:
            dataset_id: ID of the dataset
            df: DataFrame to evaluate
            
        Returns:
            Dictionary with evaluation results
        """
        # Create unique evaluation ID
        eval_id = str(uuid.uuid4())
        
        try:
            # Execute existing business rules
            rule_execution = await business_rules_service.execute_rules(dataset_id, df)
            
            # Create evaluation log entry
            evaluation = {
                "id": eval_id,
                "dataset_id": dataset_id,
                "type": EvalType.BUSINESS_RULE,
                "timestamp": datetime.now().isoformat(),
                "status": EvalStatus.PASS,
                "rules_executed": rule_execution.get("total_rules", 0),
                "rules_passed": rule_execution.get("passed_rules", 0),
                "rules_failed": rule_execution.get("failed_rules", 0),
                "execution_time": rule_execution.get("execution_time", 0),
                "results": rule_execution.get("results", []),
                "ds_dataset_metadata": {
                    "rows": len(df),
                    "columns": len(df.columns),
                }
            }
            
            # Determine overall status
            if rule_execution.get("failed_rules", 0) > 0:
                if any(r.get("severity") == "high" for r in rule_execution.get("results", []) if not r.get("success")):
                    evaluation["status"] = EvalStatus.FAIL
                else:
                    evaluation["status"] = EvalStatus.WARNING
            
            # Store evaluation history
            self.evaluation_history[eval_id] = evaluation
            
            # Save evaluation log
            self._save_evaluation_log(evaluation)
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating business rules: {str(e)}")
            
            # Create error evaluation
            evaluation = {
                "id": eval_id,
                "dataset_id": dataset_id,
                "type": EvalType.BUSINESS_RULE,
                "timestamp": datetime.now().isoformat(),
                "status": EvalStatus.ERROR,
                "error": str(e),
                "ds_dataset_metadata": {
                    "rows": len(df) if df is not None else 0,
                    "columns": len(df.columns) if df is not None else 0,
                }
            }
            
            # Store evaluation history
            self.evaluation_history[eval_id] = evaluation
            
            # Save evaluation log
            self._save_evaluation_log(evaluation)
            
            return evaluation
    
    async def evaluate_data_quality(self, dataset_id: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluate data quality for a dataset
        
        Args:
            dataset_id: ID of the dataset
            df: DataFrame to evaluate
            
        Returns:
            Dictionary with data quality evaluation results
        """
        # Create unique evaluation ID
        eval_id = str(uuid.uuid4())
        
        try:
            # Calculate basic data quality metrics
            dq_metrics = {
                "completeness": {},
                "uniqueness": {},
                "consistency": {},
                "accuracy": {}
            }
            
            # Completeness (missing values)
            missing_counts = df.isna().sum()
            for column in df.columns:
                missing = missing_counts[column]
                missing_pct = (missing / len(df)) * 100 if len(df) > 0 else 0
                dq_metrics["completeness"][column] = {
                    "missing_count": int(missing),
                    "missing_percentage": float(missing_pct),
                    "score": float(100 - missing_pct)  # Higher is better
                }
            
            # Uniqueness
            for column in df.columns:
                unique_count = df[column].nunique()
                unique_pct = (unique_count / len(df)) * 100 if len(df) > 0 else 0
                dq_metrics["uniqueness"][column] = {
                    "unique_count": int(unique_count),
                    "unique_percentage": float(unique_pct),
                    "is_unique": unique_count == len(df)
                }
            
            # Overall data quality score (simple average)
            completeness_scores = [metric["score"] for metric in dq_metrics["completeness"].values()]
            overall_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
            
            # Create evaluation
            evaluation = {
                "id": eval_id,
                "dataset_id": dataset_id,
                "type": EvalType.DATA_QUALITY,
                "timestamp": datetime.now().isoformat(),
                "metrics": dq_metrics,
                "overall_score": float(overall_completeness),
                "status": EvalStatus.PASS if overall_completeness >= 90 else EvalStatus.WARNING,
                "ds_dataset_metadata": {
                    "rows": len(df),
                    "columns": len(df.columns),
                }
            }
            
            # Store evaluation history
            self.evaluation_history[eval_id] = evaluation
            
            # Save evaluation log
            self._save_evaluation_log(evaluation)
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating data quality: {str(e)}")
            
            # Create error evaluation
            evaluation = {
                "id": eval_id,
                "dataset_id": dataset_id,
                "type": EvalType.DATA_QUALITY,
                "timestamp": datetime.now().isoformat(),
                "status": EvalStatus.ERROR,
                "error": str(e),
                "ds_dataset_metadata": {
                    "rows": len(df) if df is not None else 0,
                    "columns": len(df.columns) if df is not None else 0,
                }
            }
            
            # Store evaluation history
            self.evaluation_history[eval_id] = evaluation
            
            # Save evaluation log
            self._save_evaluation_log(evaluation)
            
            return evaluation
    
    async def generate_business_rules_with_openeval(self, 
                                                   dataset_id: str, 
                                                   column_dataset_metadata: Dict[str, Any],
                                                   data_sample: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Generate business rules with OpenEvals for self-correction
        
        This function uses the AI agent to generate business rules and then
        evaluates those rules against sample data for self-correction.
        
        Args:
            dataset_id: ID of the dataset
            column_dataset_metadata: Column dataset_metadata for rule generation
            data_sample: Optional sample data for evaluation
            
        Returns:
            Dictionary with generated and validated rules
        """
        start_time = time.time()
        
        try:
            # Step 1: Generate initial rules using AI
            initial_rules = await business_rules_service.generate_ai_rules(dataset_id, column_dataset_metadata)
            
            # If no sample data, return the initial rules
            if data_sample is None or len(initial_rules.get("rules", [])) == 0:
                return initial_rules
            
            # Step 2: Test the generated rules against sample data
            rules_to_test = []
            for rule in initial_rules.get("rules", []):
                # Format rule for testing
                rule_data = {
                    "name": rule.get("name"),
                    "description": rule.get("description"),
                    "condition": rule.get("condition"),
                    "severity": rule.get("severity", "medium"),
                    "message": rule.get("message"),
                    "source": "ai",
                    "dataset_id": dataset_id,
                    "rules_dataset_metadata": rule.get("rules_dataset_metadata", {})
                }
                
                # Add to test list
                rules_to_test.append(rule_data)
            
            # Step 3: Execute rules against sample data
            test_results = []
            failed_rules = []
            
            for rule in rules_to_test:
                # Execute rule
                result = await business_rules_service._execute_python_rule(rule, data_sample)
                
                # Add test result
                test_results.append({
                    "rule": rule,
                    "result": result
                })
                
                # Track failed rules
                if not result.get("success"):
                    failed_rules.append({
                        "rule": rule,
                        "error": result.get("message", "Unknown error"),
                        "rules_dataset_metadata": result.get("rules_dataset_metadata", {})
                    })
            
            # Step 4: Fix failed rules using AI
            corrected_rules = []
            
            if failed_rules:
                for failed_rule in failed_rules:
                    # Get rule details
                    rule = failed_rule["rule"]
                    error = failed_rule["error"]
                    
                    # Create context for rule correction
                    rule_context = {
                        "rule": rule,
                        "error": error,
                        "column_dataset_metadata": column_dataset_metadata,
                        "data_sample": data_sample.head(5).to_dict() if data_sample is not None else None
                    }
                    
                    # Format AI prompt for rule correction
                    correction_query = f"""Fix the following business rule that failed during validation:
                    Rule Name: {rule.get('name')}
                    Rule Description: {rule.get('description')}
                    Rule Condition: {rule.get('condition')}
                    Error: {error}
                    
                    Please provide a corrected version of the rule condition that will work properly.
                    Return only the corrected Python condition code without any explanation."""
                    
                    # Get AI response
                    correction_response = await get_agent_response(
                        query=correction_query,
                        agent_type="data_analyst",
                        context={"system_prompt_addition": "You are a business rules expert. Your task is to fix Python code for business rules that failed validation."},
                    )
                    
                    # Extract corrected condition
                    if correction_response.get("success") and correction_response.get("answer"):
                        corrected_condition = correction_response["answer"].strip()
                        
                        # Create corrected rule
                        corrected_rule = rule.copy()
                        corrected_rule["condition"] = corrected_condition
                        corrected_rule['rules_dataset_metadata']["corrected"] = True
                        corrected_rule['rules_dataset_metadata']["original_condition"] = rule["condition"] 
                        
                        # Test corrected rule
                        test_result = await business_rules_service._execute_python_rule(corrected_rule, data_sample)
                        
                        if test_result.get("success"):
                            # Rule successfully corrected
                            corrected_rules.append({
                                "original_rule": rule,
                                "corrected_rule": corrected_rule,
                                "test_result": test_result
                            })
            
            # Step 5: Compile final results
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "dataset_id": dataset_id,
                "initial_rules_count": len(initial_rules.get("rules", [])),
                "failed_rules_count": len(failed_rules),
                "corrected_rules_count": len(corrected_rules),
                "rules": [
                    # Include successful initial rules
                    *[r["rule"] for r in test_results if r["result"].get("success")],
                    # Include corrected rules
                    *[r["corrected_rule"] for r in corrected_rules]
                ],
                "failed_rules": failed_rules,
                "execution_time": execution_time
            }
            
        except Exception as e:
            logger.error(f"Error generating business rules with OpenEval: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "dataset_id": dataset_id,
                "execution_time": time.time() - start_time
            }
    
    async def evaluate_agent_response(self, query: str, response: str, facts: List[Dict[str, Any]] = None, conversation_id: str = None, message_id: str = None) -> Dict[str, Any]:
        """
        Evaluate an AI agent's response for accuracy and consistency
        
        Args:
            query: User query that prompted the response
            response: AI generated response to evaluate
            facts: List of facts to check against (optional)
            conversation_id: ID of the conversation (optional)
            message_id: ID of the message being evaluated (optional)
            
        Returns:
            Dictionary with evaluation results
        """
        eval_id = str(uuid.uuid4())
        
        try:
            # Prepare evaluation prompt
            if facts:
                facts_text = "\n".join([f"- {f.get('statement')}" for f in facts])
                evaluation_prompt = f"""Evaluate the following AI response for accuracy and consistency against known facts:
                
User Query: {query}

AI Response: {response}

Known Facts:
{facts_text}

Provide an evaluation with scores (0-100) for:
1. Accuracy: Does the response match known facts?
2. Completeness: Does the response address all aspects of the query?
3. Consistency: Is the response internally consistent?
4. Hallucination: Does the response make up information not in the facts?

Also include a brief explanation for each score.
"""
            else:
                evaluation_prompt = f"""Evaluate the following AI response for quality and coherence:
                
User Query: {query}

AI Response: {response}

Provide an evaluation with scores (0-100) for:
1. Relevance: Does the response address the query?
2. Coherence: Is the response well-structured and logical?
3. Helpfulness: Is the response helpful to the user?
4. Potential Hallucinations: Rate the likelihood of made-up information.

Also include a brief explanation for each score.
"""
            
            # Get evaluation from AI agent
            eval_response = await get_agent_response(
                query=evaluation_prompt,
                agent_type="data_analyst",
                context={"system_prompt_addition": "You are an AI evaluation expert. Your task is to honestly and critically evaluate AI-generated responses."},
            )
            
            # Parse scores from response
            scores = self._extract_scores(eval_response.get("answer", ""))
            
            # Determine overall status
            avg_score = sum(scores.values()) / len(scores) if scores else 0
            status = EvalStatus.PASS
            if avg_score < 70:
                status = EvalStatus.FAIL
            elif avg_score < 85:
                status = EvalStatus.WARNING
            
            # Create evaluation result
            evaluation = {
                "id": eval_id,
                "type": EvalType.CONSISTENCY,
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "response": response,
                "scores": scores,
                "average_score": avg_score,
                "explanation": eval_response.get("answer"),
                "status": status
            }
            
            # Store evaluation history
            self.evaluation_history[eval_id] = evaluation
            
            # Save evaluation log
            self._save_evaluation_log(evaluation)
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating agent response: {str(e)}")
            
            # Create error evaluation
            evaluation = {
                "id": eval_id,
                "type": EvalType.CONSISTENCY,
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "response": response,
                "status": EvalStatus.ERROR,
                "error": str(e)
            }
            
            # Store evaluation history
            self.evaluation_history[eval_id] = evaluation
            
            # Save evaluation log
            self._save_evaluation_log(evaluation)
            
            return evaluation
    
    def _extract_scores(self, evaluation_text: str) -> Dict[str, float]:
        """
        Extract scores from evaluation text
        """
        scores = {}
        
        # Common score labels
        score_labels = [
            "accuracy", "completeness", "consistency", "hallucination",
            "relevance", "coherence", "helpfulness"
        ]
        
        # Look for scores in format "Label: X" or "Label (X/100)"
        for label in score_labels:
            # Try different patterns
            patterns = [
                f"{label}:?\s*(\d+)",  # Label: 85
                f"{label}\s*\(?\s*(\d+)\s*/?\s*100\s*\)?",  # Label (85/100)
                f"{label}\s*score:?\s*(\d+)"  # Label score: 85
            ]
            
            import re
            for pattern in patterns:
                matches = re.findall(pattern, evaluation_text.lower())
                if matches:
                    try:
                        scores[label] = float(matches[0])
                        break
                    except ValueError:
                        continue
        
        return scores
    
    def _save_evaluation_log(self, evaluation: Dict[str, Any]) -> None:
        """
        Save evaluation log to disk
        """
        try:
            # Create log filename
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            eval_type = evaluation.get("type", "unknown")
            eval_id = evaluation.get("id", str(uuid.uuid4()))
            filename = f"{timestamp}_{eval_type}_{eval_id}.json"
            filepath = os.path.join(self.eval_logs_path, filename)
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(evaluation, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving evaluation log: {str(e)}")
    
    async def get_evaluation_history(self, eval_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get evaluation history
        
        Args:
            eval_type: Filter by evaluation type
            limit: Maximum number of evaluations to return
            
        Returns:
            List of evaluations, most recent first
        """
        # Get evaluations
        evaluations = list(self.evaluation_history.values())
        
        # Filter by type if specified
        if eval_type:
            evaluations = [e for e in evaluations if e.get("type") == eval_type]
        
        # Sort by timestamp (newest first)
        evaluations.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        
        # Limit results
        return evaluations[:limit]
    
    async def get_evaluation(self, eval_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific evaluation by ID
        
        Args:
            eval_id: Evaluation ID
            
        Returns:
            Evaluation details or None if not found
        """
        return self.evaluation_history.get(eval_id)
        
    async def evaluate_conversation_insights(self, conversation_id: str, insights: List[str]) -> Dict[str, Any]:
        """
        Evaluate the quality and usefulness of insights generated in a conversation
        
        Args:
            conversation_id: ID of the conversation
            insights: List of insights to evaluate
            
        Returns:
            Dictionary with evaluation results
        """
        eval_id = str(uuid.uuid4())
        
        try:
            # Get conversation history
            conversation = conversation_memory.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # Get messages from conversation (last 10 to keep context manageable)
            messages = conversation.get('messages', [])[-10:]
            
            # Prepare context for evaluation
            conversation_context = ""
            for msg in messages:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                conversation_context += f"[{role}]: {content}\n"
            
            # Format insights for evaluation
            insights_text = "\n".join([f"- {insight}" for insight in insights])
            
            # Create evaluation prompt
            evaluation_prompt = f"""Evaluate the following insights generated from a conversation:

Conversation Context:
{conversation_context}

Insights Generated:
{insights_text}

Provide an evaluation with scores (0-100) for:
1. Relevance: How relevant are the insights to the conversation context?
2. Novelty: Do the insights provide new information or perspectives?
3. Accuracy: Are the insights factually accurate based on the conversation?
4. Actionability: Can the insights be used to take meaningful action?
5. Clarity: Are the insights clearly expressed and understandable?

For each score, include a brief explanation. Also provide suggestions for improving the insights."""
            
            # Get evaluation from AI agent
            eval_response = await get_agent_response(
                query=evaluation_prompt,
                agent_type="data_analyst",
                context={"system_prompt_addition": "You are an insights evaluation expert. Your task is to critically evaluate insights generated from conversations."},
            )
            
            # Parse scores from response
            scores = self._extract_scores(eval_response.get("answer", ""))
            
            # Extract improvement suggestions (simple implementation)
            suggestions = []
            for line in eval_response.get("answer", "").split("\n"):
                if "suggestion" in line.lower() or "improve" in line.lower() or "could be" in line.lower():
                    suggestions.append(line.strip())
            
            # Determine overall quality score
            avg_score = sum(scores.values()) / len(scores) if scores else 0
            
            # Determine status
            status = EvalStatus.PASS
            if avg_score >= 85:
                status = EvalStatus.EXCELLENT
            elif avg_score < 70:
                status = EvalStatus.IMPROVEMENT_NEEDED
            
            # Create evaluation result
            evaluation = {
                "id": eval_id,
                "type": EvalType.INSIGHT_QUALITY,
                "timestamp": datetime.now().isoformat(),
                "conversation_id": conversation_id,
                "insights": insights,
                "scores": scores,
                "average_score": avg_score,
                "explanation": eval_response.get("answer"),
                "improvement_suggestions": suggestions,
                "status": status
            }
            
            # Store evaluation history
            self.evaluation_history[eval_id] = evaluation
            
            # Save evaluation log
            self._save_evaluation_log(evaluation)
            
            return evaluation
        
        except Exception as e:
            logger.error(f"Error evaluating conversation insights: {str(e)}")
            
            # Create error evaluation
            evaluation = {
                "id": eval_id,
                "type": EvalType.INSIGHT_QUALITY,
                "timestamp": datetime.now().isoformat(),
                "conversation_id": conversation_id,
                "status": EvalStatus.ERROR,
                "error": str(e)
            }
            
            # Store evaluation history
            self.evaluation_history[eval_id] = evaluation
            
            # Save evaluation log
            self._save_evaluation_log(evaluation)
            
            return evaluation
    
    async def get_improved_response(self, query: str, initial_response: str, conversation_id: str = None, evaluation: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate an improved response based on evaluation feedback
        
        Args:
            query: User query that prompted the initial response
            initial_response: Original AI response to improve
            conversation_id: ID of the conversation (optional)
            evaluation: Evaluation data (optional, will be generated if not provided)
            
        Returns:
            Dictionary with improved response
        """
        try:
            # Get evaluation if not provided
            if not evaluation:
                evaluation = await self.evaluate_agent_response(query, initial_response, conversation_id=conversation_id)
            
            # Get conversation context if conversation_id provided
            conversation_context = ""
            learning_context = {}
            
            if conversation_id:
                # Get conversation from memory
                conversation = conversation_memory.get_conversation(conversation_id)
                if conversation:
                    # Get last few messages for context
                    messages = conversation.get('messages', [])[-5:]  # Last 5 messages
                    for msg in messages:
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')
                        conversation_context += f"[{role}]: {content}\n"
                    
                    # Get learning context
                    metrics = list(evaluation.get("scores", {}).keys())
                    learning_context = conversation_memory.get_learning_context(query, metrics)
            
            # Prepare improvement prompt
            scores = evaluation.get("scores", {})
            explanation = evaluation.get("explanation", "")
            
            # Format scores for prompt
            scores_text = ""
            for metric, score in scores.items():
                scores_text += f"- {metric.capitalize()}: {score}/100\n"
            
            # Format learning guidance if available
            guidance = ""
            if learning_context and "guidance" in learning_context:
                guidance = f"\n\n{learning_context['guidance']}"
            
            improvement_prompt = f"""I need to improve the following response to a user query.

User Query: {query}

Original Response: {initial_response}

Evaluation Feedback:
{explanation}

Scores:
{scores_text}{guidance}

Please provide an improved version of the response that addresses the feedback and maintains the core information. Your response should ONLY include the improved response text without any explanations or meta-commentary."""
            
            # Get improved response from AI agent
            improved_response = await get_agent_response(
                query=improvement_prompt,
                agent_type="data_analyst",
                context={"system_prompt_addition": "You are an expert at improving AI responses based on evaluation feedback. Generate only the improved response without any explanations."},
            )
            
            # Extract improved response text
            improved_text = improved_response.get("answer", "")
            
            # Re-evaluate improved response
            re_evaluation = await self.evaluate_agent_response(query, improved_text, conversation_id=conversation_id)
            
            return {
                "success": True,
                "original_response": initial_response,
                "improved_response": improved_text,
                "original_evaluation": evaluation,
                "improved_evaluation": re_evaluation,
                "improvement_delta": {
                    "average": re_evaluation.get("average_score", 0) - evaluation.get("average_score", 0),
                    "scores": {
                        metric: re_evaluation.get("scores", {}).get(metric, 0) - score
                        for metric, score in evaluation.get("scores", {}).items()
                        if metric in re_evaluation.get("scores", {})
                    }
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting improved response: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "original_response": initial_response
            }
    
    async def process_continuous_learning(self, conversation_id: str, message_id: str, user_feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user feedback and add to continuous learning system
        
        Args:
            conversation_id: ID of the conversation
            message_id: ID of the message receiving feedback
            user_feedback: Feedback data with format:
                {
                    "rating": 1-5 star rating,
                    "feedback_text": Optional text feedback,
                    "improvement_areas": Optional list of areas for improvement,
                    "tags": Optional list of feedback tags
                }
                
        Returns:
            Dictionary with processing results
        """
        try:
            # Get conversation
            conversation = conversation_memory.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # Find the message
            message = None
            for msg in conversation.get('messages', []):
                if msg.get('id') == message_id:
                    message = msg
                    break
            
            if not message:
                raise ValueError(f"Message {message_id} not found")
            
            # Create evaluation ID
            eval_id = str(uuid.uuid4())
            
            # Process rating
            rating = user_feedback.get("rating", 3)
            feedback_text = user_feedback.get("feedback_text", "")
            improvement_areas = user_feedback.get("improvement_areas", [])
            tags = user_feedback.get("tags", [])
            
            # Map rating to score (1-5 to 0-100)
            score = (rating - 1) * 25  # 1->0, 2->25, 3->50, 4->75, 5->100
            
            # Map rating to status
            status = EvalStatus.PASS
            if rating >= 4:
                status = EvalStatus.EXCELLENT
            elif rating <= 2:
                status = EvalStatus.IMPROVEMENT_NEEDED
            
            # Create evaluation
            evaluation = {
                "id": eval_id,
                "type": EvalType.USER_FEEDBACK,
                "timestamp": datetime.now().isoformat(),
                "conversation_id": conversation_id,
                "message_id": message_id,
                "message_content": message.get("content", ""),
                "user_feedback": user_feedback,
                "scores": {
                    "user_satisfaction": score
                },
                "average_score": score,
                "status": status,
                "tags": tags
            }
            
            # Store evaluation history
            self.evaluation_history[eval_id] = evaluation
            
            # Save evaluation log
            self._save_evaluation_log(evaluation)
            
            # Add to conversation memory
            conversation_memory.add_evaluation(conversation_id, message_id, evaluation)
            
            # For low ratings, automatically generate an improved response
            improved_response = None
            if rating <= 3 and message.get("role") == "assistant":
                # Find the query that prompted this response
                query = conversation_memory._find_query_for_response(conversation_id, message_id)
                
                if query:
                    # Generate improved response
                    improvement_result = await self.get_improved_response(
                        query=query,
                        initial_response=message.get("content", ""),
                        conversation_id=conversation_id,
                        evaluation={
                            "scores": {"user_satisfaction": score},
                            "explanation": feedback_text or f"User rated this response {rating}/5 stars. Improvement areas: {', '.join(improvement_areas)}"
                        }
                    )
                    
                    if improvement_result.get("success"):
                        improved_response = improvement_result.get("improved_response")
            
            return {
                "success": True,
                "evaluation_id": eval_id,
                "status": status,
                "improved_response": improved_response,
                "message": "Feedback processed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error processing user feedback: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Create singleton instance
openevals_service = OpenEvalsService()
