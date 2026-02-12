"""Advanced workflow API routes with templates, conditions, and visualization."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.advanced_workflow import (
    AdvancedWorkflowEngine,
    WorkflowTemplate,
    WorkflowTemplateStore,
    TaskChain,
    ConditionOperator,
    DependencyType,
    get_advanced_workflow_engine,
)
from src.db.session import get_db

router = APIRouter(prefix="/workflows/advanced", tags=["advanced-workflows"])


# --- Schemas ---

class ConditionSchema(BaseModel):
    """Schema for task execution condition."""
    field: str = Field(..., description="Field path (e.g., 'task_a.result.status')")
    operator: str = Field(..., description="Comparison operator")
    value: Optional[Any] = None
    conditions: Optional[List["ConditionSchema"]] = None


class TaskDefinitionSchema(BaseModel):
    """Enhanced task definition with conditions."""
    name: str = Field(..., description="Task identifier within workflow")
    task_name: str = Field(..., description="Task type/handler name")
    task_args: List[Any] = Field(default_factory=list)
    task_kwargs: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)
    max_retries: int = Field(default=5, ge=0, le=10)
    timeout_seconds: int = Field(default=300, ge=1, le=3600)
    condition: Optional[ConditionSchema] = None


class DependencySchema(BaseModel):
    """Dependency definition with type."""
    parents: List[str] = Field(default_factory=list)
    type: str = Field(default="wait_for_all", description="wait_for_all, wait_for_any, sequential")


class AdvancedWorkflowCreate(BaseModel):
    """Schema for creating an advanced workflow."""
    workflow_name: str = Field(..., min_length=1, max_length=255)
    tasks: List[TaskDefinitionSchema] = Field(..., min_length=1)
    dependencies: Optional[Dict[str, List[str]]] = None
    conditions: Optional[Dict[str, ConditionSchema]] = None


class WorkflowTemplateCreate(BaseModel):
    """Schema for creating a workflow template."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    version: str = "1.0.0"
    tasks: List[TaskDefinitionSchema] = Field(..., min_length=1)
    dependencies: Optional[Dict[str, List[str]]] = None
    conditions: Optional[Dict[str, ConditionSchema]] = None


class WorkflowFromTemplateCreate(BaseModel):
    """Create workflow from template."""
    template_id: str
    workflow_name: str
    parameters: Optional[Dict[str, Any]] = None


class WorkflowVisualizationResponse(BaseModel):
    """Workflow visualization data."""
    workflow_id: str
    workflow_name: Optional[str] = None
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    execution_levels: List[List[str]]


class TaskChainStep(BaseModel):
    """Step in a task chain."""
    task_name: str
    handler: str
    args: Optional[List[Any]] = None
    kwargs: Optional[Dict[str, Any]] = None
    condition: Optional[ConditionSchema] = None


class TaskChainCreate(BaseModel):
    """Create workflow using task chain syntax."""
    workflow_name: str
    initial_task: TaskChainStep
    chain: List[TaskChainStep]


# --- Routes ---

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_advanced_workflow(
    workflow: AdvancedWorkflowCreate,
    db: Session = Depends(get_db),
):
    """Create an advanced workflow with conditions and typed dependencies.
    
    Example with conditions:
    ```json
    {
        "workflow_name": "conditional_pipeline",
        "tasks": [
            {"name": "validate", "task_name": "validate_data"},
            {"name": "process", "task_name": "process_data"},
            {"name": "notify", "task_name": "send_notification"}
        ],
        "dependencies": {
            "process": ["validate"],
            "notify": ["process"]
        },
        "conditions": {
            "process": {
                "field": "validate.result.valid",
                "operator": "eq",
                "value": true
            }
        }
    }
    ```
    """
    try:
        engine = get_advanced_workflow_engine(db)
        
        # Convert conditions to dict format
        conditions_dict = None
        if workflow.conditions:
            conditions_dict = {
                name: cond.model_dump() for name, cond in workflow.conditions.items()
            }
        
        result = engine.create_workflow(
            workflow_name=workflow.workflow_name,
            tasks=[t.model_dump() for t in workflow.tasks],
            dependencies=workflow.dependencies,
            conditions=conditions_dict,
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.get("/{workflow_id}/visualization", response_model=WorkflowVisualizationResponse)
async def get_workflow_visualization(
    workflow_id: str,
    db: Session = Depends(get_db),
):
    """Get workflow visualization data for rendering dependency graph."""
    try:
        engine = get_advanced_workflow_engine(db)
        viz_data = engine.get_workflow_visualization(workflow_id)
        
        if not viz_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        return WorkflowVisualizationResponse(**viz_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get visualization: {str(e)}"
        )


# --- Template Routes ---

@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_workflow_template(
    template: WorkflowTemplateCreate,
):
    """Create a reusable workflow template.
    
    Use {{parameter_name}} syntax in task_kwargs for parameter placeholders.
    """
    try:
        from uuid import uuid4
        
        store = WorkflowTemplateStore()
        
        wf_template = WorkflowTemplate(
            template_id=str(uuid4()),
            name=template.name,
            description=template.description,
            version=template.version,
            tasks=[t.model_dump() for t in template.tasks],
            dependencies=template.dependencies,
            conditions={
                name: cond.model_dump() for name, cond in template.conditions.items()
            } if template.conditions else None,
        )
        
        store.save(wf_template)
        
        return wf_template.to_dict()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )


@router.get("/templates")
async def list_workflow_templates():
    """List all workflow templates."""
    try:
        store = WorkflowTemplateStore()
        templates = store.list_all()
        
        return {
            "templates": [t.to_dict() for t in templates],
            "total": len(templates),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}"
        )


@router.get("/templates/{template_id}")
async def get_workflow_template(template_id: str):
    """Get a workflow template by ID."""
    store = WorkflowTemplateStore()
    template = store.get(template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found"
        )
    
    return template.to_dict()


@router.delete("/templates/{template_id}")
async def delete_workflow_template(template_id: str):
    """Delete a workflow template."""
    store = WorkflowTemplateStore()
    store.delete(template_id)
    
    return {"message": "Template deleted"}


@router.post("/from-template", status_code=status.HTTP_201_CREATED)
async def create_workflow_from_template(
    request: WorkflowFromTemplateCreate,
    db: Session = Depends(get_db),
):
    """Create a workflow instance from a template.
    
    Parameters will be substituted for {{placeholder}} values in task_kwargs.
    """
    try:
        engine = get_advanced_workflow_engine(db)
        
        result = engine.create_workflow_from_template(
            template_id=request.template_id,
            workflow_name=request.workflow_name,
            parameters=request.parameters,
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow from template: {str(e)}"
        )


@router.post("/chain", status_code=status.HTTP_201_CREATED)
async def create_workflow_chain(
    request: TaskChainCreate,
    db: Session = Depends(get_db),
):
    """Create workflow using fluent chain syntax.
    
    Example:
    ```json
    {
        "workflow_name": "chained_workflow",
        "initial_task": {
            "task_name": "start",
            "handler": "start_task"
        },
        "chain": [
            {"task_name": "step1", "handler": "process_step1"},
            {"task_name": "step2", "handler": "process_step2"},
            {"task_name": "end", "handler": "finish_task"}
        ]
    }
    ```
    """
    try:
        engine = get_advanced_workflow_engine(db)
        
        # Build chain
        chain = TaskChain({
            "name": request.initial_task.task_name,
            "task_name": request.initial_task.handler,
            "task_args": request.initial_task.args or [],
            "task_kwargs": request.initial_task.kwargs or {},
        })
        
        for step in request.chain:
            chain.then(
                task_name=step.task_name,
                handler=step.handler,
                args=step.args,
                kwargs=step.kwargs,
            )
        
        workflow_def = chain.build()
        
        result = engine.create_workflow(
            workflow_name=request.workflow_name,
            tasks=workflow_def["tasks"],
            dependencies=workflow_def["dependencies"],
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create chained workflow: {str(e)}"
        )
