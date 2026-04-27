import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ChevronDown, Download } from "lucide-react";

interface Task {
  id: string;
  instruction: string;
  status: "completed" | "running" | "failed" | "pending";
  duration?: number;
  provider: string;
  timestamp: string;
  output?: string;
}

type SortField = "task" | "status" | "duration" | "provider" | "timestamp";
type SortOrder = "asc" | "desc";

export default function TaskHistory() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [expandedTaskId, setExpandedTaskId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortField, setSortField] = useState<SortField>("timestamp");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  useEffect(() => {
    // Fetch all tasks from API
    const fetchTasks = async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_FRONTEND_FORGE_API_URL || "http://localhost:8000"}/api/agent/tasks`
        );
        if (response.ok) {
          const data = await response.json();
          setTasks(data);
        }
      } catch (error) {
        console.error("Failed to fetch tasks:", error);
      }
    };

    fetchTasks();
    const interval = setInterval(fetchTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortOrder("desc");
    }
  };

  const filteredTasks = tasks.filter(
    (task) => statusFilter === "all" || task.status === statusFilter
  );

  const sortedTasks = [...filteredTasks].sort((a, b) => {
    let aVal: any = sortField === "task" ? a.instruction : (a as any)[sortField];
    let bVal: any = sortField === "task" ? b.instruction : (b as any)[sortField];

    if (sortField === "duration") {
      aVal = a.duration || 0;
      bVal = b.duration || 0;
    } else if (sortField === "task") {
      aVal = a.instruction;
      bVal = b.instruction;
    }

    if (typeof aVal === "string") {
      aVal = aVal.toLowerCase();
      bVal = (bVal as string).toLowerCase();
    }

    if (sortOrder === "asc") {
      return aVal > bVal ? 1 : -1;
    } else {
      return aVal < bVal ? 1 : -1;
    }
  });

  const handleExport = () => {
    const dataStr = JSON.stringify(tasks, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `tasks-${new Date().toISOString().split("T")[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
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

  const SortHeader = ({
    field,
    label,
  }: {
    field: SortField;
    label: string;
  }) => (
    <th
      onClick={() => handleSort(field)}
      className="px-6 py-3 text-left font-mono font-semibold text-muted uppercase text-xs cursor-pointer hover:text-primary transition-colors"
    >
      <div className="flex items-center gap-2">
        {label}
        {sortField === field && (
          <ChevronDown
            className={`w-4 h-4 transition-transform ${
              sortOrder === "desc" ? "" : "rotate-180"
            }`}
          />
        )}
      </div>
    </th>
  );

  return (
    <div className="p-8 space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-3xl font-mono font-700 text-foreground mb-2">
          Task History
        </h1>
        <p className="text-muted text-sm font-mono">
          Complete record of all executed tasks
        </p>
      </motion.div>

      {/* Filter & Export Bar */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between"
      >
        <div className="flex gap-2">
          <label className="text-xs font-mono text-muted uppercase">
            Filter by Status:
          </label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="terminal-input text-sm"
          >
            <option value="all">All</option>
            <option value="completed">Completed</option>
            <option value="running">Running</option>
            <option value="failed">Failed</option>
            <option value="pending">Pending</option>
          </select>
        </div>

        <button
          onClick={handleExport}
          className="flex items-center gap-2 px-4 py-2 border border-primary text-primary hover:bg-primary/10 rounded-sm transition-colors font-mono text-sm"
        >
          <Download className="w-4 h-4" />
          Export JSON
        </button>
      </motion.div>

      {/* Tasks Table */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="terminal-card overflow-hidden"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="px-6 py-3 text-left font-mono font-semibold text-muted uppercase text-xs w-8">
                  {/* Expand icon column */}
                </th>
                <SortHeader field="task" label="Task" />
                <SortHeader field="status" label="Status" />
                <SortHeader field="duration" label="Duration" />
                <SortHeader field="provider" label="Provider" />
                <SortHeader field="timestamp" label="Timestamp" />
              </tr>
            </thead>
            <tbody>
              {sortedTasks.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-muted">
                    No tasks found.
                  </td>
                </tr>
              ) : (
                sortedTasks.map((task) => (
                  <motion.tbody
                    key={task.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    <tr
                      className="border-b border-border hover:bg-card/50 transition-colors cursor-pointer"
                      onClick={() =>
                        setExpandedTaskId(
                          expandedTaskId === task.id ? null : task.id
                        )
                      }
                    >
                      <td className="px-6 py-3">
                        <ChevronDown
                          className={`w-4 h-4 text-muted transition-transform ${
                            expandedTaskId === task.id ? "rotate-180" : ""
                          }`}
                        />
                      </td>
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
                      <td className="px-6 py-3 text-muted">
                        {task.provider || "unknown"}
                      </td>
                      <td className="px-6 py-3 text-muted text-xs">
                        {new Date(task.timestamp).toLocaleString()}
                      </td>
                    </tr>

                    {/* Expanded Row */}
                    {expandedTaskId === task.id && (
                      <tr className="border-b border-border bg-card/50">
                        <td colSpan={6} className="px-6 py-4">
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: "auto" }}
                            exit={{ opacity: 0, height: 0 }}
                            className="space-y-3"
                          >
                            <div>
                              <h4 className="text-xs font-mono font-700 text-muted uppercase mb-2">
                                Full Instruction
                              </h4>
                              <p className="text-sm text-foreground bg-input p-3 rounded-sm font-mono">
                                {task.instruction}
                              </p>
                            </div>

                            {task.output && (
                              <div>
                                <h4 className="text-xs font-mono font-700 text-muted uppercase mb-2">
                                  Output
                                </h4>
                                <div className="text-sm text-foreground bg-input p-3 rounded-sm font-mono max-h-48 overflow-y-auto">
                                  {task.output}
                                </div>
                              </div>
                            )}

                            <div className="grid grid-cols-2 gap-4 text-xs">
                              <div>
                                <span className="text-muted font-mono">ID:</span>
                                <p className="text-foreground font-mono break-all">
                                  {task.id}
                                </p>
                              </div>
                              <div>
                                <span className="text-muted font-mono">
                                  Provider:
                                </span>
                                <p className="text-foreground font-mono">
                                  {task.provider}
                                </p>
                              </div>
                            </div>
                          </motion.div>
                        </td>
                      </tr>
                    )}
                  </motion.tbody>
                ))
              )}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
}
