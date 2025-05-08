"""
Pipeline Repository Module

This module provides database operations for pipeline runs and steps.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship
from database.db import Base, get_session

from models.pipeline import PipelineStepType, PipelineRunStatus

logger = logging.getLogger(__name__)

class PipelineRun(Base):
    """Database model for pipeline runs."""
    __tablename__ = "pipeline_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, nullable=False, index=True)
    status = Column(String(50), default=PipelineRunStatus.PENDING)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, default=dict)
    
    # Relationship with pipeline steps
    steps = relationship("PipelineStep", back_populates="pipeline_run", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "dataset_id": self.dataset_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata or {}
        }

class PipelineStep(Base):
    """Database model for pipeline steps."""
    __tablename__ = "pipeline_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    pipeline_run_id = Column(Integer, ForeignKey("pipeline_runs.id"), nullable=False)
    step_type = Column(String(50), nullable=False)
    status = Column(String(50), default=PipelineRunStatus.PENDING)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, default=dict)
    error = Column(Text, nullable=True)
    
    # Relationship with pipeline run
    pipeline_run = relationship("PipelineRun", back_populates="steps")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "pipeline_run_id": self.pipeline_run_id,
            "step_type": self.step_type,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata or {},
            "error": self.error
        }

class PipelineRepository:
    """Repository for pipeline operations."""
    
    async def create_pipeline_run(self, dataset_id: int) -> int:
        """
        Create a new pipeline run for a dataset.
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            ID of the created pipeline run
        """
        async with get_session() as session:
            pipeline_run = PipelineRun(
                dataset_id=dataset_id,
                status=PipelineRunStatus.PENDING,
                started_at=datetime.utcnow(),
                metadata={}
            )
            
            session.add(pipeline_run)
            await session.commit()
            await session.refresh(pipeline_run)
            
            return pipeline_run.id
    
    async def get_pipeline_run(self, run_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a pipeline run by ID.
        
        Args:
            run_id: ID of the pipeline run
            
        Returns:
            Pipeline run data or None if not found
        """
        async with get_session() as session:
            result = await session.execute(
                select(PipelineRun).where(PipelineRun.id == run_id)
            )
            
            pipeline_run = result.scalars().first()
            
            if not pipeline_run:
                return None
                
            return pipeline_run.to_dict()
    
    async def get_pipeline_runs_for_dataset(self, dataset_id: int) -> List[Dict[str, Any]]:
        """
        Get all pipeline runs for a dataset.
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            List of pipeline runs
        """
        async with get_session() as session:
            result = await session.execute(
                select(PipelineRun)
                .where(PipelineRun.dataset_id == dataset_id)
                .order_by(PipelineRun.started_at.desc())
            )
            
            pipeline_runs = result.scalars().all()
            
            return [run.to_dict() for run in pipeline_runs]
    
    async def update_pipeline_run_status(
        self, 
        run_id: int, 
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update the status of a pipeline run.
        
        Args:
            run_id: ID of the pipeline run
            status: New status
            metadata: Optional metadata to update
            
        Returns:
            True if successful, False otherwise
        """
        async with get_session() as session:
            result = await session.execute(
                select(PipelineRun).where(PipelineRun.id == run_id)
            )
            
            pipeline_run = result.scalars().first()
            
            if not pipeline_run:
                return False
                
            pipeline_run.status = status
            
            if status in [PipelineRunStatus.COMPLETED, PipelineRunStatus.FAILED]:
                pipeline_run.completed_at = datetime.utcnow()
                
            if metadata:
                if pipeline_run.metadata:
                    # Merge with existing metadata
                    pipeline_run.metadata.update(metadata)
                else:
                    pipeline_run.metadata = metadata
            
            await session.commit()
            
            return True
    
    async def create_pipeline_step(self, run_id: int, step_type: str) -> int:
        """
        Create a new pipeline step for a run.
        
        Args:
            run_id: ID of the pipeline run
            step_type: Type of the step
            
        Returns:
            ID of the created pipeline step
        """
        async with get_session() as session:
            pipeline_step = PipelineStep(
                pipeline_run_id=run_id,
                step_type=step_type,
                status=PipelineRunStatus.PENDING,
                started_at=datetime.utcnow(),
                metadata={}
            )
            
            session.add(pipeline_step)
            await session.commit()
            await session.refresh(pipeline_step)
            
            return pipeline_step.id
    
    async def get_pipeline_step(self, step_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a pipeline step by ID.
        
        Args:
            step_id: ID of the pipeline step
            
        Returns:
            Pipeline step data or None if not found
        """
        async with get_session() as session:
            result = await session.execute(
                select(PipelineStep).where(PipelineStep.id == step_id)
            )
            
            pipeline_step = result.scalars().first()
            
            if not pipeline_step:
                return None
                
            return pipeline_step.to_dict()
    
    async def get_pipeline_steps_for_run(self, run_id: int) -> List[Dict[str, Any]]:
        """
        Get all pipeline steps for a run.
        
        Args:
            run_id: ID of the pipeline run
            
        Returns:
            List of pipeline steps
        """
        async with get_session() as session:
            result = await session.execute(
                select(PipelineStep)
                .where(PipelineStep.pipeline_run_id == run_id)
                .order_by(PipelineStep.started_at)
            )
            
            pipeline_steps = result.scalars().all()
            
            return [step.to_dict() for step in pipeline_steps]
    
    async def update_pipeline_step_status(
        self, 
        step_id: int, 
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        Update the status of a pipeline step.
        
        Args:
            step_id: ID of the pipeline step
            status: New status
            metadata: Optional metadata to update
            error: Optional error message
            
        Returns:
            True if successful, False otherwise
        """
        async with get_session() as session:
            result = await session.execute(
                select(PipelineStep).where(PipelineStep.id == step_id)
            )
            
            pipeline_step = result.scalars().first()
            
            if not pipeline_step:
                return False
                
            pipeline_step.status = status
            
            if status in [PipelineRunStatus.COMPLETED, PipelineRunStatus.FAILED]:
                pipeline_step.completed_at = datetime.utcnow()
                
            if metadata:
                if pipeline_step.metadata:
                    # Merge with existing metadata
                    pipeline_step.metadata.update(metadata)
                else:
                    pipeline_step.metadata = metadata
                    
            if error:
                pipeline_step.error = error
            
            await session.commit()
            
            # If this step completed or failed, update the parent run status if all steps are done
            if status in [PipelineRunStatus.COMPLETED, PipelineRunStatus.FAILED]:
                await self._update_run_status_if_all_steps_done(pipeline_step.pipeline_run_id)
            
            return True
    
    async def _update_run_status_if_all_steps_done(self, run_id: int) -> None:
        """
        Update the run status if all steps are completed or failed.
        
        Args:
            run_id: ID of the pipeline run
        """
        async with get_session() as session:
            # Get all steps for this run
            result = await session.execute(
                select(PipelineStep).where(PipelineStep.pipeline_run_id == run_id)
            )
            
            steps = result.scalars().all()
            
            # Check if all steps are done
            all_completed = all(
                step.status in [PipelineRunStatus.COMPLETED, PipelineRunStatus.FAILED]
                for step in steps
            )
            
            if all_completed:
                # Check if any step failed
                any_failed = any(step.status == PipelineRunStatus.FAILED for step in steps)
                
                # Get the run
                run_result = await session.execute(
                    select(PipelineRun).where(PipelineRun.id == run_id)
                )
                
                pipeline_run = run_result.scalars().first()
                
                if pipeline_run:
                    pipeline_run.status = (
                        PipelineRunStatus.FAILED if any_failed else PipelineRunStatus.COMPLETED
                    )
                    pipeline_run.completed_at = datetime.utcnow()
                    
                    # Aggregate metadata from all steps
                    aggregated_metadata = {}
                    for step in steps:
                        if step.metadata:
                            step_type = step.step_type
                            aggregated_metadata[step_type] = step.metadata
                    
                    if pipeline_run.metadata:
                        pipeline_run.metadata.update({"steps": aggregated_metadata})
                    else:
                        pipeline_run.metadata = {"steps": aggregated_metadata}
                    
                    await session.commit()
    
    async def delete_pipeline_run(self, run_id: int) -> bool:
        """
        Delete a pipeline run and all its steps.
        
        Args:
            run_id: ID of the pipeline run
            
        Returns:
            True if successful, False otherwise
        """
        async with get_session() as session:
            result = await session.execute(
                select(PipelineRun).where(PipelineRun.id == run_id)
            )
            
            pipeline_run = result.scalars().first()
            
            if not pipeline_run:
                return False
                
            await session.delete(pipeline_run)
            await session.commit()
            
            return True
