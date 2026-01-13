"""Worker service layer for business logic"""

from sqlalchemy.orm import Session
from src.models import Worker
from uuid import UUID
from datetime import datetime
from typing import Optional, List


def register_worker(
    db: Session,
    hostname: str,
    capacity: int = 5,
) -> Worker:
    """Register a new worker"""
    worker = Worker(
        hostname=hostname,
        status="ACTIVE",
        capacity=capacity,
        last_heartbeat=datetime.utcnow(),
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)
    return worker


def get_worker(db: Session, worker_id: UUID) -> Optional[Worker]:
    """Get worker by ID"""
    return db.query(Worker).filter(Worker.worker_id == worker_id).first()


def update_worker_heartbeat(db: Session, worker_id: UUID) -> Optional[Worker]:
    """Update worker last heartbeat"""
    worker = get_worker(db, worker_id)
    if worker:
        worker.last_heartbeat = datetime.utcnow()
        db.commit()
        db.refresh(worker)
    return worker


def update_worker_status(db: Session, worker_id: UUID, status: str) -> Optional[Worker]:
    """Update worker status"""
    worker = get_worker(db, worker_id)
    if worker:
        worker.status = status
        db.commit()
        db.refresh(worker)
    return worker


def list_workers(db: Session, status: str = None) -> List[Worker]:
    """List workers with optional status filter"""
    query = db.query(Worker)
    if status:
        query = query.filter(Worker.status == status)
    return query.all()
