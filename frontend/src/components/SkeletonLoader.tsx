/**
 * SkeletonLoader – animated placeholder blocks used during data fetching.
 * Compose <SkeletonLoader.Row />, <SkeletonLoader.Card />, etc. as needed.
 */
import React from "react";

interface SkeletonProps {
  className?: string;
}

/** A single animated shimmer block */
const Block: React.FC<SkeletonProps> = ({ className = "" }) => (
  <div className={`bg-gray-200 rounded animate-pulse ${className}`} />
);

/** A table-row skeleton (n cells) */
const Row: React.FC<{ cols?: number }> = ({ cols = 5 }) => (
  <tr>
    {Array.from({ length: cols }).map((_, i) => (
      <td key={i} className="px-6 py-4">
        <Block className="h-4 w-full max-w-[120px]" />
      </td>
    ))}
  </tr>
);

/** A full table skeleton */
const Table: React.FC<{ rows?: number; cols?: number }> = ({
  rows = 8,
  cols = 5,
}) => (
  <tbody>
    {Array.from({ length: rows }).map((_, i) => (
      <Row key={i} cols={cols} />
    ))}
  </tbody>
);

/** A metric/stat card skeleton */
const Card: React.FC = () => (
  <div className="bg-white rounded-xl shadow-sm p-6 space-y-3">
    <Block className="h-3 w-24" />
    <Block className="h-8 w-32" />
    <Block className="h-3 w-20" />
  </div>
);

/** A grid of metric card skeletons */
const MetricCards: React.FC<{ count?: number }> = ({ count = 4 }) => (
  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
    {Array.from({ length: count }).map((_, i) => (
      <Card key={i} />
    ))}
  </div>
);

/** A chart area skeleton */
const Chart: React.FC<{ height?: string }> = ({ height = "h-64" }) => (
  <div className={`bg-white rounded-xl shadow-sm p-6 ${height}`}>
    <Block className="h-4 w-32 mb-6" />
    <Block className="h-full w-full" />
  </div>
);

const SkeletonLoader = { Block, Row, Table, Card, MetricCards, Chart };
export default SkeletonLoader;
