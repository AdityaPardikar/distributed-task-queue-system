import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import LiveMetricsPanel from "../LiveMetricsPanel";

// Mock useMetricsStream hook
jest.mock("../../hooks/useMetricsStream", () => ({
  useMetricsStream: jest.fn(() => ({
    isConnected: true,
    metrics: {
      totalTasks: 100,
      completedTasks: 80,
      failedTasks: 5,
      pendingTasks: 10,
      runningTasks: 5,
      avgCompletionTime: 1500,
      activeWorkers: 4,
      queueDepth: 15,
      throughput: 10,
      errorRate: 0.05,
      timestamp: Date.now(),
    },
    workerHealthMap: new Map([
      [
        "worker-1",
        {
          workerId: "worker-1",
          status: "healthy",
          cpuUsage: 45.5,
          memoryUsage: 60.2,
          taskCount: 5,
          lastHeartbeat: Date.now(),
          uptime: 3600,
        },
      ],
      [
        "worker-2",
        {
          workerId: "worker-2",
          status: "degraded",
          cpuUsage: 85.0,
          memoryUsage: 90.5,
          taskCount: 3,
          lastHeartbeat: Date.now(),
          uptime: 7200,
        },
      ],
    ]),
    alerts: [
      {
        id: "alert-1",
        severity: "warning",
        message: "High CPU usage on worker-2",
        timestamp: Date.now(),
      },
    ],
    lastUpdate: Date.now(),
    connect: jest.fn(),
    disconnect: jest.fn(),
    clearAlerts: jest.fn(),
  })),
}));

// Store original mock return value
const defaultMockReturnValue = {
  isConnected: true,
  metrics: {
    totalTasks: 100,
    completedTasks: 80,
    failedTasks: 5,
    pendingTasks: 10,
    runningTasks: 5,
    avgCompletionTime: 1500,
    activeWorkers: 4,
    queueDepth: 15,
    throughput: 10,
    errorRate: 0.05,
    timestamp: Date.now(),
  },
  workerHealthMap: new Map([
    [
      "worker-1",
      {
        workerId: "worker-1",
        status: "healthy",
        cpuUsage: 45.5,
        memoryUsage: 60.2,
        taskCount: 5,
        lastHeartbeat: Date.now(),
        uptime: 3600,
      },
    ],
    [
      "worker-2",
      {
        workerId: "worker-2",
        status: "degraded",
        cpuUsage: 85.0,
        memoryUsage: 90.5,
        taskCount: 3,
        lastHeartbeat: Date.now(),
        uptime: 7200,
      },
    ],
  ]),
  alerts: [
    {
      id: "alert-1",
      severity: "warning",
      message: "High CPU usage on worker-2",
      timestamp: Date.now(),
    },
  ],
  lastUpdate: Date.now(),
  connect: jest.fn(),
  disconnect: jest.fn(),
  clearAlerts: jest.fn(),
};

describe("LiveMetricsPanel", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset mock to default implementation
    const useMetricsStreamMock = require("../../hooks/useMetricsStream").useMetricsStream;
    useMetricsStreamMock.mockReturnValue({
      ...defaultMockReturnValue,
      workerHealthMap: new Map(defaultMockReturnValue.workerHealthMap),
    });
  });

  it("renders without crashing", () => {
    render(<LiveMetricsPanel />);
    expect(screen.getByText("Live")).toBeInTheDocument();
  });

  it("displays connection status as Live when connected", () => {
    render(<LiveMetricsPanel />);
    expect(screen.getByText("Live")).toBeInTheDocument();
  });

  it("displays metrics when available", () => {
    render(<LiveMetricsPanel />);
    
    // Check throughput
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("Tasks/min")).toBeInTheDocument();
    
    // Check queue depth
    expect(screen.getByText("15")).toBeInTheDocument();
    expect(screen.getByText("Queue Depth")).toBeInTheDocument();
    
    // Check running tasks
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("Running")).toBeInTheDocument();
    
    // Check error rate
    expect(screen.getByText("5.0%")).toBeInTheDocument();
    expect(screen.getByText("Error Rate")).toBeInTheDocument();
  });

  it("displays worker health section", () => {
    render(<LiveMetricsPanel />);
    
    expect(screen.getByText("Worker Health")).toBeInTheDocument();
    expect(screen.getByText("worker-1")).toBeInTheDocument();
    expect(screen.getByText("worker-2")).toBeInTheDocument();
  });

  it("displays worker stats correctly", () => {
    render(<LiveMetricsPanel />);
    
    // Check CPU usage
    expect(screen.getByText("45.5%")).toBeInTheDocument();
    expect(screen.getByText("85.0%")).toBeInTheDocument();
    
    // Check memory usage
    expect(screen.getByText("60.2%")).toBeInTheDocument();
    expect(screen.getByText("90.5%")).toBeInTheDocument();
    
    // Check task counts
    expect(screen.getByText("5 tasks")).toBeInTheDocument();
    expect(screen.getByText("3 tasks")).toBeInTheDocument();
  });

  it("displays alerts section", () => {
    render(<LiveMetricsPanel />);
    
    expect(screen.getByText("Alerts")).toBeInTheDocument();
    expect(screen.getByText("High CPU usage on worker-2")).toBeInTheDocument();
  });

  it("has clear alerts button", () => {
    render(<LiveMetricsPanel />);
    
    const clearButton = screen.getByText("Clear");
    expect(clearButton).toBeInTheDocument();
  });

  it("calls clearAlerts when clear button is clicked", () => {
    const mockClearAlerts = jest.fn();
    const useMetricsStreamMock = require("../../hooks/useMetricsStream").useMetricsStream;
    useMetricsStreamMock.mockReturnValue({
      isConnected: true,
      metrics: {
        throughput: 10,
        queueDepth: 15,
        runningTasks: 5,
        errorRate: 0.05,
      },
      workerHealthMap: new Map(),
      alerts: [{ id: "1", severity: "info", message: "Test", timestamp: Date.now() }],
      lastUpdate: Date.now(),
      connect: jest.fn(),
      disconnect: jest.fn(),
      clearAlerts: mockClearAlerts,
    });

    render(<LiveMetricsPanel />);
    
    const clearButton = screen.getByText("Clear");
    fireEvent.click(clearButton);
    
    expect(mockClearAlerts).toHaveBeenCalled();
  });

  it("displays uptime in correct format", () => {
    render(<LiveMetricsPanel />);
    
    // worker-1 has 3600 seconds (1h 0m)
    expect(screen.getByText(/Uptime:\s*1h\s*0m/)).toBeInTheDocument();
    // worker-2 has 7200 seconds (2h 0m)
    expect(screen.getByText(/Uptime:\s*2h\s*0m/)).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<LiveMetricsPanel className="custom-class" />);
    
    expect(container.querySelector(".live-metrics-panel.custom-class")).toBeInTheDocument();
  });

  it("shows last update time", () => {
    render(<LiveMetricsPanel />);
    
    expect(screen.getByText(/Last update:/)).toBeInTheDocument();
  });
});

describe("LiveMetricsPanel - Disconnected State", () => {
  it("displays disconnected status when not connected", () => {
    const useMetricsStreamMock = require("../../hooks/useMetricsStream").useMetricsStream;
    useMetricsStreamMock.mockReturnValue({
      isConnected: false,
      metrics: null,
      workerHealthMap: new Map(),
      alerts: [],
      lastUpdate: null,
      connect: jest.fn(),
      disconnect: jest.fn(),
      clearAlerts: jest.fn(),
    });

    render(<LiveMetricsPanel />);
    expect(screen.getByText("Disconnected")).toBeInTheDocument();
  });

  it("shows loading message when disconnected and no data", () => {
    const useMetricsStreamMock = require("../../hooks/useMetricsStream").useMetricsStream;
    useMetricsStreamMock.mockReturnValue({
      isConnected: false,
      metrics: null,
      workerHealthMap: new Map(),
      alerts: [],
      lastUpdate: null,
      connect: jest.fn(),
      disconnect: jest.fn(),
      clearAlerts: jest.fn(),
    });

    render(<LiveMetricsPanel />);
    expect(screen.getByText("Connecting to metrics stream...")).toBeInTheDocument();
  });
});
