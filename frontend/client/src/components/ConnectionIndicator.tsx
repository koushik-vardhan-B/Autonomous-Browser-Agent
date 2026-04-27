import { useEffect, useState } from "react";
import { motion } from "framer-motion";

export default function ConnectionIndicator() {
  const [isConnected, setIsConnected] = useState(true);

  useEffect(() => {
    // Check connection to backend API
    const checkConnection = async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_FRONTEND_FORGE_API_URL || "http://localhost:8000"}/api/health`,
          { method: "GET" }
        );
        setIsConnected(response.ok);
      } catch {
        setIsConnected(false);
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center gap-2">
      <motion.div
        className={`w-3 h-3 rounded-full ${
          isConnected ? "bg-green-500" : "bg-red-500"
        }`}
        animate={
          isConnected
            ? {
                boxShadow: [
                  "0 0 0 0 rgba(74, 222, 128, 0.7)",
                  "0 0 0 8px rgba(74, 222, 128, 0)",
                ],
              }
            : {}
        }
        transition={isConnected ? { duration: 2, repeat: Infinity } : {}}
      />
      <span className="text-xs font-mono text-muted">
        {isConnected ? "Connected" : "Disconnected"}
      </span>
    </div>
  );
}
