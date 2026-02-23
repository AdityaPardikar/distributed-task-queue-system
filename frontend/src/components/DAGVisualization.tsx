/**
 * DAGVisualization — SVG-based Directed Acyclic Graph renderer for workflows.
 * Renders nodes laid out by execution level with animated edges.
 */

import React, { useMemo, useCallback } from "react";
import type { DAGNode, DAGEdge, WorkflowTaskStatus } from "../types/workflow";

/* ── Constants ── */

const NODE_WIDTH = 160;
const NODE_HEIGHT = 64;
const LEVEL_GAP_X = 220;
const NODE_GAP_Y = 90;
const PADDING = 40;
const ARROW_SIZE = 8;

/* ── Colours by status ── */

const STATUS_STYLES: Record<
  WorkflowTaskStatus,
  { fill: string; stroke: string; text: string; badge: string }
> = {
  pending: {
    fill: "#F9FAFB",
    stroke: "#D1D5DB",
    text: "#6B7280",
    badge: "bg-gray-100 text-gray-600",
  },
  running: {
    fill: "#EFF6FF",
    stroke: "#3B82F6",
    text: "#1D4ED8",
    badge: "bg-blue-100 text-blue-700",
  },
  completed: {
    fill: "#F0FDF4",
    stroke: "#22C55E",
    text: "#15803D",
    badge: "bg-green-100 text-green-700",
  },
  failed: {
    fill: "#FEF2F2",
    stroke: "#EF4444",
    text: "#B91C1C",
    badge: "bg-red-100 text-red-700",
  },
  skipped: {
    fill: "#FFFBEB",
    stroke: "#F59E0B",
    text: "#B45309",
    badge: "bg-amber-100 text-amber-700",
  },
};

const EDGE_TYPE_STYLES: Record<string, { stroke: string; dash: string }> = {
  sequential: { stroke: "#6B7280", dash: "" },
  wait_for_all: { stroke: "#3B82F6", dash: "6,3" },
  wait_for_any: { stroke: "#F59E0B", dash: "4,4" },
};

/* ── Helpers ── */

interface PositionedNode extends DAGNode {
  x: number;
  y: number;
}

function layoutNodes(nodes: DAGNode[], levels: string[][]): PositionedNode[] {
  const posMap = new Map<string, { x: number; y: number }>();
  const maxLevelHeight = Math.max(...levels.map((l) => l.length), 1);

  levels.forEach((level, li) => {
    const totalHeight =
      level.length * NODE_HEIGHT +
      (level.length - 1) * (NODE_GAP_Y - NODE_HEIGHT);
    const startY = (maxLevelHeight * NODE_GAP_Y - totalHeight) / 2;

    level.forEach((nodeId, ni) => {
      posMap.set(nodeId, {
        x: PADDING + li * LEVEL_GAP_X,
        y: PADDING + startY + ni * NODE_GAP_Y,
      });
    });
  });

  return nodes.map((n) => {
    const pos = posMap.get(n.id) ?? { x: PADDING, y: PADDING };
    return { ...n, x: pos.x, y: pos.y };
  });
}

function edgePath(
  sourceNode: PositionedNode,
  targetNode: PositionedNode,
): string {
  const sx = sourceNode.x + NODE_WIDTH;
  const sy = sourceNode.y + NODE_HEIGHT / 2;
  const tx = targetNode.x;
  const ty = targetNode.y + NODE_HEIGHT / 2;
  const mx = (sx + tx) / 2;
  return `M ${sx} ${sy} C ${mx} ${sy}, ${mx} ${ty}, ${tx} ${ty}`;
}

/* ── Status icon (inline SVG) ── */

const StatusIcon: React.FC<{ status: WorkflowTaskStatus }> = ({ status }) => {
  switch (status) {
    case "completed":
      return (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="7" stroke="#22C55E" strokeWidth="1.5" />
          <path
            d="M5 8l2 2 4-4"
            stroke="#22C55E"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "running":
      return (
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          className="animate-spin"
        >
          <circle cx="8" cy="8" r="7" stroke="#DBEAFE" strokeWidth="1.5" />
          <path
            d="M8 1a7 7 0 0 1 7 7"
            stroke="#3B82F6"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
      );
    case "failed":
      return (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="7" stroke="#EF4444" strokeWidth="1.5" />
          <path
            d="M6 6l4 4M10 6l-4 4"
            stroke="#EF4444"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
      );
    case "skipped":
      return (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="7" stroke="#F59E0B" strokeWidth="1.5" />
          <path
            d="M5 8h6"
            stroke="#F59E0B"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
      );
    default:
      return (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="7" stroke="#D1D5DB" strokeWidth="1.5" />
          <circle cx="8" cy="8" r="2" fill="#D1D5DB" />
        </svg>
      );
  }
};

/* ── Props ── */

interface DAGVisualizationProps {
  nodes: DAGNode[];
  edges: DAGEdge[];
  executionLevels: string[][];
  onNodeClick?: (nodeId: string) => void;
  selectedNodeId?: string | null;
  className?: string;
}

/* ── Component ── */

const DAGVisualization: React.FC<DAGVisualizationProps> = ({
  nodes,
  edges,
  executionLevels,
  onNodeClick,
  selectedNodeId,
  className = "",
}) => {
  const positioned = useMemo(
    () => layoutNodes(nodes, executionLevels),
    [nodes, executionLevels],
  );

  const nodeMap = useMemo(() => {
    const map = new Map<string, PositionedNode>();
    positioned.forEach((n) => map.set(n.id, n));
    return map;
  }, [positioned]);

  const svgWidth = useMemo(
    () => PADDING * 2 + executionLevels.length * LEVEL_GAP_X,
    [executionLevels],
  );

  const svgHeight = useMemo(() => {
    const maxPerLevel = Math.max(...executionLevels.map((l) => l.length), 1);
    return PADDING * 2 + maxPerLevel * NODE_GAP_Y;
  }, [executionLevels]);

  const handleNodeClick = useCallback(
    (nodeId: string) => {
      onNodeClick?.(nodeId);
    },
    [onNodeClick],
  );

  if (nodes.length === 0) {
    return (
      <div
        className={`flex items-center justify-center h-64 text-gray-400 ${className}`}
      >
        <p>No tasks in this workflow</p>
      </div>
    );
  }

  return (
    <div
      className={`overflow-auto rounded-lg border border-gray-200 bg-white ${className}`}
    >
      <svg
        width={svgWidth}
        height={svgHeight}
        viewBox={`0 0 ${svgWidth} ${svgHeight}`}
        className="min-w-full"
      >
        <defs>
          {/* Arrowhead markers for each edge type */}
          {Object.entries(EDGE_TYPE_STYLES).map(([type, style]) => (
            <marker
              key={type}
              id={`arrow-${type}`}
              viewBox="0 0 10 10"
              refX={ARROW_SIZE}
              refY={ARROW_SIZE / 2}
              markerWidth={ARROW_SIZE}
              markerHeight={ARROW_SIZE}
              orient="auto-start-reverse"
            >
              <path
                d={`M 0 0 L ${ARROW_SIZE} ${ARROW_SIZE / 2} L 0 ${ARROW_SIZE} z`}
                fill={style.stroke}
              />
            </marker>
          ))}
        </defs>

        {/* Edges */}
        <g>
          {edges.map((edge) => {
            const src = nodeMap.get(edge.source);
            const tgt = nodeMap.get(edge.target);
            if (!src || !tgt) return null;
            const style =
              EDGE_TYPE_STYLES[edge.type] ?? EDGE_TYPE_STYLES.sequential;
            return (
              <path
                key={edge.id}
                d={edgePath(src, tgt)}
                fill="none"
                stroke={style.stroke}
                strokeWidth={2}
                strokeDasharray={style.dash}
                markerEnd={`url(#arrow-${edge.type})`}
                className="transition-colors"
              />
            );
          })}
        </g>

        {/* Nodes */}
        <g>
          {positioned.map((node) => {
            const s = STATUS_STYLES[node.status];
            const isSelected = selectedNodeId === node.id;
            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                onClick={() => handleNodeClick(node.id)}
                className="cursor-pointer"
                role="button"
                tabIndex={0}
                aria-label={`Task ${node.name}, status ${node.status}`}
              >
                {/* Selection glow */}
                {isSelected && (
                  <rect
                    x={-4}
                    y={-4}
                    width={NODE_WIDTH + 8}
                    height={NODE_HEIGHT + 8}
                    rx={12}
                    fill="none"
                    stroke="#6366F1"
                    strokeWidth={2}
                    className="animate-pulse"
                  />
                )}
                {/* Card background */}
                <rect
                  width={NODE_WIDTH}
                  height={NODE_HEIGHT}
                  rx={8}
                  fill={s.fill}
                  stroke={s.stroke}
                  strokeWidth={1.5}
                />
                {/* Task name */}
                <text
                  x={12}
                  y={24}
                  fontSize={13}
                  fontWeight={600}
                  fill={s.text}
                  className="select-none"
                >
                  {node.name.length > 16
                    ? node.name.slice(0, 15) + "…"
                    : node.name}
                </text>
                {/* Task handler */}
                <text
                  x={12}
                  y={44}
                  fontSize={10}
                  fill="#9CA3AF"
                  className="select-none"
                >
                  {node.taskName}
                </text>
                {/* Status icon (foreignObject for React SVG) */}
                <foreignObject x={NODE_WIDTH - 28} y={8} width={20} height={20}>
                  <div className="flex items-center justify-center">
                    <StatusIcon status={node.status} />
                  </div>
                </foreignObject>
              </g>
            );
          })}
        </g>
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 px-4 py-3 border-t border-gray-100 text-xs text-gray-500">
        <span className="font-medium text-gray-600">Status:</span>
        {(Object.keys(STATUS_STYLES) as WorkflowTaskStatus[]).map((st) => (
          <span key={st} className="flex items-center gap-1">
            <StatusIcon status={st} />
            <span className="capitalize">{st}</span>
          </span>
        ))}
        <span className="ml-4 font-medium text-gray-600">Edge:</span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-5 border-t-2 border-gray-500" />
          Sequential
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-5 border-t-2 border-dashed border-blue-500" />
          Wait All
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-5 border-t-2 border-dotted border-amber-500" />
          Wait Any
        </span>
      </div>
    </div>
  );
};

export default DAGVisualization;
