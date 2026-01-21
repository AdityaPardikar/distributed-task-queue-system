"""Workflow routes for batch operations and task workflows."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from uuid import UUID

from src.core.workflow_engine import get_workflow_engine
from src.db.session import get_db

router = APIRouter(prefix="/workflows", tags=["workflows"])


class TaskDefinition(BaseModel):
    """Task definition for workflow."""
    name: str = Field(..., description="Task identifier within workflow")
    task_name: str = Field(..., description="Task type/handler name")
    task_args: List[Any] = Field(default_factory=list)
    task_kwargs: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)
    max_retries: int = Field(default=5, ge=0, le=10)
    timeout_seconds: int = Field(default=300, ge=1, le=3600)


class WorkflowCreate(BaseModel):
    """Schema for creating a workflow."""
    workflow_name: str = Field(..., min_length=1, max_length=255)
    tasks: List[TaskDefinition] = Field(..., min_items=1)
    dependencies: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Map of child task names to list of parent task names"
    )


class WorkflowResponse(BaseModel):
    """Response after workflow creation."""
    workflow_id: str
    workflow_name: str
    total_tasks: int
    task_ids: List[str]


class WorkflowStatusResponse(BaseModel):
    """Workflow status response."""
    status: str
    total_tasks: int
    completed: int
    failed: int
    running: int
    pending: int
    progress_percent: float


class BatchTaskCreate(BaseModel):
    """Schema for batch task creation."""
    tasks: List[TaskDefinition] = Field(..., min_items=1, max_items=100)


class BatchTaskResponse(BaseModel):
    """Response after batch task creation."""
    total_created: int
    task_ids: List[str]


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow: WorkflowCreate,
    db: Session = Depends(get_db)
):
    """Create a workflow with multiple tasks and dependencies.
    
    Example workflow with parallel tasks:
    ```json
    {
        "workflow_name": "data_pipeline",
        "tasks": [
            {"name": "fetch", "task_name": "fetch_data", "priority": 8},
            {"name": "process_a", "task_name": "process_chunk", "priority": 5},
            {"name": "process_b", "task_name": "process_chunk", "priority": 5},
            {"name": "aggregate", "task_name": "aggregate_results", "priority": 7}
        ],
        "dependencies": {
            "process_a": ["fetch"],
            "process_b": ["fetch"],
            "aggregate": ["process_a", "process_b"]
        }
    }
    ```
    """
    try:
        engine = get_workflow_engine(db)
        
        # Validate dependencies reference existing tasks
        task_names = {t.name for t in workflow.tasks}
        if workflow.dependencies:
            for child, parents in workflow.dependencies.items():
                if child not in task_names:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Dependency child '{child}' not found in tasks"
                    )
                for parent in parents:
                    if parent not in task_names:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Dependency parent '{parent}' not found in tasks"
                        )
        
        result = engine.create_workflow(
            workflow_name=workflow.workflow_name,
            tasks=[t.model_dump() for t in workflow.tasks],
            dependencies=workflow.dependencies
        )
        
        return WorkflowResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.get("/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: UUID,
    db: Session = Depends(get_db)
):
    """Get workflow status by tracking all tasks with matching workflow_id metadata."""
    # This is a simplified implementation
    # In production, you'd store workflow_id in task metadata or separate table
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Workflow status tracking requires workflow metadata storage"
    )


@router.post("/batch", response_model=BatchTaskResponse, status_code=status.HTTP_201_CREATED)
async def batch_create_tasks(
    batch: BatchTaskCreate,
    db: Session = Depends(get_db)
):
    """Create multiple independent tasks in a single batch operation.
    
    All tasks are created and enqueued immediately without dependencies.
    """
    try:
        engine = get_workflow_engine(db)
        task_ids = engine.batch_create_tasks([t.model_dump() for t in batch.tasks])
        
        return BatchTaskResponse(
            total_created=len(task_ids),
            task_ids=task_ids
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch tasks: {str(e)}"
        )
