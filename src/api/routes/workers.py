"""Worker routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from src.api.schemas import WorkerListResponse, WorkerResponse
from src.db.session import get_db
from src.models import Worker

router = APIRouter(prefix="/workers", tags=["workers"])


@router.get("", response_model=WorkerListResponse)
async def list_workers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    db: Session = Depends(get_db),
):
    """List workers"""
    query = db.query(Worker)

    if status:
        query = query.filter(Worker.status == status)

    total = query.count()
    workers = query.offset((page - 1) * page_size).limit(page_size).all()

    return WorkerListResponse(
        items=[WorkerResponse.model_validate(w) for w in workers],
        total=total,
    )


@router.get("/{worker_id}", response_model=WorkerResponse)
async def get_worker(worker_id: UUID, db: Session = Depends(get_db)):
    """Get worker details"""
    worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    return WorkerResponse.model_validate(worker)


@router.post("/{worker_id}/pause")
async def pause_worker(worker_id: UUID, db: Session = Depends(get_db)):
    """Pause a worker"""
    worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    worker.status = "PAUSED"
    db.commit()

    return {"detail": "Worker paused", "worker_id": worker_id}


@router.post("/{worker_id}/resume")
async def resume_worker(worker_id: UUID, db: Session = Depends(get_db)):
    """Resume a worker"""
    worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    worker.status = "ACTIVE"
    db.commit()

    return {"detail": "Worker resumed", "worker_id": worker_id}
