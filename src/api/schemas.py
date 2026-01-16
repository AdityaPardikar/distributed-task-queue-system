"""API Schemas using Pydantic"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TaskCreate(BaseModel):
    """Schema for creating a task"""

    task_name: str = Field(..., min_length=1, max_length=255, description="Task name/type")
    task_args: List[Any] = Field(default=[], description="Task positional arguments")
    task_kwargs: Dict[str, Any] = Field(default={}, description="Task keyword arguments")
    priority: int = Field(default=5, ge=1, le=10, description="Task priority (1=lowest, 10=highest)")
    max_retries: int = Field(default=5, ge=0, le=10, description="Maximum retry attempts")
    timeout_seconds: int = Field(default=300, ge=1, le=3600, description="Task timeout in seconds")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled execution time")
    parent_task_id: Optional[UUID] = Field(None, description="Parent task ID for dependencies")
    campaign_id: Optional[UUID] = Field(None, description="Campaign ID if part of campaign")

    @field_validator('task_name')
    @classmethod
    def validate_task_name(cls, v: str) -> str:
        """Validate task name format"""
        if not v or not v.strip():
            raise ValueError("Task name cannot be empty")
        return v.strip()

    @field_validator('task_kwargs')
    @classmethod
    def validate_task_kwargs(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate task kwargs are JSON-serializable"""
        # This is a basic check; actual serialization will be tested later
        if not isinstance(v, dict):
            raise ValueError("task_kwargs must be a dictionary")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "task_name": "send_email",
                "task_kwargs": {
                    "to": "user@example.com",
                    "subject": "Welcome!",
                    "body": "Hello and welcome!"
                },
                "priority": 8,
                "max_retries": 3,
                "timeout_seconds": 60
            }
        }


class TaskResponse(BaseModel):
    """Schema for task response"""

    task_id: UUID
    task_name: str
    priority: int
    status: str
    retry_count: int
    max_retries: int
    timeout_seconds: int
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Schema for task list response with pagination"""

    items: List[TaskResponse]
    total: int
    page: int
    page_size: int
    has_next: bool = False
    has_previous: bool = False
    total_pages: int = 1

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 150,
                "page": 1,
                "page_size": 20,
                "has_next": True,
                "has_previous": False,
                "total_pages": 8
            }
        }


class TaskExecutionInfo(BaseModel):
    """Schema for task execution information"""
    
    execution_id: UUID
    attempt_number: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: str
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class TaskDetailResponse(TaskResponse):
    """Extended schema for detailed task response"""
    
    task_args: List[Any] = []
    task_kwargs: Dict[str, Any] = {}
    worker_id: Optional[UUID] = None
    parent_task_id: Optional[UUID] = None
    campaign_id: Optional[UUID] = None
    retry_count: int = 0
    executions: List[TaskExecutionInfo] = []
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WorkerResponse(BaseModel):
    """Schema for worker response"""

    worker_id: UUID
    hostname: str
    status: str
    capacity: int
    current_load: int
    last_heartbeat: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WorkerListResponse(BaseModel):
    """Schema for worker list response"""

    items: List[WorkerResponse]
    total: int


class CampaignCreate(BaseModel):
    """Schema for creating a campaign"""

    name: str = Field(..., min_length=1, max_length=255)
    template_subject: str = Field(..., min_length=1, max_length=255)
    template_body: str = Field(...)
    template_variables: Dict[str, Any] = Field(default={})
    rate_limit_per_minute: int = Field(default=100, ge=1, le=1000)
    scheduled_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Welcome Campaign",
                "template_subject": "Welcome {{name}}!",
                "template_body": "Hello {{name}}, welcome to our service.",
                "template_variables": ["name"],
            }
        }


class CampaignResponse(BaseModel):
    """Schema for campaign response"""

    campaign_id: UUID
    name: str
    status: str
    total_recipients: int
    sent_count: int
    failed_count: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    """Schema for campaign list response"""

    items: List[CampaignResponse]
    total: int
    page: int
    page_size: int


class HealthResponse(BaseModel):
    """Schema for health check response"""

    status: str
    version: str
    timestamp: datetime


class MetricsResponse(BaseModel):
    """Schema for metrics response"""

    tasks_total: int
    tasks_completed: int
    tasks_failed: int
    tasks_pending: int
    workers_active: int
    workers_idle: int
    queue_depth: int
    avg_task_duration: float


class ErrorResponse(BaseModel):
    """Schema for error response"""

    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
