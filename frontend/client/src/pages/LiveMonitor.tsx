import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { ChevronDown } from "lucide-react";

interface Step {
  id: number;
  type: "PLANNER" | "EXECUTOR" | "OUTPUT";
  description: string;
  status: "pending" | "running" | "completed" | "failed";
}

interface LogEntry {
  timestamp: string;
  level: "INFO" | "WARN" | "ERROR" | "DEBUG";
  message: string;
}

export default function LiveMonitor() {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [steps, setSteps] = useState<Step[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Auto-scroll logs to bottom
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // Connect to WebSocket for live updates
  useEffect(() => {
    if (!taskId) return;

    const apiUrl =
      import.meta.env.VITE_FRONTEND_FORGE_API_URL || "http://localhost:8000";
    const wsUrl = apiUrl.replace("http", "ws") + `/api/ws/task/${taskId}`;

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setIsRunning(true);
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === "step") {
          setSteps((prev) => {
            const existing = prev.find((s) => s.id === data.step.id);
            if (existing) {
              return prev.map((s) =>
                s.id === data.step.id ? { ...s, ...data.step } : s
              );
            }
            return [...prev, data.step];
          });
        } else if (data.type === "log") {
          setLogs((prev) => [...prev, data.log]);
        } else if (data.type === "complete") {
          setIsRunning(false);
        }
      };

      wsRef.current.onerror = () => {
        setIsRunning(false);
      };

      wsRef.current.onclose = () => {
        setIsRunning(false);
      };

      return () => {
        wsRef.current?.close();
      };
    } catch (error) {
      console.error("WebSocket connection failed:", error);
      setIsRunning(false);
    }
  }, [taskId]);

  const handleStartMonitoring = async () => {
    // In a real app, this would be triggered from Dashboard
    // For now, we'll show a placeholder
    setTaskId("demo-task-001");
    setSteps([
      {
        id: 1,
        type: "PLANNER",
        description: "Analyzing task requirements",
        status: "completed",
      },
      {
        id: 2,
        type: "EXECUTOR",
        description: "Opening browser and navigating to target",
        status: "running",
      },
      {
        id: 3,
        type: "EXECUTOR",
        description: "Extracting data from page",
        status: "pending",
      },
      {
        id: 4,
        type: "OUTPUT",
        description: "Formatting and returning results",
        status: "pending",
      },
    ]);
    setLogs([
      {
        timestamp: new Date().toISOString(),
        level: "INFO",
        message: "Task started: demo-task-001",
      },
      {
        timestamp: new Date().toISOString(),
        level: "INFO",
        message: "Initializing browser agent",
      },
      {
        timestamp: new Date().toISOString(),
        level: "INFO",
        message: "Planner analyzing task requirements",
      },
      {
        timestamp: new Date().toISOString(),
        level: "INFO",
        message: "Opening browser instance",
      },
    ]);
  };

  const getStepBadgeColor = (type: string) => {
    switch (type) {
      case "PLANNER":
        return "bg-blue-500/20 text-blue-300 border-blue-500/30";
      case "EXECUTOR":
        return "bg-amber-500/20 text-amber-300 border-amber-500/30";
      case "OUTPUT":
        return "bg-green-500/20 text-green-300 border-green-500/30";
      default:
        return "bg-slate-500/20 text-slate-300 border-slate-500/30";
    }
  };

  const getLogColor = (level: string) => {
    switch (level) {
      case "INFO":
        return "log-info";
      case "WARN":
        return "log-warn";
      case "ERROR":
        return "log-error";
      case "DEBUG":
        return "log-debug";
      default:
        return "";
    }
  };

  return (
    <div className="p-8 space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-3xl font-mono font-700 text-foreground mb-2">
          Live Monitor
        </h1>
        <p className="text-muted text-sm font-mono">
          Real-time task execution tracking
        </p>
      </motion.div>

      {!taskId ? (
        <div className="terminal-card p-12 text-center space-y-4">
          <p className="text-muted font-mono">No task currently being monitored</p>
          <button
            onClick={handleStartMonitoring}
            className="glow-button mx-auto"
          >
            Start Monitoring Demo Task
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Panel: Task Info & Steps */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="lg:col-span-1 space-y-4"
          >
            {/* Task Info */}
            <div className="terminal-card p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-muted uppercase">
                  Task ID
                </span>
                <motion.div
                  animate={isRunning ? { opacity: [1, 0.5, 1] } : {}}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="w-2 h-2 rounded-full bg-amber-500"
                />
              </div>
              <div className="font-mono text-sm text-foreground break-all">
                {taskId}
              </div>
              <div className="text-xs text-muted font-mono">
                Status: {isRunning ? "RUNNING" : "COMPLETED"}
              </div>
            </div>

            {/* Steps Progress */}
            <div className="terminal-card p-4 space-y-3">
              <h3 className="text-sm font-mono font-700 text-foreground uppercase">
                Execution Plan
              </h3>
              <div className="space-y-2">
                {steps.map((step, index) => (
                  <motion.div
                    key={step.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex gap-3"
                  >
                    <div className="flex flex-col items-center">
                      <div
                        className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-mono font-700 ${
                          step.status === "completed"
                            ? "bg-green-500/20 text-green-300"
                            : step.status === "running"
                              ? "bg-amber-500/20 text-amber-300"
                              : "bg-slate-500/20 text-slate-300"
                        }`}
                      >
                        {index + 1}
                      </div>
                      {index < steps.length - 1 && (
                        <div className="w-0.5 h-8 bg-border my-1" />
                      )}
                    </div>
                    <div className="flex-1 pt-1">
                      <div
                        className={`inline-block px-2 py-1 rounded text-xs font-mono font-semibold mb-1 ${getStepBadgeColor(step.type)}`}
                      >
                        {step.type}
                      </div>
                      <p className="text-xs text-foreground">
                        {step.description}
                      </p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Right Panel: Live Log Feed */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="lg:col-span-2"
          >
            <div className="terminal-card flex flex-col h-full">
              <div className="p-4 border-b border-border flex items-center justify-between">
                <h3 className="text-sm font-mono font-700 text-foreground uppercase">
                  Live Log Feed
                </h3>
                <motion.div
                  animate={isRunning ? { opacity: [1, 0.5, 1] } : {}}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="w-2 h-2 rounded-full bg-green-500"
                />
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-1 font-mono text-xs bg-input">
                {logs.length === 0 ? (
                  <div className="text-muted">Waiting for log entries...</div>
                ) : (
                  logs.map((log, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`${getLogColor(log.level)}`}
                    >
                      <span className="text-muted">
                        [{new Date(log.timestamp).toLocaleTimeString()}]
                      </span>{" "}
                      <span className="text-muted">[{log.level}]</span> {log.message}
                    </motion.div>
                  ))
                )}
                <div ref={logsEndRef} />
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
