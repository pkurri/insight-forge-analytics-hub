"""
Suggestions Repository Module

This module provides database operations for suggestions.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import asyncpg
from uuid import uuid4

from api.config import get_db_config
from models.suggestion import SuggestionModel, SuggestionStatus, SuggestionType

logger = logging.getLogger(__name__)

class SuggestionsRepository:
    def __init__(self):
        self.pool = None
        
    async def initialize(self):
        """Initialize the database connection pool"""
        if self.pool is None:
            try:
                db_config = get_db_config()
                self.pool = await asyncpg.create_pool(**db_config)
                logger.info("Suggestions repository initialized with asyncpg connection pool")
            except Exception as e:
                logger.error(f"Failed to initialize suggestions repository: {str(e)}")
                raise
    
    async def create_suggestion(self, suggestion: SuggestionModel) -> str:
        """Create a new suggestion in the database
        
        Args:
            suggestion: The suggestion model to create
            
        Returns:
            The ID of the created suggestion
        """
        await self.initialize()
        
        suggestion_id = str(uuid4())
        created_at = datetime.utcnow()
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO suggestions (
                    id, dataset_id, title, description, type, status, 
                    confidence_score, metadata, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $9)
                """,
                suggestion_id,
                suggestion.dataset_id,
                suggestion.title,
                suggestion.description,
                suggestion.type.value,
                suggestion.status.value,
                suggestion.confidence_score,
                json.dumps(suggestion.metadata or {}),
                created_at
            )
        
        return suggestion_id
    
    async def get_suggestions_by_dataset(self, dataset_id: int, limit: int = 50) -> List[SuggestionModel]:
        """Get suggestions for a specific dataset
        
        Args:
            dataset_id: The ID of the dataset
            limit: Maximum number of suggestions to return
            
        Returns:
            List of suggestion models
        """
        await self.initialize()
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, dataset_id, title, description, type, status, 
                       confidence_score, metadata, created_at, updated_at
                FROM suggestions
                WHERE dataset_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                dataset_id,
                limit
            )
        
        return [
            SuggestionModel(
                id=row['id'],
                dataset_id=row['dataset_id'],
                title=row['title'],
                description=row['description'],
                type=SuggestionType(row['type']),
                status=SuggestionStatus(row['status']),
                confidence_score=row['confidence_score'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            for row in rows
        ]
    
    async def update_suggestion_status(self, suggestion_id: str, status: SuggestionStatus) -> bool:
        """Update the status of a suggestion
        
        Args:
            suggestion_id: The ID of the suggestion to update
            status: The new status
            
        Returns:
            True if the update was successful, False otherwise
        """
        await self.initialize()
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE suggestions
                SET status = $1, updated_at = $2
                WHERE id = $3
                """,
                status.value,
                datetime.utcnow(),
                suggestion_id
            )
        
        return result == "UPDATE 1"
    
    async def get_suggestion_by_id(self, suggestion_id: str) -> Optional[SuggestionModel]:
        """Get a suggestion by its ID
        
        Args:
            suggestion_id: The ID of the suggestion
            
        Returns:
            The suggestion model if found, None otherwise
        """
        await self.initialize()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, dataset_id, title, description, type, status, 
                       confidence_score, metadata, created_at, updated_at
                FROM suggestions
                WHERE id = $1
                """,
                suggestion_id
            )
        
        if not row:
            return None
        
        return SuggestionModel(
            id=row['id'],
            dataset_id=row['dataset_id'],
            title=row['title'],
            description=row['description'],
            type=SuggestionType(row['type']),
            status=SuggestionStatus(row['status']),
            confidence_score=row['confidence_score'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    async def delete_suggestion(self, suggestion_id: str) -> bool:
        """Delete a suggestion
        
        Args:
            suggestion_id: The ID of the suggestion to delete
            
        Returns:
            True if the deletion was successful, False otherwise
        """
        await self.initialize()
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM suggestions WHERE id = $1",
                suggestion_id
            )
        
        return result == "DELETE 1"
    
    async def get_suggestions_by_type(self, suggestion_type: SuggestionType, limit: int = 50) -> List[SuggestionModel]:
        """Get suggestions by type
        
        Args:
            suggestion_type: The type of suggestions to retrieve
            limit: Maximum number of suggestions to return
            
        Returns:
            List of suggestion models
        """
        await self.initialize()
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, dataset_id, title, description, type, status, 
                       confidence_score, metadata, created_at, updated_at
                FROM suggestions
                WHERE type = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                suggestion_type.value,
                limit
            )
        
        return [
            SuggestionModel(
                id=row['id'],
                dataset_id=row['dataset_id'],
                title=row['title'],
                description=row['description'],
                type=SuggestionType(row['type']),
                status=SuggestionStatus(row['status']),
                confidence_score=row['confidence_score'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            for row in rows
        ]
    
    async def get_recent_suggestions(self, limit: int = 10) -> List[SuggestionModel]:
        """Get the most recent suggestions across all datasets
        
        Args:
            db: Database session
            suggestions: List of suggestion models to create
            
        Returns:
            List of created suggestion database models
        """
        db_suggestions = []
        
        for suggestion in suggestions:
            db_suggestion = Suggestion(
                dataset_id=suggestion.dataset_id,
                type=suggestion.type,
                title=suggestion.title,
                description=suggestion.description,
                content=suggestion.content,
                status=SuggestionStatus.GENERATED,
                confidence_score=suggestion.confidence_score,
                metadata=suggestion.metadata
            )
            db_suggestions.append(db_suggestion)
        
        db.add_all(db_suggestions)
        await db.commit()
        
        for suggestion in db_suggestions:
            await db.refresh(suggestion)
        
        return db_suggestions
    
    async def get_suggestions_by_dataset(
        self, 
        db: AsyncSession, 
        dataset_id: int,
        status: Optional[SuggestionStatus] = None,
        suggestion_type: Optional[SuggestionType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Suggestion]:
        """
        Get suggestions for a specific dataset with optional filters.
        
        Args:
            db: Database session
            dataset_id: Dataset ID to filter by
            status: Optional status filter
            suggestion_type: Optional suggestion type filter
            limit: Maximum number of suggestions to return
            offset: Offset for pagination
            
        Returns:
            List of suggestion database models
        """
        query = select(Suggestion).where(Suggestion.dataset_id == dataset_id)
        
        if status:
            query = query.where(Suggestion.status == status)
            
        if suggestion_type:
            query = query.where(Suggestion.type == suggestion_type)
            
        query = query.order_by(desc(Suggestion.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update_suggestion_status(
        self,
        db: AsyncSession,
        suggestion_id: int,
        status: SuggestionStatus,
        user_id: Optional[int] = None
    ) -> Optional[Suggestion]:
        """
        Update the status of a suggestion.
        
        Args:
            db: Database session
            suggestion_id: ID of the suggestion to update
            status: New status
            user_id: Optional user ID who selected the suggestion
            
        Returns:
            Updated suggestion or None if not found
        """
        update_values = {"status": status, "updated_at": datetime.utcnow()}
        
        if status == SuggestionStatus.SELECTED and user_id:
            update_values.update({
                "selected_at": datetime.utcnow(),
                "user_id": user_id
            })
        
        stmt = (
            update(Suggestion)
            .where(Suggestion.id == suggestion_id)
            .values(**update_values)
            .returning(Suggestion)
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.scalar_one_or_none()
    
    async def get_suggestion_by_id(self, db: AsyncSession, suggestion_id: int) -> Optional[Suggestion]:
        """
        Get a suggestion by its ID.
        
        Args:
            db: Database session
            suggestion_id: ID of the suggestion to retrieve
            
        Returns:
            Suggestion database model or None if not found
        """
        query = select(Suggestion).where(Suggestion.id == suggestion_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def delete_suggestion(self, db: AsyncSession, suggestion_id: int) -> bool:
        """
        Delete a suggestion by its ID.
        
        Args:
            db: Database session
            suggestion_id: ID of the suggestion to delete
            
        Returns:
            True if deleted, False if not found
        """
        suggestion = await self.get_suggestion_by_id(db, suggestion_id)
        
        if suggestion:
            await db.delete(suggestion)
            await db.commit()
            return True
        
        return False
    
    async def expire_old_suggestions(
        self,
        db: AsyncSession,
        dataset_id: int,
        days_threshold: int = 30
    ) -> int:
        """
        Mark old suggestions as expired.
        
        Args:
            db: Database session
            dataset_id: Dataset ID to filter by
            days_threshold: Number of days after which suggestions are considered old
            
        Returns:
            Number of suggestions marked as expired
        """
        import datetime as dt
        
        expiration_date = datetime.utcnow() - dt.timedelta(days=days_threshold)
        
        stmt = (
            update(Suggestion)
            .where(
                and_(
                    Suggestion.dataset_id == dataset_id,
                    Suggestion.created_at < expiration_date,
                    Suggestion.status == SuggestionStatus.GENERATED
                )
            )
            .values(status=SuggestionStatus.EXPIRED)
            .returning(Suggestion.id)
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        expired_ids = result.scalars().all()
        return len(expired_ids)


# Create singleton instance
suggestions_repository = SuggestionsRepository()
