"""Worker administration and control service."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.cache.client import RedisClient, get_redis_client
from src.models import Worker, Task


class WorkerState(str, Enum):
    """Worker operational states."""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DRAINING = "DRAINING"
    IDLE = "IDLE"
    DEAD = "DEAD"


class WorkerController:
    """Control and manage worker lifecycle and operations."""

    WORKER_STATE_KEY = "worker:state"
    WORKER_DRAIN_KEY = "worker:drain"
    WORKER_CONFIG_KEY = "worker:config"

    def __init__(self, redis_client: Optional[RedisClient] = None):
        """Initialize worker controller."""
        self.redis = redis_client or get_redis_client()

    def pause_worker(self, db: Session, worker_id: str) -> bool:
        """Temporarily pause a worker (no new tasks assigned).
        
        Args:
            db: Database session
            worker_id: Worker ID
            
        Returns:
            True if pause was successful
        """
        worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
        if not worker:
            return False

        worker.status = "PAUSED"
        db.commit()

        # Store pause state in Redis
        self.redis.hset(
            f"{self.WORKER_STATE_KEY}:{worker_id}",
            mapping={"status": "PAUSED", "paused_at": datetime.utcnow().isoformat()},
        )

        return True

    def resume_worker(self, db: Session, worker_id: str) -> bool:
        """Resume a paused worker.
        
        Args:
            db: Database session
            worker_id: Worker ID
            
        Returns:
            True if resume was successful
        """
        worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
        if not worker:
            return False

        worker.status = "ACTIVE"
        db.commit()

        # Clear pause state in Redis
        self.redis.delete(f"{self.WORKER_STATE_KEY}:{worker_id}")

        return True

    def drain_worker(self, db: Session, worker_id: str) -> bool:
        """Drain worker: finish current tasks then shutdown.
        
        Draining prevents the worker from accepting new tasks while
        allowing it to complete work in progress.
        
        Args:
            db: Database session
            worker_id: Worker ID
            
        Returns:
            True if drain was initiated
        """
        worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
        if not worker:
            return False

        worker.status = "DRAINING"
        db.commit()

        # Mark as draining in Redis
        self.redis.set(f"{self.WORKER_DRAIN_KEY}:{worker_id}", "1", ttl=86400)

        return True

    def is_worker_draining(self, worker_id: str) -> bool:
        """Check if a worker is in draining state.
        
        Args:
            worker_id: Worker ID
            
        Returns:
            True if worker is draining
        """
        return self.redis.get(f"{self.WORKER_DRAIN_KEY}:{worker_id}") is not None

    def update_worker_capacity(
        self,
        db: Session,
        worker_id: str,
        new_capacity: int,
    ) -> bool:
        """Update worker task capacity.
        
        Args:
            db: Database session
            worker_id: Worker ID
            new_capacity: New capacity value
            
        Returns:
            True if update was successful
        """
        worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
        if not worker or new_capacity < 1:
            return False

        worker.capacity = new_capacity
        db.commit()

        # Store in Redis for quick access
        self.redis.hset(
            f"{self.WORKER_CONFIG_KEY}:{worker_id}",
            mapping={"capacity": str(new_capacity)},
        )

        return True

    def update_worker_timeout(
        self,
        db: Session,
        worker_id: str,
        timeout_seconds: int,
    ) -> bool:
        """Update worker task timeout.
        
        Args:
            db: Database session
            worker_id: Worker ID
            timeout_seconds: New timeout in seconds
            
        Returns:
            True if update was successful
        """
        worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
        if not worker or timeout_seconds < 1:
            return False

        # Store timeout configuration
        self.redis.hset(
            f"{self.WORKER_CONFIG_KEY}:{worker_id}",
            mapping={"timeout_seconds": str(timeout_seconds)},
        )

        return True

    def get_worker_logs(
        self,
        worker_id: str,
        limit: int = 100,
    ) -> List[str]:
        """Fetch recent worker logs.
        
        Args:
            worker_id: Worker ID
            limit: Maximum number of log entries
            
        Returns:
            List of recent log messages
        """
        log_key = f"worker:logs:{worker_id}"
        logs = self.redis.lrange(log_key, -limit, -1)
        return logs or []

    def get_worker_status(self, db: Session, worker_id: str) -> Optional[Dict]:
        """Get detailed worker status including current tasks.
        
        Args:
            db: Database session
            worker_id: Worker ID
            
        Returns:
            Dictionary with worker status details or None
        """
        worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
        if not worker:
            return None

        # Get current tasks
        current_tasks = (
            db.query(Task)
            .filter(
                Task.worker_id == worker_id,
                Task.status == "RUNNING",
            )
            .all()
        )

        # Get worker config from Redis
        config_key = f"{self.WORKER_CONFIG_KEY}:{worker_id}"
        config = self.redis.hgetall(config_key) or {}

        return {
            "worker_id": str(worker.worker_id),
            "hostname": worker.hostname,
            "status": worker.status,
            "capacity": worker.capacity,
            "current_load": worker.current_load,
            "current_tasks": len(current_tasks),
            "last_heartbeat": worker.last_heartbeat.isoformat() if worker.last_heartbeat else None,
            "created_at": worker.created_at.isoformat() if worker.created_at else None,
            "is_draining": self.is_worker_draining(str(worker_id)),
            "config": config,
        }

    def get_all_workers_status(self, db: Session) -> List[Dict]:
        """Get status for all workers.
        
        Args:
            db: Database session
            
        Returns:
            List of worker status dictionaries
        """
        workers = db.query(Worker).all()
        return [
            self.get_worker_status(db, str(w.worker_id))
            for w in workers
            if self.get_worker_status(db, str(w.worker_id)) is not None
        ]

    def terminate_worker(self, db: Session, worker_id: str) -> bool:
        """Mark worker as dead (administrative termination).
        
        Args:
            db: Database session
            worker_id: Worker ID
            
        Returns:
            True if termination was successful
        """
        worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
        if not worker:
            return False

        worker.status = "DEAD"
        db.commit()

        # Clean up Redis keys
        self.redis.delete(f"{self.WORKER_STATE_KEY}:{worker_id}")
        self.redis.delete(f"{self.WORKER_DRAIN_KEY}:{worker_id}")

        return True

    def get_worker_task_history(
        self,
        db: Session,
        worker_id: str,
        limit: int = 100,
    ) -> List[Dict]:
        """Get task execution history for a worker.
        
        Args:
            db: Database session
            worker_id: Worker ID
            limit: Maximum number of tasks
            
        Returns:
            List of task execution records
        """
        tasks = (
            db.query(Task)
            .filter(Task.worker_id == worker_id)
            .order_by(Task.completed_at.desc())
            .limit(limit)
            .all()
        )

        history = []
        for task in tasks:
            duration = None
            if task.completed_at and task.started_at:
                duration = (task.completed_at - task.started_at).total_seconds()

            history.append({
                "task_id": str(task.task_id),
                "task_name": task.task_name,
                "status": task.status,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "duration_seconds": duration,
                "retry_count": task.retry_count,
            })

        return history

    def scale_workers(
        self,
        desired_count: int,
    ) -> Dict:
        """Request worker scaling (placeholder for orchestration systems).
        
        Args:
            desired_count: Desired number of workers
            
        Returns:
            Scaling request status
        """
        # This is a placeholder for integration with orchestration systems
        # (Kubernetes, Docker Swarm, etc.)
        return {
            "scaling_requested": True,
            "desired_count": desired_count,
            "message": "Scaling request sent to orchestrator",
        }


# Global instance
_controller: Optional[WorkerController] = None


def get_worker_controller() -> WorkerController:
    """Get global worker controller instance."""
    global _controller
    if _controller is None:
        _controller = WorkerController()
    return _controller
