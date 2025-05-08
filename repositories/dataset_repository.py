import warnings
from typing import Optional, Dict, Any
from datetime import datetime
from models.dataset import Dataset, DatasetCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import Session

# Display deprecation warning
warnings.warn(
    "This module is deprecated. Use api.repositories.dataset_repository instead.",
    DeprecationWarning,
    stacklevel=2
)

class DatasetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_dataset(
        self,
        dataset: DatasetCreate,
        user_id: Optional[int] = None,
        file_path: Optional[str] = None
    ) -> Dataset:
        """Create a new dataset record."""
        db_dataset = Dataset(
            name=dataset.name,
            description=dataset.description,
            file_type=dataset.file_type,
            source_type=dataset.source_type,
            source_info=dataset.source_info,
            status=dataset.status,
            file_path=file_path,
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.session.add(db_dataset)
        await self.session.commit()
        await self.session.refresh(db_dataset)
        
        return db_dataset

    async def get_dataset(self, dataset_id: int) -> Optional[Dataset]:
        """Get a dataset by ID."""
        result = await self.session.execute(
            select(Dataset).where(Dataset.id == dataset_id)
        )
        return result.scalar_one_or_none()

    async def update_dataset(
        self,
        dataset_id: int,
        update_data: Dict[str, Any]
    ) -> Optional[Dataset]:
        """Update a dataset record."""
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        # Update the dataset
        await self.session.execute(
            update(Dataset)
            .where(Dataset.id == dataset_id)
            .values(**update_data)
        )
        await self.session.commit()
        
        # Return updated dataset
        return await self.get_dataset(dataset_id)

    async def list_datasets(
        self,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[Dataset]:
        """List datasets with optional user filter."""
        query = select(Dataset)
        
        if user_id is not None:
            query = query.where(Dataset.user_id == user_id)
        
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def delete_dataset(self, dataset_id: int) -> bool:
        """Delete a dataset record."""
        dataset = await self.get_dataset(dataset_id)
        if dataset:
            await self.session.delete(dataset)
            await self.session.commit()
            return True
        return False

def get_dataset_repository(session: AsyncSession) -> DatasetRepository:
    """Get a dataset repository instance."""
    return DatasetRepository(session) 