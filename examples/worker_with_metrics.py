"""Example worker script showing metrics integration."""

import asyncio
import sys
import time
from datetime import datetime

from sqlalchemy.orm import Session

from src.cache.client import get_redis_client
from src.core.broker import get_broker
from src.db.session import SessionLocal
from src.models import Task
from src.monitoring.worker_metrics import get_worker_metrics_tracker
from src.services.worker_service import register_worker, update_worker_heartbeat


async def process_task(db: Session, task_id: str, worker_id: str) -> None:
    """Process a single task with metrics tracking.
    
    Args:
        db: Database session
        task_id: Task identifier
        worker_id: Worker identifier
    """
    tracker = get_worker_metrics_tracker()
    
    # Get task from database
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        return
    
    # Record task start
    tracker.record_task_start(worker_id, task_id, task.task_name)
    
    start_time = time.time()
    success = True
    
    try:
        # Update task status to RUNNING
        task.status = "RUNNING"
        task.started_at = datetime.utcnow()
        db.commit()
        
        # Simulate task execution
        print(f"[{worker_id}] Processing task {task_id} ({task.task_name})")
        await asyncio.sleep(1)  # Simulated work
        
        # Mark task as completed
        task.status = "COMPLETED"
        task.completed_at = datetime.utcnow()
        db.commit()
        print(f"[{worker_id}] Completed task {task_id}")
        
    except Exception as e:
        success = False
        task.status = "FAILED"
        task.error_message = str(e)
        db.commit()
        print(f"[{worker_id}] Failed task {task_id}: {e}")
    
    finally:
        # Record task completion
        duration = time.time() - start_time
        tracker.record_task_complete(
            worker_id,
            task_id,
            task.task_name,
            duration_seconds=duration,
            success=success
        )


async def worker_loop(worker_id: str, db: Session):
    """Main worker loop that processes tasks from queue.
    
    Args:
        worker_id: Worker identifier
        db: Database session
    """
    broker = get_broker()
    tracker = get_worker_metrics_tracker()
    
    print(f"Worker {worker_id} started and listening for tasks...")
    
    while True:
        try:
            # Send heartbeat every iteration
            update_worker_heartbeat(db, worker_id)
            tracker.record_heartbeat(worker_id)
            
            # Try to dequeue task (non-blocking with timeout)
            task_id = broker.dequeue_task(timeout=5)
            
            if task_id:
                await process_task(db, task_id, worker_id)
            else:
                # No tasks available, sleep briefly
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\nWorker {worker_id} shutting down...")
            break
        except Exception as e:
            print(f"Worker {worker_id} error: {e}")
            await asyncio.sleep(5)  # Back off on error


async def main():
    """Start worker with metrics tracking."""
    # Create database session
    db = SessionLocal()
    
    try:
        # Register worker
        worker = register_worker(db, hostname="localhost", capacity=5)
        worker_id = str(worker.worker_id)
        
        print(f"Registered worker: {worker_id}")
        print("View metrics at: http://localhost:8000/api/v1/metrics/workers")
        print(f"Worker-specific metrics: http://localhost:8000/api/v1/metrics/workers/{worker_id}")
        
        # Run worker loop
        await worker_loop(worker_id, db)
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
