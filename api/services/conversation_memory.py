import os
import json
import logging
import pickle
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationMemory:
    """
    Conversation Memory System for tracking chat history, evaluations, and learning
    Enables AI agent to improve responses based on previous interactions
    """
    
    def __init__(self):
        """
        Initialize the conversation memory system
        """
        self.conversations = {}
        self.user_preferences = {}
        self.learning_patterns = {}
        self.memory_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'conversation_memory')
        os.makedirs(self.memory_path, exist_ok=True)
        
        # Load existing memory if available
        self._load_memory()
    
    def _load_memory(self):
        """
        Load conversation memory from disk
        """
        memory_file = os.path.join(self.memory_path, 'memory.pkl')
        
        if os.path.exists(memory_file):
            try:
                with open(memory_file, 'rb') as f:
                    data = pickle.load(f)
                    self.conversations = data.get('conversations', {})
                    self.user_preferences = data.get('user_preferences', {})
                    self.learning_patterns = data.get('learning_patterns', {})
                logger.info(f"Loaded conversation memory with {len(self.conversations)} conversations")
            except Exception as e:
                logger.error(f"Error loading conversation memory: {str(e)}")
    
    def _save_memory(self):
        """
        Save conversation memory to disk
        """
        memory_file = os.path.join(self.memory_path, 'memory.pkl')
        
        try:
            with open(memory_file, 'wb') as f:
                data = {
                    'conversations': self.conversations,
                    'user_preferences': self.user_preferences,
                    'learning_patterns': self.learning_patterns
                }
                pickle.dump(data, f)
            logger.info("Saved conversation memory")
            return True
        except Exception as e:
            logger.error(f"Error saving conversation memory: {str(e)}")
            return False
    
    def create_conversation(self, user_id: str = None) -> str:
        """
        Create a new conversation and return its ID
        
        Args:
            user_id: Optional user ID to associate with the conversation
            
        Returns:
            Conversation ID
        """
        conversation_id = str(uuid.uuid4())
        
        self.conversations[conversation_id] = {
            'id': conversation_id,
            'user_id': user_id,
            'messages': [],
            'evaluations': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'metadata': {}
        }
        
        # Save memory
        self._save_memory()
        
        return conversation_id
    
    def add_message(self, conversation_id: str, message: Dict[str, Any]) -> bool:
        """
        Add a message to a conversation
        
        Args:
            conversation_id: ID of the conversation
            message: Message to add, with format:
                {
                    'role': 'user' or 'assistant',
                    'content': 'Message content',
                    'timestamp': ISO timestamp (optional),
                    'metadata': Additional metadata (optional)
                }
                
        Returns:
            True if successful, False otherwise
        """
        if conversation_id not in self.conversations:
            return False
        
        # Add timestamp if not provided
        if 'timestamp' not in message:
            message['timestamp'] = datetime.now().isoformat()
        
        # Add message ID if not provided
        if 'id' not in message:
            message['id'] = str(uuid.uuid4())
        
        # Add message to conversation
        self.conversations[conversation_id]['messages'].append(message)
        self.conversations[conversation_id]['updated_at'] = datetime.now().isoformat()
        
        # Save memory (periodically)
        if len(self.conversations[conversation_id]['messages']) % 5 == 0:
            self._save_memory()
        
        return True
    
    def add_evaluation(self, conversation_id: str, message_id: str, evaluation: Dict[str, Any]) -> bool:
        """
        Add an evaluation for a message in a conversation
        
        Args:
            conversation_id: ID of the conversation
            message_id: ID of the message being evaluated
            evaluation: Evaluation data
                
        Returns:
            True if successful, False otherwise
        """
        if conversation_id not in self.conversations:
            return False
        
        # Add timestamp if not provided
        if 'timestamp' not in evaluation:
            evaluation['timestamp'] = datetime.now().isoformat()
        
        # Add evaluation ID if not provided
        if 'id' not in evaluation:
            evaluation['id'] = str(uuid.uuid4())
        
        # Add message ID to evaluation
        evaluation['message_id'] = message_id
        
        # Add evaluation to conversation
        self.conversations[conversation_id]['evaluations'].append(evaluation)
        
        # Process evaluation for learning
        self._process_evaluation_for_learning(conversation_id, message_id, evaluation)
        
        # Save memory
        self._save_memory()
        
        return True
    
    def _process_evaluation_for_learning(self, conversation_id: str, message_id: str, evaluation: Dict[str, Any]):
        """
        Process an evaluation to extract learning patterns
        
        Args:
            conversation_id: ID of the conversation
            message_id: ID of the message being evaluated
            evaluation: Evaluation data
        """
        # Find the message
        message = None
        for msg in self.conversations[conversation_id]['messages']:
            if msg.get('id') == message_id:
                message = msg
                break
        
        if not message or message.get('role') != 'assistant':
            return
        
        # Extract scores
        scores = evaluation.get('scores', {})
        if not scores:
            return
        
        # Extract learning patterns based on scores
        for metric, score in scores.items():
            if metric not in self.learning_patterns:
                self.learning_patterns[metric] = {
                    'high_scoring_examples': [],
                    'low_scoring_examples': []
                }
            
            # Define score thresholds
            if score >= 85:  # High score
                # Add to high scoring examples (limited to 20 examples)
                if len(self.learning_patterns[metric]['high_scoring_examples']) >= 20:
                    self.learning_patterns[metric]['high_scoring_examples'].pop(0)
                
                self.learning_patterns[metric]['high_scoring_examples'].append({
                    'query': self._find_query_for_response(conversation_id, message_id),
                    'response': message.get('content', ''),
                    'score': score,
                    'evaluation': evaluation.get('explanation', '')
                })
            
            elif score <= 60:  # Low score
                # Add to low scoring examples (limited to 20 examples)
                if len(self.learning_patterns[metric]['low_scoring_examples']) >= 20:
                    self.learning_patterns[metric]['low_scoring_examples'].pop(0)
                
                self.learning_patterns[metric]['low_scoring_examples'].append({
                    'query': self._find_query_for_response(conversation_id, message_id),
                    'response': message.get('content', ''),
                    'score': score,
                    'evaluation': evaluation.get('explanation', '')
                })
    
    def _find_query_for_response(self, conversation_id: str, message_id: str) -> str:
        """
        Find the user query that prompted a specific response
        
        Args:
            conversation_id: ID of the conversation
            message_id: ID of the assistant's message
            
        Returns:
            User query or empty string if not found
        """
        messages = self.conversations[conversation_id]['messages']
        assistant_index = None
        
        # Find the assistant message
        for i, msg in enumerate(messages):
            if msg.get('id') == message_id:
                assistant_index = i
                break
        
        if assistant_index is None or assistant_index == 0:
            return ""
        
        # Find the most recent user message before the assistant message
        for i in range(assistant_index - 1, -1, -1):
            if messages[i].get('role') == 'user':
                return messages[i].get('content', '')
        
        return ""
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a conversation by ID
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Conversation data or None if not found
        """
        return self.conversations.get(conversation_id)
    
    def get_learning_context(self, query: str, metrics: List[str] = None) -> Dict[str, Any]:
        """
        Get learning context based on previous evaluations
        
        Args:
            query: User query to get context for
            metrics: List of metrics to prioritize (e.g., 'accuracy', 'helpfulness')
            
        Returns:
            Learning context with examples and guidance
        """
        if not metrics:
            metrics = list(self.learning_patterns.keys())
        
        # Get relevant examples for each metric
        examples = {
            'positive_examples': [],
            'negative_examples': []
        }
        
        for metric in metrics:
            if metric in self.learning_patterns:
                # Add high scoring examples
                for example in self.learning_patterns[metric]['high_scoring_examples'][-3:]:
                    examples['positive_examples'].append({
                        'metric': metric,
                        'query': example.get('query', ''),
                        'response': example.get('response', ''),
                        'score': example.get('score', 0),
                        'feedback': example.get('evaluation', '')
                    })
                
                # Add low scoring examples
                for example in self.learning_patterns[metric]['low_scoring_examples'][-3:]:
                    examples['negative_examples'].append({
                        'metric': metric,
                        'query': example.get('query', ''),
                        'response': example.get('response', ''),
                        'score': example.get('score', 0),
                        'feedback': example.get('evaluation', '')
                    })
        
        # Generate guidance based on examples
        guidance = self._generate_guidance(examples, query)
        
        return {
            'examples': examples,
            'guidance': guidance
        }
    
    def _generate_guidance(self, examples: Dict[str, List[Dict[str, Any]]], query: str) -> str:
        """
        Generate guidance for improving responses based on learning patterns
        
        Args:
            examples: Positive and negative examples
            query: Current user query
            
        Returns:
            Guidance string for improving responses
        """
        guidance = """Based on previous evaluations, please ensure your response:
"""
        
        # Add guidance from positive examples
        if examples['positive_examples']:
            guidance += "\n- DO:"
            positive_patterns = set()
            
            for example in examples['positive_examples']:
                feedback = example.get('feedback', '')
                if feedback:
                    # Extract key positive points (simple heuristic)
                    for line in feedback.split('\n'):
                        if 'good' in line.lower() or 'excellent' in line.lower() or 'strength' in line.lower():
                            positive_patterns.add(line.strip())
            
            for pattern in list(positive_patterns)[:5]:  # Limit to 5 patterns
                guidance += f"\n  - {pattern}"
        
        # Add guidance from negative examples
        if examples['negative_examples']:
            guidance += "\n- DON'T:"
            negative_patterns = set()
            
            for example in examples['negative_examples']:
                feedback = example.get('feedback', '')
                if feedback:
                    # Extract key negative points (simple heuristic)
                    for line in feedback.split('\n'):
                        if 'poor' in line.lower() or 'issue' in line.lower() or 'lacking' in line.lower() or 'improve' in line.lower():
                            negative_patterns.add(line.strip())
            
            for pattern in list(negative_patterns)[:5]:  # Limit to 5 patterns
                guidance += f"\n  - {pattern}"
        
        return guidance
    
    def update_user_preference(self, user_id: str, preference: Dict[str, Any]) -> bool:
        """
        Update or add a user preference
        
        Args:
            user_id: ID of the user
            preference: Preference data with format:
                {
                    'key': 'preference_key',
                    'value': 'preference_value',
                    'metadata': Additional metadata (optional)
                }
                
        Returns:
            True if successful, False otherwise
        """
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        
        key = preference.get('key')
        if not key:
            return False
        
        # Update preference
        self.user_preferences[user_id][key] = {
            'value': preference.get('value'),
            'metadata': preference.get('metadata', {}),
            'updated_at': datetime.now().isoformat()
        }
        
        # Save memory
        self._save_memory()
        
        return True
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get all preferences for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary of user preferences
        """
        return self.user_preferences.get(user_id, {})
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent conversations
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversations, most recent first
        """
        # Convert to list and sort by updated_at
        conversations = list(self.conversations.values())
        conversations.sort(key=lambda c: c.get('updated_at', ''), reverse=True)
        
        # Return limited number of conversations with limited data
        result = []
        for convo in conversations[:limit]:
            result.append({
                'id': convo.get('id'),
                'user_id': convo.get('user_id'),
                'message_count': len(convo.get('messages', [])),
                'evaluation_count': len(convo.get('evaluations', [])),
                'created_at': convo.get('created_at'),
                'updated_at': convo.get('updated_at')
            })
        
        return result

# Create singleton instance
conversation_memory = ConversationMemory()
