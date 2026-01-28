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
    cron_expression: Optional[str] = Field(None, description="Cron expression for recurring tasks (e.g., '0 */6 * * *')")
    is_recurring: bool = Field(default=False, description="Whether this is a recurring task")
    depends_on: List[UUID] = Field(default_factory=list, description="List of task IDs that must complete before this task runs")
    parent_task_id: Optional[UUID] = Field(None, description="Parent task ID for dependencies")
    campaign_id: Optional[UUID] = Field(None, description="Campaign ID if part of campaign")

    @field_validator('task_name')
    @classmethod
    def validate_task_name(cls, v: str) -> str:
        """Validate task name format"""
        if not v or not v.strip():
            raise ValueError("Task name cannot be empty")
        return v.strip()
    
    @field_validator('cron_expression')
    @classmethod
    def validate_cron_expression(cls, v: Optional[str]) -> Optional[str]:
        """Validate cron expression format"""
        if v:
            from croniter import croniter
            try:
                croniter(v)
            except Exception:
                raise ValueError(f"Invalid cron expression: {v}")
        return v

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


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    
    priority: Optional[int] = Field(None, ge=1, le=10, description="Update priority (1-10)")
    timeout_seconds: Optional[int] = Field(None, ge=1, le=3600, description="Update timeout in seconds")
    max_retries: Optional[int] = Field(None, ge=0, le=10, description="Update max retries")
    task_kwargs: Optional[Dict[str, Any]] = Field(None, description="Update task arguments")
    
    class Config:
        json_schema_extra = {
            "example": {
                "priority": 8,
                "timeout_seconds": 120,
                "task_kwargs": {"email": "new@example.com"}
            }
        }


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
    template_variables: Dict[str, Any] = Field(default_factory=dict)
    rate_limit_per_minute: int = Field(default=100, ge=1, le=1000)
    scheduled_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Welcome Campaign",
                "template_subject": "Welcome {{name}}!",
                "template_body": "Hello {{name}}, welcome to our service.",
                "template_variables": {"name": "John"},
            }
        }


class CampaignUpdate(BaseModel):
    """Schema for updating a campaign"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    template_subject: Optional[str] = Field(None, min_length=1, max_length=255)
    template_body: Optional[str] = None
    template_variables: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, description="Campaign status")
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=1000)
    scheduled_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Welcome Campaign v2",
                "template_subject": "Updated subject",
                "status": "SCHEDULED",
                "rate_limit_per_minute": 200,
            }
        }


class CampaignResponse(BaseModel):
    """Schema for campaign response"""

    campaign_id: UUID
    name: str
    status: str
    template_subject: Optional[str] = None
    template_body: Optional[str] = None
    template_variables: Dict[str, Any] = Field(default_factory=dict)
    rate_limit_per_minute: Optional[int] = None
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


class TemplateVariableSchema(BaseModel):
    """Schema for template variable information"""

    name: str = Field(..., description="Variable name")
    required: bool = Field(default=True, description="Whether variable is required")
    default: Optional[str] = Field(None, description="Default value if not provided")


class TemplateCreate(BaseModel):
    """Schema for creating an email template"""

    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    subject: str = Field(..., min_length=1, max_length=255, description="Email subject template")
    body: str = Field(..., min_length=1, description="Email body template (HTML or plain text)")
    campaign_id: Optional[UUID] = Field(None, description="Associated campaign ID")

    @field_validator('subject', 'body')
    @classmethod
    def validate_template_syntax(cls, v: str) -> str:
        """Validate Jinja2 syntax"""
        from jinja2 import Template, TemplateSyntaxError
        try:
            Template(v)
        except TemplateSyntaxError as e:
            raise ValueError(f"Invalid template syntax: {e.message}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Welcome Email",
                "subject": "Welcome {{ first_name }}!",
                "body": "<p>Hello {{ first_name }} {{ last_name }},</p><p>Thanks for joining!</p>",
                "campaign_id": None
            }
        }


class TemplateUpdate(BaseModel):
    """Schema for updating an email template"""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Template name")
    subject: Optional[str] = Field(None, min_length=1, max_length=255, description="Email subject template")
    body: Optional[str] = Field(None, min_length=1, description="Email body template")

    @field_validator('subject', 'body')
    @classmethod
    def validate_template_syntax(cls, v: Optional[str]) -> Optional[str]:
        """Validate Jinja2 syntax"""
        if v is None:
            return v
        from jinja2 import Template, TemplateSyntaxError
        try:
            Template(v)
        except TemplateSyntaxError as e:
            raise ValueError(f"Invalid template syntax: {e.message}")
        return v


class TemplateResponse(BaseModel):
    """Schema for email template response"""

    template_id: UUID
    name: str
    subject: str
    body: str
    variables: List[TemplateVariableSchema]
    version: int
    campaign_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "template_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Welcome Email",
                "subject": "Welcome {{ first_name }}!",
                "body": "<p>Hello {{ first_name }},</p>",
                "variables": [
                    {"name": "first_name", "required": True, "default": None}
                ],
                "version": 1,
                "campaign_id": None,
                "created_at": "2026-01-27T12:00:00",
                "updated_at": "2026-01-27T12:00:00"
            }
        }


class TemplatePreviewRequest(BaseModel):
    """Schema for template preview request"""

    variables: Dict[str, Any] = Field(..., description="Template variables for rendering")

    class Config:
        json_schema_extra = {
            "example": {
                "variables": {
                    "first_name": "John",
                    "last_name": "Doe"
                }
            }
        }


class TemplatePreviewResponse(BaseModel):
    """Schema for template preview response"""

    subject: str
    body: str
    variables: List[TemplateVariableSchema]

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Welcome John!",
                "body": "<p>Hello John Doe,</p>",
                "variables": [
                    {"name": "first_name", "required": True},
                    {"name": "last_name", "required": True}
                ]
            }
        }


# Recipient Schemas

class RecipientCreate(BaseModel):
    """Schema for creating a single recipient"""

    email: str = Field(..., description="Recipient email address")
    name: Optional[str] = Field(None, description="Recipient name")
    personalization: Dict[str, Any] = Field(default_factory=dict, description="Template variables for this recipient")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation"""
        if not v or '@' not in v:
            raise ValueError("Invalid email address")
        return v.lower().strip()

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "name": "John Doe",
                "personalization": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "company": "Acme Corp"
                }
            }
        }


class RecipientBulkCreate(BaseModel):
    """Schema for bulk recipient upload"""

    recipients: List[RecipientCreate] = Field(..., min_length=1, description="List of recipients to add")

    class Config:
        json_schema_extra = {
            "example": {
                "recipients": [
                    {
                        "email": "user1@example.com",
                        "name": "User One",
                        "personalization": {"first_name": "User", "last_name": "One"}
                    },
                    {
                        "email": "user2@example.com",
                        "name": "User Two",
                        "personalization": {"first_name": "User", "last_name": "Two"}
                    }
                ]
            }
        }


class RecipientResponse(BaseModel):
    """Schema for recipient response"""

    recipient_id: UUID
    campaign_id: UUID
    email: str
    status: str
    personalization: Dict[str, Any]
    sent_at: Optional[datetime]
    task_id: Optional[UUID]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecipientListResponse(BaseModel):
    """Schema for recipient list response"""

    items: List[RecipientResponse]
    total: int
    page: int
    page_size: int


class CampaignLaunchRequest(BaseModel):
    """Schema for launching a campaign"""

    template_id: Optional[UUID] = Field(None, description="Optional template ID to use instead of campaign template")
    send_immediately: bool = Field(default=True, description="Send immediately or schedule for later")
    scheduled_at: Optional[datetime] = Field(None, description="Schedule time if not sending immediately")

    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "550e8400-e29b-41d4-a716-446655440000",
                "send_immediately": True,
                "scheduled_at": None
            }
        }


class CampaignLaunchResponse(BaseModel):
    """Schema for campaign launch response"""

    campaign_id: UUID
    status: str
    total_recipients: int
    tasks_created: int
    scheduled_at: Optional[datetime]

    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "RUNNING",
                "total_recipients": 150,
                "tasks_created": 150,
                "scheduled_at": None
            }
        }


class BulkUploadResult(BaseModel):
    """Schema for bulk upload result"""

    total_uploaded: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "total_uploaded": 100,
                "successful": 95,
                "failed": 5,
                "errors": [
                    {"row": 3, "email": "invalid", "error": "Invalid email address"},
                    {"row": 7, "email": "duplicate@example.com", "error": "Duplicate email"}
                ]
            }
        }
