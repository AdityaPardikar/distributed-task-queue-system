"""Advanced workflow engine with dependency graphs, conditional execution, and templates."""

import json
from collections import defaultdict, deque
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
from uuid import uuid4

from sqlalchemy.orm import Session

from src.cache.client import get_redis_client
from src.config import get_settings
from src.core.broker import get_broker
from src.models import Task

settings = get_settings()


class DependencyType(str, Enum):
    """Types of task dependencies."""
    WAIT_FOR_ALL = "wait_for_all"  # Wait for all parent tasks
    WAIT_FOR_ANY = "wait_for_any"  # Wait for any parent task
    SEQUENTIAL = "sequential"      # Execute sequentially


class ConditionOperator(str, Enum):
    """Operators for conditional execution."""
    EQUALS = "eq"
    NOT_EQUALS = "neq"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    CONTAINS = "contains"
    EXISTS = "exists"
    AND = "and"
    OR = "or"


class TaskCondition:
    """Condition for task execution."""
    
    def __init__(
        self,
        field: str,
        operator: ConditionOperator,
        value: Any = None,
        conditions: Optional[List["TaskCondition"]] = None,
    ):
        self.field = field
        self.operator = operator
        self.value = value
        self.conditions = conditions or []
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate condition against context.
        
        Args:
            context: Evaluation context with task results
            
        Returns:
            True if condition is met
        """
        if self.operator == ConditionOperator.AND:
            return all(c.evaluate(context) for c in self.conditions)
        
        if self.operator == ConditionOperator.OR:
            return any(c.evaluate(context) for c in self.conditions)
        
        # Get field value from context
        field_value = self._get_field_value(context, self.field)
        
        if self.operator == ConditionOperator.EXISTS:
            return field_value is not None
        
        if self.operator == ConditionOperator.EQUALS:
            return field_value == self.value
        
        if self.operator == ConditionOperator.NOT_EQUALS:
            return field_value != self.value
        
        if self.operator == ConditionOperator.GREATER_THAN:
            return field_value > self.value
        
        if self.operator == ConditionOperator.LESS_THAN:
            return field_value < self.value
        
        if self.operator == ConditionOperator.CONTAINS:
            return self.value in field_value if field_value else False
        
        return False
    
    def _get_field_value(self, context: Dict[str, Any], field: str) -> Any:
        """Get nested field value from context.
        
        Args:
            context: Context dictionary
            field: Dot-separated field path
            
        Returns:
            Field value or None
        """
        parts = field.split(".")
        value = context
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "field": self.field,
            "operator": self.operator.value,
            "value": self.value,
            "conditions": [c.to_dict() for c in self.conditions] if self.conditions else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskCondition":
        """Create from dictionary."""
        conditions = None
        if data.get("conditions"):
            conditions = [cls.from_dict(c) for c in data["conditions"]]
        
        return cls(
            field=data["field"],
            operator=ConditionOperator(data["operator"]),
            value=data.get("value"),
            conditions=conditions,
        )


class DependencyGraph:
    """Directed acyclic graph for task dependencies."""
    
    def __init__(self):
        self.graph: Dict[str, Set[str]] = defaultdict(set)  # child -> parents
        self.reverse_graph: Dict[str, Set[str]] = defaultdict(set)  # parent -> children
        self.tasks: Dict[str, Dict[str, Any]] = {}
    
    def add_task(
        self,
        task_id: str,
        task_data: Dict[str, Any],
        dependencies: Optional[List[str]] = None,
        dependency_type: DependencyType = DependencyType.WAIT_FOR_ALL,
    ) -> None:
        """Add a task to the graph.
        
        Args:
            task_id: Task identifier
            task_data: Task configuration
            dependencies: List of parent task IDs
            dependency_type: How to handle dependencies
        """
        self.tasks[task_id] = {
            **task_data,
            "dependency_type": dependency_type,
        }
        
        if dependencies:
            for parent_id in dependencies:
                self.graph[task_id].add(parent_id)
                self.reverse_graph[parent_id].add(task_id)
    
    def has_cycle(self) -> bool:
        """Check if graph has a cycle.
        
        Returns:
            True if cycle exists
        """
        visited = set()
        rec_stack = set()
        
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for child in self.reverse_graph.get(node, []):
                if child not in visited:
                    if dfs(child):
                        return True
                elif child in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for task_id in self.tasks:
            if task_id not in visited:
                if dfs(task_id):
                    return True
        
        return False
    
    def topological_sort(self) -> List[str]:
        """Get tasks in topological order.
        
        Returns:
            List of task IDs in execution order
            
        Raises:
            ValueError: If graph has a cycle
        """
        if self.has_cycle():
            raise ValueError("Dependency graph has a cycle")
        
        in_degree = {task_id: len(parents) for task_id, parents in self.graph.items()}
        
        # Add tasks with no dependencies
        for task_id in self.tasks:
            if task_id not in in_degree:
                in_degree[task_id] = 0
        
        queue = deque(task_id for task_id, degree in in_degree.items() if degree == 0)
        result = []
        
        while queue:
            task_id = queue.popleft()
            result.append(task_id)
            
            for child in self.reverse_graph.get(task_id, []):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)
        
        return result
    
    def get_ready_tasks(self, completed: Set[str]) -> List[str]:
        """Get tasks that are ready to execute.
        
        Args:
            completed: Set of completed task IDs
            
        Returns:
            List of task IDs ready for execution
        """
        ready = []
        
        for task_id, task_data in self.tasks.items():
            if task_id in completed:
                continue
            
            parents = self.graph.get(task_id, set())
            dependency_type = task_data.get("dependency_type", DependencyType.WAIT_FOR_ALL)
            
            if not parents:
                ready.append(task_id)
            elif dependency_type == DependencyType.WAIT_FOR_ALL:
                if all(p in completed for p in parents):
                    ready.append(task_id)
            elif dependency_type == DependencyType.WAIT_FOR_ANY:
                if any(p in completed for p in parents):
                    ready.append(task_id)
        
        return ready
    
    def get_execution_levels(self) -> List[List[str]]:
        """Get tasks grouped by execution level (parallel groups).
        
        Returns:
            List of task ID lists, each can be executed in parallel
        """
        sorted_tasks = self.topological_sort()
        levels: List[List[str]] = []
        task_level: Dict[str, int] = {}
        
        for task_id in sorted_tasks:
            parents = self.graph.get(task_id, set())
            
            if not parents:
                level = 0
            else:
                level = max(task_level.get(p, 0) for p in parents) + 1
            
            task_level[task_id] = level
            
            while len(levels) <= level:
                levels.append([])
            
            levels[level].append(task_id)
        
        return levels


class WorkflowTemplate:
    """Reusable workflow template."""
    
    def __init__(
        self,
        template_id: str,
        name: str,
        description: str = "",
        version: str = "1.0.0",
        tasks: Optional[List[Dict[str, Any]]] = None,
        dependencies: Optional[Dict[str, List[str]]] = None,
        conditions: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.template_id = template_id
        self.name = name
        self.description = description
        self.version = version
        self.tasks = tasks or []
        self.dependencies = dependencies or {}
        self.conditions = conditions or {}
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "tasks": self.tasks,
            "dependencies": self.dependencies,
            "conditions": self.conditions,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowTemplate":
        """Create from dictionary."""
        template = cls(
            template_id=data["template_id"],
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            tasks=data.get("tasks", []),
            dependencies=data.get("dependencies", {}),
            conditions=data.get("conditions", {}),
        )
        if "created_at" in data:
            template.created_at = datetime.fromisoformat(data["created_at"])
        return template


class WorkflowTemplateStore:
    """Storage for workflow templates."""
    
    def __init__(self):
        self.redis = get_redis_client()
        self.key_prefix = "workflow_template"
    
    def save(self, template: WorkflowTemplate) -> bool:
        """Save a workflow template.
        
        Args:
            template: Template to save
            
        Returns:
            True if saved
        """
        key = f"{self.key_prefix}:{template.template_id}"
        self.redis.set(key, json.dumps(template.to_dict()))
        
        # Add to index
        self.redis.sadd(f"{self.key_prefix}:index", template.template_id)
        
        return True
    
    def get(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get a template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            Template or None
        """
        key = f"{self.key_prefix}:{template_id}"
        data = self.redis.get(key)
        
        if data:
            return WorkflowTemplate.from_dict(json.loads(data))
        
        return None
    
    def list_all(self) -> List[WorkflowTemplate]:
        """List all templates.
        
        Returns:
            List of templates
        """
        template_ids = self.redis.smembers(f"{self.key_prefix}:index")
        templates = []
        
        for tid in template_ids:
            template = self.get(tid)
            if template:
                templates.append(template)
        
        return templates
    
    def delete(self, template_id: str) -> bool:
        """Delete a template.
        
        Args:
            template_id: Template ID
            
        Returns:
            True if deleted
        """
        key = f"{self.key_prefix}:{template_id}"
        self.redis.delete(key)
        self.redis.srem(f"{self.key_prefix}:index", template_id)
        return True


class TaskChain:
    """Fluent interface for task chaining."""
    
    def __init__(self, initial_task: Dict[str, Any]):
        self.tasks: List[Dict[str, Any]] = [initial_task]
        self.dependencies: Dict[str, List[str]] = {}
        self._current_name: str = initial_task.get("name", "task_0")
    
    def then(
        self,
        task_name: str,
        handler: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        condition: Optional[TaskCondition] = None,
    ) -> "TaskChain":
        """Chain another task after the current one.
        
        Args:
            task_name: Name for the new task
            handler: Task handler name
            args: Task arguments
            kwargs: Task keyword arguments
            condition: Execution condition
            
        Returns:
            Self for chaining
        """
        task_def = {
            "name": task_name,
            "task_name": handler,
            "task_args": args or [],
            "task_kwargs": kwargs or {},
        }
        
        if condition:
            task_def["condition"] = condition.to_dict()
        
        self.tasks.append(task_def)
        self.dependencies[task_name] = [self._current_name]
        self._current_name = task_name
        
        return self
    
    def parallel(
        self,
        tasks: List[Dict[str, Any]],
    ) -> "TaskChain":
        """Add parallel tasks that depend on the current task.
        
        Args:
            tasks: List of task definitions
            
        Returns:
            Self for chaining
        """
        parallel_names = []
        
        for task in tasks:
            task_name = task.get("name", f"parallel_{len(self.tasks)}")
            self.tasks.append({**task, "name": task_name})
            self.dependencies[task_name] = [self._current_name]
            parallel_names.append(task_name)
        
        # Create a join point for the parallel tasks
        join_name = f"join_{len(self.tasks)}"
        self.tasks.append({
            "name": join_name,
            "task_name": "noop",
            "task_args": [],
            "task_kwargs": {},
        })
        self.dependencies[join_name] = parallel_names
        self._current_name = join_name
        
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the workflow definition.
        
        Returns:
            Workflow definition dictionary
        """
        return {
            "tasks": self.tasks,
            "dependencies": self.dependencies,
        }


class AdvancedWorkflowEngine:
    """Enhanced workflow engine with advanced features."""
    
    def __init__(self, db: Session):
        self.db = db
        self.broker = get_broker()
        self.template_store = WorkflowTemplateStore()
        self.redis = get_redis_client()
    
    def create_workflow_from_template(
        self,
        template_id: str,
        workflow_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a workflow from a template.
        
        Args:
            template_id: Template ID
            workflow_name: Name for this workflow instance
            parameters: Parameters to inject into tasks
            
        Returns:
            Created workflow info
        """
        template = self.template_store.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Inject parameters into tasks
        tasks = []
        for task in template.tasks:
            task_copy = {**task}
            
            if parameters:
                # Replace parameter placeholders
                task_copy["task_kwargs"] = {
                    k: parameters.get(v.replace("{{", "").replace("}}", ""), v) 
                    if isinstance(v, str) and v.startswith("{{") else v
                    for k, v in task.get("task_kwargs", {}).items()
                }
            
            tasks.append(task_copy)
        
        return self.create_workflow(
            workflow_name=workflow_name,
            tasks=tasks,
            dependencies=template.dependencies,
            conditions=template.conditions,
        )
    
    def create_workflow(
        self,
        workflow_name: str,
        tasks: List[Dict[str, Any]],
        dependencies: Optional[Dict[str, List[str]]] = None,
        conditions: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Create a workflow with advanced features.
        
        Args:
            workflow_name: Workflow name
            tasks: Task definitions
            dependencies: Task dependencies
            conditions: Execution conditions
            
        Returns:
            Workflow info
        """
        workflow_id = str(uuid4())
        
        # Build dependency graph
        graph = DependencyGraph()
        task_map: Dict[str, Task] = {}
        
        # Create tasks
        for task_def in tasks:
            task_name = task_def.get("name", f"task_{len(task_map)}")
            
            db_task = Task(
                task_name=task_def.get("task_name", "workflow_task"),
                task_args=task_def.get("task_args", []),
                task_kwargs=task_def.get("task_kwargs", {}),
                priority=task_def.get("priority", 5),
                max_retries=task_def.get("max_retries", 5),
                timeout_seconds=task_def.get("timeout_seconds", 300),
                status="PENDING",
            )
            
            self.db.add(db_task)
            self.db.flush()
            
            task_map[task_name] = db_task
            
            # Add to graph
            task_deps = dependencies.get(task_name, []) if dependencies else []
            graph.add_task(
                task_id=task_name,
                task_data={"db_id": str(db_task.task_id)},
                dependencies=task_deps,
            )
        
        # Validate graph
        if graph.has_cycle():
            self.db.rollback()
            raise ValueError("Workflow has circular dependencies")
        
        # Store conditions
        if conditions:
            for task_name, condition_data in conditions.items():
                if task_name in task_map:
                    key = f"workflow:{workflow_id}:condition:{task_name}"
                    self.redis.set(key, json.dumps(condition_data))
        
        # Store workflow metadata
        workflow_data = {
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "task_ids": {name: str(t.task_id) for name, t in task_map.items()},
            "dependencies": dependencies or {},
            "execution_levels": graph.get_execution_levels(),
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self.redis.set(
            f"workflow:{workflow_id}",
            json.dumps(workflow_data),
        )
        
        self.db.commit()
        
        # Enqueue initial tasks (no dependencies)
        for task_name in graph.get_ready_tasks(set()):
            task = task_map[task_name]
            self.broker.enqueue_task(str(task.task_id), priority=task.priority)
        
        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "total_tasks": len(task_map),
            "task_ids": list(workflow_data["task_ids"].values()),
            "execution_levels": workflow_data["execution_levels"],
        }
    
    def on_task_completed(
        self,
        workflow_id: str,
        task_name: str,
        task_result: Any,
    ) -> None:
        """Handle task completion and enqueue dependent tasks.
        
        Args:
            workflow_id: Workflow ID
            task_name: Completed task name
            task_result: Task result
        """
        # Get workflow data
        workflow_data = self.redis.get(f"workflow:{workflow_id}")
        if not workflow_data:
            return
        
        workflow = json.loads(workflow_data)
        
        # Track completion
        completed_key = f"workflow:{workflow_id}:completed"
        self.redis.sadd(completed_key, task_name)
        
        # Store result for condition evaluation
        result_key = f"workflow:{workflow_id}:result:{task_name}"
        self.redis.set(result_key, json.dumps(task_result))
        
        # Find and enqueue ready tasks
        completed = self.redis.smembers(completed_key)
        dependencies = workflow.get("dependencies", {})
        task_ids = workflow.get("task_ids", {})
        
        graph = DependencyGraph()
        for name in task_ids.keys():
            deps = dependencies.get(name, [])
            graph.add_task(name, {"db_id": task_ids[name]}, deps)
        
        for ready_task in graph.get_ready_tasks(completed):
            # Check condition
            if self._evaluate_condition(workflow_id, ready_task):
                task = self.db.query(Task).filter(
                    Task.task_id == task_ids[ready_task]
                ).first()
                
                if task:
                    self.broker.enqueue_task(str(task.task_id), priority=task.priority)
    
    def _evaluate_condition(self, workflow_id: str, task_name: str) -> bool:
        """Evaluate task execution condition.
        
        Args:
            workflow_id: Workflow ID
            task_name: Task name
            
        Returns:
            True if condition is met or no condition exists
        """
        condition_key = f"workflow:{workflow_id}:condition:{task_name}"
        condition_data = self.redis.get(condition_key)
        
        if not condition_data:
            return True
        
        # Build context from completed task results
        context = {}
        results_pattern = f"workflow:{workflow_id}:result:*"
        
        for key in self.redis.keys(results_pattern):
            task = key.split(":")[-1]
            result = self.redis.get(key)
            if result:
                context[task] = json.loads(result)
        
        condition = TaskCondition.from_dict(json.loads(condition_data))
        return condition.evaluate(context)
    
    def get_workflow_visualization(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow visualization data.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Visualization data for frontend
        """
        workflow_data = self.redis.get(f"workflow:{workflow_id}")
        if not workflow_data:
            return {}
        
        workflow = json.loads(workflow_data)
        completed = self.redis.smembers(f"workflow:{workflow_id}:completed")
        
        nodes = []
        edges = []
        
        task_ids = workflow.get("task_ids", {})
        dependencies = workflow.get("dependencies", {})
        
        for name, task_id in task_ids.items():
            task = self.db.query(Task).filter(Task.task_id == task_id).first()
            
            nodes.append({
                "id": name,
                "label": name,
                "status": task.status if task else "UNKNOWN",
                "completed": name in completed,
            })
        
        for child, parents in dependencies.items():
            for parent in parents:
                edges.append({
                    "source": parent,
                    "target": child,
                })
        
        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow.get("workflow_name"),
            "nodes": nodes,
            "edges": edges,
            "execution_levels": workflow.get("execution_levels", []),
        }


def get_advanced_workflow_engine(db: Session) -> AdvancedWorkflowEngine:
    """Get advanced workflow engine instance."""
    return AdvancedWorkflowEngine(db)
