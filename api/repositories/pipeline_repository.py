from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from db.connection import get_db_connection, execute_query, execute_transaction
from models.dataset import PipelineRun, PipelineStep, PipelineRunStatus, PipelineStepType

class PipelineRepository:
    """Repository for pipeline-related database operations."""
    
    async def create_pipeline_run(self, dataset_id: int) -> PipelineRun:
        """Create a new pipeline run."""
        query = """
        INSERT INTO pipeline_runs (
            dataset_id, status, start_time, pipeline_metadata
        ) VALUES ($1, $2, $3, $4)
        RETURNING *
        """
        
        now = datetime.utcnow()
        result = await execute_query(
            query,
            dataset_id,
            PipelineRunStatus.PENDING,
            now,
            json.dumps({})
        )
        
        return PipelineRun(**dict(result[0]))

    async def get_pipeline_run(self, run_id: int) -> Optional[PipelineRun]:
        """Get a pipeline run by ID."""
        query = "SELECT * FROM pipeline_runs WHERE id = $1"
        result = await execute_query(query, run_id)
        return PipelineRun(**dict(result[0])) if result else None

    async def get_pipeline_run_with_steps(self, run_id: int) -> Optional[PipelineRun]:
        """Get a pipeline run with its steps."""
        # Get pipeline run
        run_query = "SELECT * FROM pipeline_runs WHERE id = $1"
        run_result = await execute_query(run_query, run_id)
        if not run_result:
            return None
            
        # Get steps
        steps_query = "SELECT * FROM pipeline_steps WHERE pipeline_run_id = $1 ORDER BY id"
        steps_result = await execute_query(steps_query, run_id)
        
        run_data = dict(run_result[0])
        run_data['steps'] = [PipelineStep(**dict(step)) for step in steps_result]
        
        return PipelineRun(**run_data)
    
    async def get_latest_pipeline_run(self, dataset_id: int) -> Optional[Dict[str, Any]]:
        """Get the latest pipeline run for a dataset."""
        query = """
        SELECT * FROM pipeline_runs 
        WHERE dataset_id = $1 
        ORDER BY start_time DESC 
        LIMIT 1
        """
        result = await execute_query(query, dataset_id)
        return dict(result[0]) if result else None

    async def create_pipeline_step(
        self,
        pipeline_run_id: int = None,
        step_name: PipelineStepType = None,
        status: PipelineRunStatus = None,
        step_data: Dict[str, Any] = None
    ) -> PipelineStep:
        """Create a new pipeline step.
        
        This method supports two parameter formats:
        1. Individual parameters: pipeline_run_id, step_name, status
        2. Dictionary format: step_data with all required fields
        
        Args:
            pipeline_run_id: ID of the pipeline run
            step_name: Type of the pipeline step
            status: Status of the pipeline step
            step_data: Dictionary with all step data (alternative to individual parameters)
            
        Returns:
            Created pipeline step
        """
        # Handle both parameter formats
        if step_data is not None:
            # Dictionary format
            query = """
            INSERT INTO pipeline_steps (
                pipeline_run_id, step_type, status, start_time, end_time, step_metadata
            ) VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
            """
            
            # Convert metadata to JSON string if it's a dict
            metadata = step_data.get('metadata', {})
            if isinstance(metadata, dict):
                metadata = json.dumps(metadata)
            
            result = await execute_query(
                query,
                step_data['pipeline_run_id'],
                step_data['step_type'],
                step_data['status'],
                step_data.get('start_time', datetime.utcnow()),
                step_data.get('end_time'),
                metadata
            )
        else:
            # Individual parameters format
            query = """
            INSERT INTO pipeline_steps (
                pipeline_run_id, step_type, status, start_time, pipeline_metadata
            ) VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            """
            
            now = datetime.utcnow()
            result = await execute_query(
                query,
                pipeline_run_id,
                step_name,
                status,
                now,
                json.dumps({})
            )
        
        return PipelineStep(**dict(result[0]))

    async def update_pipeline_step_status(
        self,
        step_id: int,
        status: PipelineRunStatus,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[PipelineStep]:
        """Update a pipeline step's status and metadata."""
        query = """
        UPDATE pipeline_steps 
        SET status = $1, pipeline_metadata = $2, end_time = $3
        WHERE id = $4
        RETURNING *
        """
        
        now = datetime.utcnow()
        result = await execute_query(
            query,
            status,
            json.dumps(metadata or {}),
            now if status in [PipelineRunStatus.COMPLETED, PipelineRunStatus.FAILED] else None,
            step_id
        )
        
        return PipelineStep(**dict(result[0])) if result else None

    async def get_pipeline_steps(self, run_id: int) -> List[PipelineStep]:
        """Get all steps for a pipeline run."""
        query = "SELECT * FROM pipeline_steps WHERE pipeline_run_id = $1 ORDER BY id"
        result = await execute_query(query, run_id)
        return [PipelineStep(**dict(row)) for row in result]

    async def get_pipeline_runs(
        self,
        user_id: Optional[int] = None,
        dataset_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[PipelineRun]:
        """List pipeline runs with optional filters."""
        query = "SELECT * FROM pipeline_runs WHERE 1=1"
        values = []
        param_count = 1
        
        if dataset_id is not None:
            query += f" AND dataset_id = ${param_count}"
            values.append(dataset_id)
            param_count += 1
            
        query += f" ORDER BY start_time DESC LIMIT ${param_count} OFFSET ${param_count + 1}"
        values.extend([limit, skip])
        
        result = await execute_query(query, *values)
        return [PipelineRun(**dict(row)) for row in result]

    async def get_dataset_from_pipeline_run(self, run_id: int) -> Optional[Dict[str, Any]]:
        """Get the dataset associated with a pipeline run."""
        query = """
        SELECT d.* FROM datasets d
        JOIN pipeline_runs p ON d.id = p.dataset_id
        WHERE p.id = $1
        """
        result = await execute_query(query, run_id)
        return dict(result[0]) if result else None

def get_pipeline_repository(db_session: Optional[Session] = None) -> PipelineRepository:
    """Return a repository object for pipeline operations."""
    return PipelineRepository()
