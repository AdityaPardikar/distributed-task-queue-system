"""Campaign routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from src.api.schemas import CampaignCreate, CampaignListResponse, CampaignResponse, CampaignUpdate
from src.db.session import get_db
from src.models import Campaign

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post("", response_model=CampaignResponse, status_code=201)
async def create_campaign(campaign: CampaignCreate, db: Session = Depends(get_db)):
    """Create a new campaign"""
    try:
        db_campaign = Campaign(
            name=campaign.name,
            template_subject=campaign.template_subject,
            template_body=campaign.template_body,
            template_variables=campaign.template_variables or {},
            rate_limit_per_minute=campaign.rate_limit_per_minute,
            scheduled_at=campaign.scheduled_at,
            created_by=None,  # Will be set from JWT in production
        )
        db.add(db_campaign)
        db.commit()
        db.refresh(db_campaign)
        return CampaignResponse.model_validate(db_campaign)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    db: Session = Depends(get_db),
):
    """List campaigns"""
    query = db.query(Campaign)

    if status:
        query = query.filter(Campaign.status == status)

    total = query.count()
    campaigns = query.offset((page - 1) * page_size).limit(page_size).all()

    return CampaignListResponse(
        items=[CampaignResponse.model_validate(c) for c in campaigns],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: UUID, db: Session = Depends(get_db)):
    """Get campaign details"""
    campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return CampaignResponse.model_validate(campaign)


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(campaign_id: UUID, payload: CampaignUpdate, db: Session = Depends(get_db)):
    """Update an existing campaign"""
    campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if payload.name is not None:
        campaign.name = payload.name
    if payload.template_subject is not None:
        campaign.template_subject = payload.template_subject
    if payload.template_body is not None:
        campaign.template_body = payload.template_body
    if payload.template_variables is not None:
        campaign.template_variables = payload.template_variables
    if payload.status is not None:
        campaign.status = payload.status
    if payload.rate_limit_per_minute is not None:
        campaign.rate_limit_per_minute = payload.rate_limit_per_minute
    if payload.scheduled_at is not None:
        campaign.scheduled_at = payload.scheduled_at

    db.commit()
    db.refresh(campaign)
    return CampaignResponse.model_validate(campaign)


@router.post("/{campaign_id}/start")
async def start_campaign(campaign_id: UUID, db: Session = Depends(get_db)):
    """Start a campaign"""
    campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = "RUNNING"
    db.commit()

    return {"detail": "Campaign started", "campaign_id": campaign_id}


@router.post("/{campaign_id}/pause")
async def pause_campaign(campaign_id: UUID, db: Session = Depends(get_db)):
    """Pause a campaign"""
    campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = "PAUSED"
    db.commit()

    return {"detail": "Campaign paused", "campaign_id": campaign_id}
