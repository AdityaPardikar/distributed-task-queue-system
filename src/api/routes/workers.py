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


@router.patch("/{worker_id}/status", response_model=WorkerResponse)
async def update_worker_status(
    worker_id: UUID,
    new_status: str = Query(..., regex="^(ACTIVE|DRAINING|OFFLINE)$"),
    db: Session = Depends(get_db)
):
    """Update worker status.
    
    Status transitions:
    - ACTIVE: Worker is actively accepting tasks
    - DRAINING: Worker stops accepting new tasks but finishes existing ones
    - OFFLINE: Worker is offline and all tasks should be reassigned
    """
    worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker {worker_id} not found"
        )
    
    try:
        # Validate status transition
        current_status = worker.status
        valid_transitions = {
            "ACTIVE": ["DRAINING", "OFFLINE"],
            "DRAINING": ["OFFLINE", "ACTIVE"],
            "OFFLINE": ["ACTIVE"]
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition from {current_status} to {new_status}"
            )
        
        # If transitioning to DRAINING, no immediate action needed
        # If transitioning to OFFLINE, reassign tasks
        if new_status == "OFFLINE":
            # Get all running/queued tasks for this worker
            tasks = db.query(Task).filter(
                Task.worker_id == worker_id,
                Task.status.in_(["RUNNING", "QUEUED"])
            ).all()
            
            broker = get_broker()
            
            # Reassign tasks back to queue
            for task in tasks:
                # Reset worker_id
                task.worker_id = None
                
                # Requeue if it was running (mark as QUEUED with attempt counter)
                if task.status == "RUNNING":
                    if task.retry_count < task.max_retries:
                        task.status = "QUEUED"
                        task.retry_count += 1
                        # Re-enqueue in Redis
                        broker.enqueue_task(task)
                    else:
                        task.status = "FAILED"
                        task.failed_at = datetime.utcnow()
                        task.error_message = "Worker failed and max retries exceeded"
                # If already QUEUED, leave as is (might already be queued)
            
            db.commit()
        
        # Update worker status
        worker.status = new_status
        worker.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(worker)
        
        # Update in Redis
        broker = get_broker()
        broker.redis.hset(
            f"worker:{worker_id}",
            "status",
            new_status
        )
        
        return WorkerResponse.model_validate(worker)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status update failed: {str(e)}"
        )


@router.delete("/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deregister_worker(
    worker_id: UUID,
    reassign_tasks: bool = Query(True, description="Reassign running tasks to queue"),
    db: Session = Depends(get_db)
):
    """Deregister a worker from the system.
    
    This gracefully removes a worker, optionally reassigning its tasks.
    """
    worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker {worker_id} not found"
        )
    
    try:
        broker = get_broker()
        
        # Reassign tasks if requested
        if reassign_tasks:
            tasks = db.query(Task).filter(
                Task.worker_id == worker_id,
                Task.status.in_(["RUNNING", "QUEUED"])
            ).all()
            
            for task in tasks:
                task.worker_id = None
                
                if task.status == "RUNNING":
                    if task.retry_count < task.max_retries:
                        task.status = "QUEUED"
                        task.retry_count += 1
                        broker.enqueue_task(task)
                    else:
                        task.status = "FAILED"
                        task.failed_at = datetime.utcnow()
                        task.error_message = "Worker deregistered and max retries exceeded"
        
        # Remove from Redis
        broker.deregister_worker(str(worker_id))
        broker.redis.delete(f"worker:{worker_id}")
        broker.redis.delete(f"worker:{worker_id}:tasks")
        
        # Delete from database
        db.delete(worker)
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deregistration failed: {str(e)}"
        )
