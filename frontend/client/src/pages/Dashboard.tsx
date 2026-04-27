import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Play, Zap, CheckCircle, AlertCircle } from "lucide-react";

interface Task {
  id: string;
  instruction: string;
  status: "completed" | "running" | "failed" | "pending";
  timestamp: string;
  duration?: number;
}

export default function Dashboard() {
  const [instruction, setInstruction] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [stats, setStats] = useState({
    tasksRun: 0,
    successRate: 0,
    activeTasks: 0,
  });

  useEffect(() => {
    // Fetch tasks from API
    const fetchTasks = async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_FRONTEND_FORGE_API_URL || "http://localhost:8000"}/api/agent/tasks`
        );
        if (response.ok) {
          const data = await response.json();
          setTasks(data.slice(0, 5)); // Last 5 tasks
          
          // Calculate stats
          const completed = data.filter((t: Task) => t.status === "completed").length;
          const running = data.filter((t: Task) => t.status === "running").length;
          setStats({
            tasksRun: data.length,
            successRate: data.length > 0 ? Math.round((completed / data.length) * 100) : 0,
            activeTasks: running,
          });
        }
      } catch (error) {
        console.error("Failed to fetch tasks:", error);
      }
    };

    fetchTasks();
    const interval = setInterval(fetchTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleRunTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!instruction.trim()) return;

    setIsLoading(true);
    try {
      const response = await fetch(
        `${import.meta.env.VITE_FRONTEND_FORGE_API_URL || "http://localhost:8000"}/api/agent/run`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            instruction: instruction.trim(),
            headless: true,
            provider: "gemini",
            max_steps: 10,
          }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        setInstruction("");
        // Refresh tasks
        const tasksResponse = await fetch(
          `${import.meta.env.VITE_FRONTEND_FORGE_API_URL || "http://localhost:8000"}/api/agent/tasks`
        );
        if (tasksResponse.ok) {
          const tasksData = await tasksResponse.json();
          setTasks(tasksData.slice(0, 5));
        }
      }
    } catch (error) {
      console.error("Failed to run task:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "success";
      case "running":
        return "running";
      case "failed":
        return "failed";
      default:
        return "pending";
    }
  };

  return (
    <div className="p-8 space-y-8">
      {/* Hero Input Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="space-y-4"
      >
        <div>
          <h1 className="text-4xl font-mono font-700 text-foreground mb-2">
            Agent Terminal
          </h1>
          <p className="text-muted text-sm font-mono">
            Execute autonomous browser tasks with precision
          </p>
        </div>

        <form onSubmit={handleRunTask} className="space-y-4">
          <div className="relative">
            <textarea
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              placeholder="Enter task instruction... (e.g., 'Search for React documentation and summarize key concepts')"
              className="w-full h-32 terminal-input resize-none"
              disabled={isLoading}
            />
            <div className="absolute bottom-3 right-3 text-xs text-muted font-mono">
              {instruction.length} / 1000
            </div>
          </div>

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={isLoading || !instruction.trim()}
              className="glow-button flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play className="w-4 h-4" />
              {isLoading ? "Running..." : "Run Task"}
            </button>
            <button
              type="button"
              onClick={() => setInstruction("")}
              className="px-4 py-2 border border-border rounded-sm text-foreground hover:border-primary transition-colors"
              disabled={isLoading}
            >
              Clear
            </button>
          </div>
        </form>
      </motion.div>

      {/* Stat Cards */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-4"
      >
        {/* Tasks Run */}
        <div className="terminal-card p-6 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-muted uppercase">
              Tasks Run
            </span>
            <Zap className="w-4 h-4 text-primary" />
          </div>
          <div className="text-3xl font-mono font-700 text-foreground">
            {stats.tasksRun}
          </div>
          <div className="text-xs text-muted font-mono">
            Total executions
          </div>
        </div>

        {/* Success Rate */}
        <div className="terminal-card p-6 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-muted uppercase">
              Success Rate
            </span>
            <CheckCircle className="w-4 h-4 text-green-500" />
          </div>
          <div className="text-3xl font-mono font-700 text-foreground">
            {stats.successRate}%
          </div>
          <div className="text-xs text-muted font-mono">
            Completion rate
          </div>
        </div>

        {/* Active Tasks */}
        <div className="terminal-card p-6 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-muted uppercase">
              Active Tasks
            </span>
            <AlertCircle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-3xl font-mono font-700 text-foreground">
            {stats.activeTasks}
          </div>
          <div className="text-xs text-muted font-mono">
            Currently running
          </div>
        </div>
      </motion.div>

      {/* Recent Tasks Table */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="terminal-card overflow-hidden"
      >
        <div className="p-6 border-b border-border">
          <h2 className="text-lg font-mono font-700 text-foreground">
            Recent Tasks
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="px-6 py-3 text-left font-mono font-semibold text-muted uppercase text-xs">
                  Task
                </th>
                <th className="px-6 py-3 text-left font-mono font-semibold text-muted uppercase text-xs">
                  Status
                </th>
                <th className="px-6 py-3 text-left font-mono font-semibold text-muted uppercase text-xs">
                  Duration
                </th>
                <th className="px-6 py-3 text-left font-mono font-semibold text-muted uppercase text-xs">
                  Timestamp
                </th>
              </tr>
            </thead>
            <tbody>
              {tasks.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-muted">
                    No tasks yet. Run your first task to get started.
                  </td>
                </tr>
              ) : (
                tasks.map((task) => (
                  <tr
                    key={task.id}
                    className="border-b border-border hover:bg-card/50 transition-colors"
                  >
                    <td className="px-6 py-3 text-foreground truncate max-w-xs">
                      {task.instruction.substring(0, 50)}...
                    </td>
                    <td className="px-6 py-3">
                      <span
                        className={`status-badge ${getStatusColor(task.status)}`}
                      >
                        {task.status}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-muted">
                      {task.duration ? `${task.duration}s` : "-"}
                    </td>
                    <td className="px-6 py-3 text-muted text-xs">
                      {new Date(task.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
}
