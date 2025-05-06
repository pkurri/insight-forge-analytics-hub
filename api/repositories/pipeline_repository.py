from typing import Any, Dict, List, Optional
from api.models.db_models import PipelineRun, PipelineStep, Dataset
from sqlalchemy.orm import Session
from datetime import datetime

class PipelineRepository:
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

    def create_pipeline_run(self, dataset_id: int, status: str = 'pending', **kwargs) -> PipelineRun:
        """Create a new pipeline run."""
        run = PipelineRun(dataset_id=dataset_id, status=status, **kwargs)
        if self.db_session:
            self.db_session.add(run)
            self.db_session.commit()
        return run

    def get_pipeline_run(self, run_id: int) -> Optional[PipelineRun]:
        """Get a pipeline run by ID."""
        if self.db_session:
            return self.db_session.query(PipelineRun).filter_by(id=run_id).first()
        return None

    def get_pipeline_run_with_steps(self, run_id: int) -> Optional[PipelineRun]:
        """Get a pipeline run with its steps."""
        if self.db_session:
            run = self.db_session.query(PipelineRun).filter_by(id=run_id).first()
            if run:
                run.steps = self.get_pipeline_steps(run_id)
            return run
        return None

    def get_dataset_from_pipeline_run(self, run_id: int) -> Optional[Dataset]:
        """Get the dataset associated with a pipeline run."""
        if self.db_session:
            run = self.db_session.query(PipelineRun).filter_by(id=run_id).first()
            if run:
                return self.db_session.query(Dataset).filter_by(id=run.dataset_id).first()
        return None

    def create_pipeline_step(self, pipeline_run_id: int, step_name: str, status: str = 'pending', **kwargs) -> PipelineStep:
        """Create a new pipeline step."""
        step = PipelineStep(pipeline_run_id=pipeline_run_id, step_name=step_name, status=status, **kwargs)
        if self.db_session:
            self.db_session.add(step)
            self.db_session.commit()
        return step

    def get_pipeline_step(self, step_id: int) -> Optional[PipelineStep]:
        """Get a pipeline step by ID."""
        if self.db_session:
            return self.db_session.query(PipelineStep).filter_by(id=step_id).first()
        return None

    def get_pipeline_steps(self, run_id: int) -> List[PipelineStep]:
        """Get all steps for a pipeline run."""
        if self.db_session:
            return self.db_session.query(PipelineStep).filter_by(pipeline_run_id=run_id).all()
        return []

    def update_pipeline_run_status(self, run_id: int, status: str, **kwargs) -> Optional[PipelineRun]:
        """Update the status of a pipeline run."""
        if self.db_session:
            run = self.db_session.query(PipelineRun).filter_by(id=run_id).first()
            if run:
                run.status = status
                for key, value in kwargs.items():
                    setattr(run, key, value)
                self.db_session.commit()
                return run
        return None

    def update_pipeline_step_status(self, step_id: int, status: str, **kwargs) -> Optional[PipelineStep]:
        """Update the status of a pipeline step."""
        if self.db_session:
            step = self.db_session.query(PipelineStep).filter_by(id=step_id).first()
            if step:
                step.status = status
                for key, value in kwargs.items():
                    setattr(step, key, value)
                self.db_session.commit()
                return step
        return None

    def get_pipeline_runs(self, user_id: Optional[int] = None, dataset_id: Optional[int] = None, 
                         skip: int = 0, limit: int = 100) -> List[PipelineRun]:
        """Get pipeline runs with optional filtering."""
        if self.db_session:
            query = self.db_session.query(PipelineRun)
            if dataset_id:
                query = query.filter_by(dataset_id=dataset_id)
            if user_id:
                query = query.join(Dataset).filter(Dataset.user_id == user_id)
            return query.order_by(PipelineRun.start_time.desc()).offset(skip).limit(limit).all()
        return []

def get_pipeline_repository(db_session: Optional[Session] = None) -> PipelineRepository:
    """Return a repository object for pipeline operations."""
    return PipelineRepository(db_session)
