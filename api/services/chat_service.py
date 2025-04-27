"""
Chat Service Module

This module provides services for AI chat functionality.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import openai
from uuid import uuid4
from transformers import pipeline

from api.config.settings import get_settings
from api.repositories.chat_repository import ChatRepository
from api.repositories.dataset_repository import DatasetRepository
from api.services.vector_store import VectorStoreService

# Initialize repositories and services
chat_repo = ChatRepository()
dataset_repo = DatasetRepository()
vector_store = VectorStoreService()

# Initialize QA model
qa_model = pipeline("question-answering", model="deepset/roberta-base-squad2")

# Get settings
settings = get_settings()
logger = logging.getLogger(__name__)

# Configure OpenAI if API key is available
if settings.OPENAI_API_KEY:
    openai.api_key = settings.OPENAI_API_KEY

async def get_chat_sessions(user_id: int) -> List[Dict[str, Any]]:
    """
    Get all chat sessions for a user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        List of chat sessions
    """
    try:
        return await chat_repo.get_user_sessions(user_id)
    except Exception as e:
        logger.error(f"Error getting chat sessions: {str(e)}")
        raise

async def get_chat_session(session_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific chat session.
    
    Args:
        session_id: ID of the chat session
        user_id: ID of the user
        
    Returns:
        Chat session data if found, None otherwise
    """
    try:
        session = await chat_repo.get_session(session_id)
        if not session or session['user_id'] != user_id:
            return None
        return session
    except Exception as e:
        logger.error(f"Error getting chat session: {str(e)}")
        raise

async def create_chat_session(title: str, user_id: int) -> Dict[str, Any]:
    """
    Create a new chat session.
    
    Args:
        title: Title of the chat session
        user_id: ID of the user
        
    Returns:
        Created chat session data
    """
    try:
        session_id = str(uuid4())
        session = {
            'id': session_id,
            'title': title,
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'messages': []
        }
        await chat_repo.create_session(session)
        return session
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        raise

async def delete_chat_session(session_id: str, user_id: int) -> None:
    """
    Delete a chat session.
    
    Args:
        session_id: ID of the chat session to delete
        user_id: ID of the user
    """
    try:
        session = await chat_repo.get_session(session_id)
        if not session or session['user_id'] != user_id:
            raise ValueError("Chat session not found or unauthorized")
        await chat_repo.delete_session(session_id)
    except Exception as e:
        logger.error(f"Error deleting chat session: {str(e)}")
        raise

async def send_message(session_id: str, message: str, context: Optional[Dict[str, Any]], user_id: int) -> Dict[str, Any]:
    """
    Send a message and get AI completion.
    
    Args:
        session_id: ID of the chat session
        message: User's message
        context: Optional context for the message
        user_id: ID of the user
        
    Returns:
        AI response message
    """
    try:
        # Verify session exists and user has access
        session = await chat_repo.get_session(session_id)
        if not session or session['user_id'] != user_id:
            raise ValueError("Chat session not found or unauthorized")
        
        # Create message
        user_message = {
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        }
        
        # Get relevant context from vector store
        context_results = await vector_store.search_similar_data(
            query=message,
            limit=5  # Get top 5 relevant items
        )
        
        # Add context to system message
        messages = []
        system_message = "You are an AI assistant helping with data analysis."
        
        if context and context.get('dataset_id'):
            dataset = await dataset_repo.get_dataset(context['dataset_id'])
            if dataset:
                system_message += f" You are working with the dataset '{dataset.name}'"
                if context.get('analysis_type'):
                    system_message += f" performing {context['analysis_type']} analysis"
        
        if context_results:
            context_text = "\n".join([result["text_content"] for result in context_results])
            system_message += f"\n\nRelevant context:\n{context_text}"
        
        messages.append({
            'role': 'system',
            'content': system_message
        })
        
        # Add previous messages for context
        messages.extend(session['messages'][-5:])  # Last 5 messages for context
        messages.append(user_message)
        
        # Get AI completion
        if settings.OPENAI_API_KEY:
            # Use GPT-4 if available
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[{'role': m['role'], 'content': m['content']} for m in messages],
                temperature=0.7,
                max_tokens=2000
            )
            answer = response.choices[0].message.content
        else:
            # Fallback to local QA model
            answer = qa_model(
                question=message,
                context=system_message
            )["answer"]
        
        # Create assistant message
        assistant_message = {
            'role': 'assistant',
            'content': answer,
            'timestamp': datetime.now().isoformat()
        }
        
        # Update session with new messages
        session['messages'].append(user_message)
        session['messages'].append(assistant_message)
        session['updated_at'] = datetime.now().isoformat()
        await chat_repo.update_session(session_id, session)
        
        return assistant_message
        
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        raise
