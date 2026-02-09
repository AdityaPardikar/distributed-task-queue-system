"""Email template API routes"""

from typing import List
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.schemas import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
    TemplateVariableSchema,
)
from src.db.session import get_db
from src.models import EmailTemplate as EmailTemplateModel
from src.services.email_template_engine import EmailTemplate

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(
    template: TemplateCreate,
    db: Session = Depends(get_db),
) -> TemplateResponse:
    """Create a new email template"""
    try:
        # Validate template syntax using engine
        engine = EmailTemplate(template.subject, template.body)
        variables = engine.extract_variables()
        
        # Create database record
        db_template = EmailTemplateModel(
            email_template_id=uuid4(),
            name=template.name,
            subject=template.subject,
            body=template.body,
            variables={v.name: {"required": v.required, "default": v.default} for v in variables},
            version=1,
            campaign_id=template.campaign_id,
        )
        
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        
        # Convert to response schema
        return TemplateResponse(
            template_id=db_template.email_template_id,
            name=db_template.name,
            subject=db_template.subject,
            body=db_template.body,
            variables=[
                TemplateVariableSchema(
                    name=name,
                    required=info.get("required", True),
                    default=info.get("default"),
                )
                for name, info in db_template.variables.items()
            ],
            version=db_template.version,
            campaign_id=db_template.campaign_id,
            created_at=db_template.created_at,
            updated_at=db_template.updated_at,
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create template")


@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    campaign_id: UUID = Query(None, description="Filter by campaign ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> List[TemplateResponse]:
    """List all email templates with optional filtering"""
    query = db.query(EmailTemplateModel)
    
    if campaign_id:
        query = query.filter(EmailTemplateModel.campaign_id == campaign_id)
    
    templates = query.offset(skip).limit(limit).all()
    
    return [
        TemplateResponse(
            template_id=t.email_template_id,
            name=t.name,
            subject=t.subject,
            body=t.body,
            variables=[
                TemplateVariableSchema(
                    name=name,
                    required=info.get("required", True),
                    default=info.get("default"),
                )
                for name, info in t.variables.items()
            ],
            version=t.version,
            campaign_id=t.campaign_id,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in templates
    ]


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: UUID,
    db: Session = Depends(get_db),
) -> TemplateResponse:
    """Get a specific email template"""
    template = db.query(EmailTemplateModel).filter(
        EmailTemplateModel.email_template_id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return TemplateResponse(
        template_id=template.email_template_id,
        name=template.name,
        subject=template.subject,
        body=template.body,
        variables=[
            TemplateVariableSchema(
                name=name,
                required=info.get("required", True),
                default=info.get("default"),
            )
            for name, info in template.variables.items()
        ],
        version=template.version,
        campaign_id=template.campaign_id,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    update_data: TemplateUpdate,
    db: Session = Depends(get_db),
) -> TemplateResponse:
    """Update an existing email template"""
    template = db.query(EmailTemplateModel).filter(
        EmailTemplateModel.email_template_id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        # Update fields if provided
        if update_data.name is not None:
            template.name = update_data.name
        
        if update_data.subject is not None:
            template.subject = update_data.subject
        
        if update_data.body is not None:
            template.body = update_data.body
        
        # Re-validate template syntax
        engine = EmailTemplate(template.subject, template.body)
        variables = engine.extract_variables()
        template.variables = {v.name: {"required": v.required, "default": v.default} for v in variables}
        
        # Increment version
        template.version += 1
        template.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(template)
        
        return TemplateResponse(
            template_id=template.email_template_id,
            name=template.name,
            subject=template.subject,
            body=template.body,
            variables=[
                TemplateVariableSchema(
                    name=name,
                    required=info.get("required", True),
                    default=info.get("default"),
                )
                for name, info in template.variables.items()
            ],
            version=template.version,
            campaign_id=template.campaign_id,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update template")


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: UUID,
    db: Session = Depends(get_db),
) -> None:
    """Delete an email template"""
    template = db.query(EmailTemplateModel).filter(
        EmailTemplateModel.email_template_id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(template)
    db.commit()


@router.post("/{template_id}/preview", response_model=TemplatePreviewResponse)
async def preview_template(
    template_id: UUID,
    preview_request: TemplatePreviewRequest,
    db: Session = Depends(get_db),
) -> TemplatePreviewResponse:
    """Preview a template with sample variables"""
    template = db.query(EmailTemplateModel).filter(
        EmailTemplateModel.email_template_id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        engine = EmailTemplate(template.subject, template.body)
        rendered_subject, rendered_body = engine.render(preview_request.variables)
        variables = engine.extract_variables()
        
        return TemplatePreviewResponse(
            subject=rendered_subject,
            body=rendered_body,
            variables=[
                TemplateVariableSchema(
                    name=v.name,
                    required=v.required,
                    default=v.default,
                )
                for v in variables
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to preview template")
