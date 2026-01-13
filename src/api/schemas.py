"""API Schemas using Pydantic"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TaskCreate(BaseModel):
    """Schema for creating a task"""

    task_name: str = Field(..., min_length=1, max_length=255, description="Task name")
    task_args: List[Any] = Field(default=[], description="Task arguments")
    task_kwargs: Dict[str, Any] = Field(default={}, description="Task keyword arguments")
    priority: int = Field(default=5, ge=1, le=10, description="Task priority (1-10)")
    max_retries: int = Field(default=5, ge=0, le=10, description="Max retry attempts")
    timeout_seconds: int = Field(default=300, ge=1, le=3600, description="Task timeout")
    scheduled_at: Optional[datetime] = Field(None, description="Schedule time")
    parent_task_id: Optional[UUID] = Field(None, description="Parent task ID")
    campaign_id: Optional[UUID] = Field(None, description="Campaign ID")

    class Config:
        json_schema_extra = {
            "example": {
                "task_name": "send_email",
                "task_kwargs": {"email": "user@example.com", "subject": "Hello"},
                "priority": 5,
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
    """Schema for task list response"""

    items: List[TaskResponse]
    total: int
    page: int
    page_size: int


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
