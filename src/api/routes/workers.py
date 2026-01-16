"""Worker routes for registration and heartbeat tracking."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from src.api.schemas import WorkerListResponse, WorkerResponse
from src.db.session import get_db
from src.models import Worker, Task
from src.core.broker import get_broker

router = APIRouter(prefix="/workers", tags=["workers"])


@router.post("", response_model=WorkerResponse, status_code=status.HTTP_201_CREATED)
async def register_worker(
    hostname: str = Query(..., min_length=1, max_length=255, description="Worker hostname/ID"),
    capacity: int = Query(5, ge=1, le=100, description="Max concurrent tasks"),
    db: Session = Depends(get_db)
):
    """Register a new worker.
    
    A worker is a process that executes tasks from the queue.
    
    Args:
        hostname: Worker hostname/identifier
        capacity: Max concurrent tasks this worker can handle
        
    Returns:
        Worker details with ID and status
    """
    try:
        # Create worker record
        worker = Worker(
            hostname=hostname,
            capacity=capacity,
            current_load=0,
            status="ACTIVE",
            last_heartbeat=datetime.utcnow(),
            metadata={"version": "1.0"}
        )
        db.add(worker)
        db.commit()
        db.refresh(worker)
        
        # Register in Redis
        broker = get_broker()
        broker.register_worker(
            str(worker.worker_id),
            {
                "hostname": hostname,
                "capacity": str(capacity),
                "status": "ACTIVE",
                "registered_at": datetime.utcnow().isoformat()
            }
        )
        
        return WorkerResponse.model_validate(worker)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register worker: {str(e)}"
        )


@router.post("/{worker_id}/heartbeat", response_model=WorkerResponse, status_code=status.HTTP_200_OK)
async def send_heartbeat(
    worker_id: UUID,
    current_load: int = Query(..., ge=0, description="Current task load"),
    worker_status: str = Query("ACTIVE", regex="^(ACTIVE|DRAINING|OFFLINE)$"),
    db: Session = Depends(get_db)
):
    """Send heartbeat to keep worker alive.
    
    Workers should send heartbeat every 15-30 seconds.
    Workers without heartbeat for > 30s are considered offline.
    """
    worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker {worker_id} not found"
        )
    
    try:
        # Update worker
        worker.current_load = current_load
        worker.status = worker_status
        worker.last_heartbeat = datetime.utcnow()
        db.commit()
        db.refresh(worker)
        
        # Update in Redis
        broker = get_broker()
        broker.update_worker_heartbeat(str(worker_id), int(datetime.utcnow().timestamp()))
        broker.redis.hset(
            f"worker:{worker_id}",
            mapping={
                "current_load": str(current_load),
                "status": worker_status,
                "last_heartbeat": worker.last_heartbeat.isoformat()
            }
        )
        
        return WorkerResponse.model_validate(worker)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Heartbeat update failed: {str(e)}"
        )


@router.get("", response_model=WorkerListResponse)
async def list_workers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    worker_status: str = Query(None, regex="^(ACTIVE|DRAINING|OFFLINE)$"),
    db: Session = Depends(get_db),
):
    """List all registered workers with pagination and filtering."""
    query = db.query(Worker)

    if worker_status:
        query = query.filter(Worker.status == worker_status)

    total = query.count()
    workers = query.order_by(Worker.last_heartbeat.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

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


@router.get("/{worker_id}/tasks", status_code=status.HTTP_200_OK)
async def get_worker_tasks(
    worker_id: UUID,
    db: Session = Depends(get_db)
):
    """Get tasks assigned to a worker."""
    worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker {worker_id} not found"
        )
    
    # Get tasks assigned to this worker
    tasks = db.query(Task).filter(
        Task.worker_id == worker_id,
        Task.status.in_(["RUNNING", "QUEUED"])
    ).all()
    
    return {
        "worker_id": str(worker_id),
        "total_tasks": len(tasks),
        "tasks": [
            {
                "task_id": str(t.task_id),
                "name": t.task_name,
                "status": t.status,
                "priority": t.priority
            }
            for t in tasks
        ]
    }


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
