/**
 * WorkflowBuilder - Visual workflow creation interface
 * Day 4: Advanced Workflow Engine - Task dependency graph visualization
 */

import React, { useState, useCallback, useMemo } from "react";

// Types
interface TaskNode {
  id: string;
  name: string;
  taskName: string;
  args: unknown[];
  kwargs: Record<string, unknown>;
  priority: number;
  maxRetries: number;
  timeoutSeconds: number;
  position: { x: number; y: number };
  status?: "pending" | "running" | "completed" | "failed";
}

interface TaskEdge {
  id: string;
  source: string;
  target: string;
  type?: "wait_for_all" | "wait_for_any" | "sequential";
}

interface Condition {
  field: string;
  operator: "eq" | "neq" | "gt" | "lt" | "contains" | "exists";
  value?: unknown;
}

interface WorkflowBuilderProps {
  onSave?: (workflow: WorkflowDefinition) => void;
  onCancel?: () => void;
  initialWorkflow?: WorkflowDefinition;
  readOnly?: boolean;
}

interface WorkflowDefinition {
  name: string;
  tasks: TaskNode[];
  edges: TaskEdge[];
  conditions?: Record<string, Condition>;
}

// Task type presets
const TASK_PRESETS = [
  { name: "HTTP Request", taskName: "http_request", icon: "🌐" },
  { name: "Data Process", taskName: "process_data", icon: "⚙️" },
  { name: "File Operation", taskName: "file_op", icon: "📁" },
  { name: "Email Send", taskName: "send_email", icon: "✉️" },
  { name: "Database Query", taskName: "db_query", icon: "🗄️" },
  { name: "Custom Task", taskName: "custom", icon: "🔧" },
];

// Simplified node component
const TaskNodeComponent: React.FC<{
  node: TaskNode;
  selected: boolean;
  onSelect: (id: string) => void;
  onDragStart: (id: string, e: React.MouseEvent) => void;
  onDelete: (id: string) => void;
}> = ({ node, selected, onSelect, onDragStart, onDelete }) => {
  const statusColors = {
    pending: "bg-gray-100 border-gray-300",
    running: "bg-blue-100 border-blue-400",
    completed: "bg-green-100 border-green-400",
    failed: "bg-red-100 border-red-400",
  };

  return (
    <div
      className={`absolute rounded-lg border-2 p-3 cursor-move shadow-md min-w-[160px] transition-all
        ${statusColors[node.status || "pending"]}
        ${selected ? "ring-2 ring-indigo-500 ring-offset-2" : "hover:shadow-lg"}
      `}
      style={{
        left: node.position.x,
        top: node.position.y,
        zIndex: selected ? 10 : 1,
      }}
      onClick={(e) => {
        e.stopPropagation();
        onSelect(node.id);
      }}
      onMouseDown={(e) => {
        if (e.button === 0) {
          onDragStart(node.id, e);
        }
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-lg">
          {TASK_PRESETS.find((p) => p.taskName === node.taskName)?.icon || "📋"}
        </span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(node.id);
          }}
          className="text-gray-400 hover:text-red-500 text-sm"
          title="Delete task"
        >
          ✕
        </button>
      </div>
      <div className="font-medium text-sm truncate">{node.name}</div>
      <div className="text-xs text-gray-500 truncate">{node.taskName}</div>
      <div className="flex gap-1 mt-2">
        <span className="text-xs bg-white/50 px-1 rounded">
          P{node.priority}
        </span>
        <span className="text-xs bg-white/50 px-1 rounded">
          R{node.maxRetries}
        </span>
      </div>
      {/* Connection points */}
      <div
        className="absolute -left-2 top-1/2 w-4 h-4 bg-indigo-500 rounded-full border-2 border-white shadow"
        title="Input"
      />
      <div
        className="absolute -right-2 top-1/2 w-4 h-4 bg-indigo-500 rounded-full border-2 border-white shadow"
        title="Output"
      />
    </div>
  );
};

// Edge SVG component
const EdgeComponent: React.FC<{
  edge: TaskEdge;
  sourcePos: { x: number; y: number };
  targetPos: { x: number; y: number };
  selected: boolean;
  onSelect: (id: string) => void;
}> = ({ edge, sourcePos, targetPos, selected, onSelect }) => {
  // Calculate bezier curve
  const nodeWidth = 160;
  const startX = sourcePos.x + nodeWidth;
  const startY = sourcePos.y + 40;
  const endX = targetPos.x;
  const endY = targetPos.y + 40;

  const controlOffset = Math.abs(endX - startX) / 2;
  const path = `M ${startX} ${startY} C ${startX + controlOffset} ${startY}, ${endX - controlOffset} ${endY}, ${endX} ${endY}`;

  return (
    <g onClick={() => onSelect(edge.id)} style={{ cursor: "pointer" }}>
      <path
        d={path}
        fill="none"
        stroke={selected ? "#6366f1" : "#94a3b8"}
        strokeWidth={selected ? 3 : 2}
        markerEnd="url(#arrowhead)"
      />
      {edge.type && edge.type !== "wait_for_all" && (
        <text
          x={(startX + endX) / 2}
          y={(startY + endY) / 2 - 10}
          className="text-xs fill-gray-500"
          textAnchor="middle"
        >
          {edge.type}
        </text>
      )}
    </g>
  );
};

// Task editor panel
const TaskEditor: React.FC<{
  task: TaskNode | null;
  onUpdate: (task: TaskNode) => void;
  onClose: () => void;
}> = ({ task, onUpdate, onClose }) => {
  const [localTask, setLocalTask] = useState<TaskNode | null>(task);

  React.useEffect(() => {
    setLocalTask(task);
  }, [task]);

  if (!localTask) return null;

  const handleChange = (field: keyof TaskNode, value: unknown) => {
    setLocalTask({ ...localTask, [field]: value });
  };

  const handleSave = () => {
    if (localTask) {
      onUpdate(localTask);
      onClose();
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-xl border p-4 w-80">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">Edit Task</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          ✕
        </button>
      </div>

      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Name
          </label>
          <input
            type="text"
            value={localTask.name}
            onChange={(e) => handleChange("name", e.target.value)}
            className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Task Type
          </label>
          <select
            value={localTask.taskName}
            onChange={(e) => handleChange("taskName", e.target.value)}
            className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            {TASK_PRESETS.map((preset) => (
              <option key={preset.taskName} value={preset.taskName}>
                {preset.icon} {preset.name}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Priority
            </label>
            <input
              type="number"
              min={1}
              max={10}
              value={localTask.priority}
              onChange={(e) =>
                handleChange("priority", parseInt(e.target.value))
              }
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Retries
            </label>
            <input
              type="number"
              min={0}
              max={10}
              value={localTask.maxRetries}
              onChange={(e) =>
                handleChange("maxRetries", parseInt(e.target.value))
              }
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Timeout (seconds)
          </label>
          <input
            type="number"
            min={1}
            max={3600}
            value={localTask.timeoutSeconds}
            onChange={(e) =>
              handleChange("timeoutSeconds", parseInt(e.target.value))
            }
            className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>

        <div className="flex gap-2 pt-2">
          <button
            onClick={handleSave}
            className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
          >
            Save
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded-md hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

// Main WorkflowBuilder component
export const WorkflowBuilder: React.FC<WorkflowBuilderProps> = ({
  onSave,
  onCancel,
  initialWorkflow,
  readOnly = false,
}) => {
  const [workflowName, setWorkflowName] = useState(
    initialWorkflow?.name || "New Workflow",
  );
  const [nodes, setNodes] = useState<TaskNode[]>(initialWorkflow?.tasks || []);
  const [edges, setEdges] = useState<TaskEdge[]>(initialWorkflow?.edges || []);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<string | null>(null);
  const [editingNode, setEditingNode] = useState<TaskNode | null>(null);
  const [dragState, setDragState] = useState<{
    nodeId: string;
    startX: number;
    startY: number;
    offsetX: number;
    offsetY: number;
  } | null>(null);
  const [connectingFrom, setConnectingFrom] = useState<string | null>(null);

  // Generate unique ID
  const generateId = () =>
    `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  // Add new task
  const addTask = useCallback(
    (preset: (typeof TASK_PRESETS)[0]) => {
      const newNode: TaskNode = {
        id: generateId(),
        name: `${preset.name} ${nodes.length + 1}`,
        taskName: preset.taskName,
        args: [],
        kwargs: {},
        priority: 5,
        maxRetries: 3,
        timeoutSeconds: 300,
        position: {
          x: 100 + (nodes.length % 4) * 200,
          y: 100 + Math.floor(nodes.length / 4) * 150,
        },
        status: "pending",
      };
      setNodes([...nodes, newNode]);
      setSelectedNode(newNode.id);
    },
    [nodes],
  );

  // Delete task
  const deleteTask = useCallback(
    (id: string) => {
      setNodes(nodes.filter((n) => n.id !== id));
      setEdges(edges.filter((e) => e.source !== id && e.target !== id));
      if (selectedNode === id) setSelectedNode(null);
    },
    [nodes, edges, selectedNode],
  );

  // Handle node drag
  const handleDragStart = useCallback(
    (nodeId: string, e: React.MouseEvent) => {
      if (readOnly) return;
      const node = nodes.find((n) => n.id === nodeId);
      if (node) {
        setDragState({
          nodeId,
          startX: e.clientX,
          startY: e.clientY,
          offsetX: node.position.x,
          offsetY: node.position.y,
        });
      }
    },
    [nodes, readOnly],
  );

  const handleDrag = useCallback(
    (e: React.MouseEvent) => {
      if (dragState) {
        const dx = e.clientX - dragState.startX;
        const dy = e.clientY - dragState.startY;
        setNodes(
          nodes.map((n) =>
            n.id === dragState.nodeId
              ? {
                  ...n,
                  position: {
                    x: Math.max(0, dragState.offsetX + dx),
                    y: Math.max(0, dragState.offsetY + dy),
                  },
                }
              : n,
          ),
        );
      }
    },
    [dragState, nodes],
  );

  const handleDragEnd = useCallback(() => {
    setDragState(null);
  }, []);

  // Add edge between nodes
  const addEdge = useCallback(
    (sourceId: string, targetId: string) => {
      if (sourceId === targetId) return;
      const exists = edges.some(
        (e) => e.source === sourceId && e.target === targetId,
      );
      if (!exists) {
        setEdges([
          ...edges,
          {
            id: `edge_${sourceId}_${targetId}`,
            source: sourceId,
            target: targetId,
            type: "wait_for_all",
          },
        ]);
      }
    },
    [edges],
  );

  // Delete edge
  const deleteEdge = useCallback(
    (id: string) => {
      setEdges(edges.filter((e) => e.id !== id));
      if (selectedEdge === id) setSelectedEdge(null);
    },
    [edges, selectedEdge],
  );

  // Convert to workflow definition
  const buildWorkflow = useCallback((): WorkflowDefinition => {
    return {
      name: workflowName,
      tasks: nodes,
      edges,
    };
  }, [workflowName, nodes, edges]);

  // Handle save
  const handleSave = useCallback(() => {
    if (onSave) {
      onSave(buildWorkflow());
    }
  }, [onSave, buildWorkflow]);

  // Get node position helper
  const nodePositions = useMemo(() => {
    return nodes.reduce(
      (acc, node) => {
        acc[node.id] = node.position;
        return acc;
      },
      {} as Record<string, { x: number; y: number }>,
    );
  }, [nodes]);

  // Validation
  const validationErrors = useMemo(() => {
    const errors: string[] = [];
    if (!workflowName.trim()) errors.push("Workflow name is required");
    if (nodes.length === 0) errors.push("At least one task is required");

    // Check for cycles (simple DFS)
    const visited = new Set<string>();
    const recStack = new Set<string>();

    const hasCycle = (nodeId: string): boolean => {
      visited.add(nodeId);
      recStack.add(nodeId);

      const outgoing = edges.filter((e) => e.source === nodeId);
      for (const edge of outgoing) {
        if (!visited.has(edge.target)) {
          if (hasCycle(edge.target)) return true;
        } else if (recStack.has(edge.target)) {
          return true;
        }
      }

      recStack.delete(nodeId);
      return false;
    };

    for (const node of nodes) {
      if (!visited.has(node.id)) {
        if (hasCycle(node.id)) {
          errors.push("Workflow contains circular dependencies");
          break;
        }
      }
    }

    return errors;
  }, [workflowName, nodes, edges]);

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Toolbar */}
      <div className="bg-white border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <input
            type="text"
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            className="text-lg font-semibold border-0 border-b-2 border-transparent hover:border-gray-300 focus:border-indigo-500 focus:outline-none px-1 py-0.5"
            placeholder="Workflow Name"
            disabled={readOnly}
          />
          <span className="text-sm text-gray-500">
            {nodes.length} tasks • {edges.length} connections
          </span>
        </div>
        <div className="flex items-center gap-2">
          {validationErrors.length > 0 && (
            <span className="text-sm text-red-500">
              ⚠️ {validationErrors[0]}
            </span>
          )}
          {!readOnly && (
            <>
              {onCancel && (
                <button
                  onClick={onCancel}
                  className="px-4 py-2 border rounded-md hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
              )}
              <button
                onClick={handleSave}
                disabled={validationErrors.length > 0}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                Save Workflow
              </button>
            </>
          )}
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Task palette */}
        {!readOnly && (
          <div className="w-64 bg-white border-r p-4 overflow-y-auto">
            <h3 className="font-semibold text-gray-700 mb-3">Add Task</h3>
            <div className="space-y-2">
              {TASK_PRESETS.map((preset) => (
                <button
                  key={preset.taskName}
                  onClick={() => addTask(preset)}
                  className="w-full flex items-center gap-2 px-3 py-2 bg-gray-50 hover:bg-indigo-50 border rounded-md transition-colors text-left"
                >
                  <span className="text-xl">{preset.icon}</span>
                  <span className="text-sm font-medium">{preset.name}</span>
                </button>
              ))}
            </div>

            <div className="mt-6">
              <h3 className="font-semibold text-gray-700 mb-3">Instructions</h3>
              <ul className="text-sm text-gray-600 space-y-2">
                <li>• Click a task type to add it</li>
                <li>• Drag tasks to position them</li>
                <li>• Click a task to select/edit it</li>
                <li>• Hold Shift + click two tasks to connect them</li>
                <li>• Press Delete to remove selected</li>
              </ul>
            </div>
          </div>
        )}

        {/* Canvas */}
        <div
          className="flex-1 overflow-auto relative"
          onMouseMove={handleDrag}
          onMouseUp={handleDragEnd}
          onMouseLeave={handleDragEnd}
          onClick={() => {
            if (!dragState) {
              setSelectedNode(null);
              setSelectedEdge(null);
            }
          }}
          onKeyDown={(e) => {
            if (e.key === "Delete" || e.key === "Backspace") {
              if (selectedNode) deleteTask(selectedNode);
              if (selectedEdge) deleteEdge(selectedEdge);
            }
          }}
          tabIndex={0}
        >
          {/* SVG for edges */}
          <svg
            className="absolute inset-0 w-full h-full pointer-events-none"
            style={{ minHeight: "600px", minWidth: "800px" }}
          >
            <defs>
              <marker
                id="arrowhead"
                markerWidth="10"
                markerHeight="7"
                refX="9"
                refY="3.5"
                orient="auto"
              >
                <polygon points="0 0, 10 3.5, 0 7" fill="#94a3b8" />
              </marker>
            </defs>
            <g className="pointer-events-auto">
              {edges.map((edge) => {
                const sourcePos = nodePositions[edge.source];
                const targetPos = nodePositions[edge.target];
                if (!sourcePos || !targetPos) return null;
                return (
                  <EdgeComponent
                    key={edge.id}
                    edge={edge}
                    sourcePos={sourcePos}
                    targetPos={targetPos}
                    selected={selectedEdge === edge.id}
                    onSelect={setSelectedEdge}
                  />
                );
              })}
            </g>
          </svg>

          {/* Task nodes */}
          {nodes.map((node) => (
            <TaskNodeComponent
              key={node.id}
              node={node}
              selected={selectedNode === node.id}
              onSelect={(id) => {
                if (connectingFrom && connectingFrom !== id) {
                  addEdge(connectingFrom, id);
                  setConnectingFrom(null);
                } else {
                  setSelectedNode(id);
                }
              }}
              onDragStart={handleDragStart}
              onDelete={deleteTask}
            />
          ))}

          {/* Empty state */}
          {nodes.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <div className="text-4xl mb-2">📋</div>
                <p>Add tasks from the palette to get started</p>
              </div>
            </div>
          )}
        </div>

        {/* Task editor panel */}
        {editingNode && (
          <div className="absolute right-4 top-20">
            <TaskEditor
              task={editingNode}
              onUpdate={(updated) => {
                setNodes(nodes.map((n) => (n.id === updated.id ? updated : n)));
              }}
              onClose={() => setEditingNode(null)}
            />
          </div>
        )}
      </div>

      {/* Status bar */}
      <div className="bg-white border-t px-4 py-2 text-sm text-gray-500 flex items-center justify-between">
        <div>
          {selectedNode &&
            `Selected: ${nodes.find((n) => n.id === selectedNode)?.name}`}
          {selectedEdge && `Selected edge: ${selectedEdge}`}
          {!selectedNode &&
            !selectedEdge &&
            "Click a task or connection to select"}
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={() => {
              if (selectedNode) {
                const node = nodes.find((n) => n.id === selectedNode);
                if (node) setEditingNode(node);
              }
            }}
            disabled={!selectedNode}
            className="text-indigo-600 hover:text-indigo-800 disabled:text-gray-400"
          >
            Edit Task
          </button>
          <button
            onClick={() => setConnectingFrom(selectedNode)}
            disabled={!selectedNode}
            className="text-indigo-600 hover:text-indigo-800 disabled:text-gray-400"
          >
            Connect From
          </button>
        </div>
      </div>
    </div>
  );
};

export default WorkflowBuilder;
