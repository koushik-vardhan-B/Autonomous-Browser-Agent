import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Check, X, GripVertical } from "lucide-react";
import { toast } from "sonner";

interface Provider {
  id: string;
  name: string;
  priority: number;
}

export default function Settings() {
  const [geminiKeys, setGeminiKeys] = useState<string[]>(["", "", ""]);
  const [groqKeys, setGroqKeys] = useState<string[]>(["", ""]);
  const [tavilyKey, setTavilyKey] = useState("");
  const [headlessMode, setHeadlessMode] = useState(true);
  const [backendUrl, setBackendUrl] = useState(
    import.meta.env.VITE_FRONTEND_FORGE_API_URL || "http://localhost:8000"
  );
  const [providers, setProviders] = useState<Provider[]>([
    { id: "gemini", name: "Gemini", priority: 1 },
    { id: "groq", name: "Groq", priority: 2 },
    { id: "tavily", name: "Tavily", priority: 3 },
  ]);
  const [connectionStatus, setConnectionStatus] = useState<
    "idle" | "testing" | "success" | "error"
  >("idle");

  // Load settings from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("agentSettings");
    if (saved) {
      try {
        const settings = JSON.parse(saved);
        if (settings.geminiKeys) setGeminiKeys(settings.geminiKeys);
        if (settings.groqKeys) setGroqKeys(settings.groqKeys);
        if (settings.tavilyKey) setTavilyKey(settings.tavilyKey);
        if (settings.headlessMode !== undefined)
          setHeadlessMode(settings.headlessMode);
        if (settings.backendUrl) setBackendUrl(settings.backendUrl);
        if (settings.providers) setProviders(settings.providers);
      } catch (error) {
        console.error("Failed to load settings:", error);
      }
    }
  }, []);

  // Save settings to localStorage whenever they change
  const saveSettings = () => {
    const settings = {
      geminiKeys,
      groqKeys,
      tavilyKey,
      headlessMode,
      backendUrl,
      providers,
    };
    localStorage.setItem("agentSettings", JSON.stringify(settings));
    toast.success("Settings saved successfully");
  };

  const handleTestConnection = async () => {
    setConnectionStatus("testing");
    try {
      const response = await fetch(`${backendUrl}/api/health`);
      if (response.ok) {
        setConnectionStatus("success");
        toast.success("Connected to backend successfully");
        setTimeout(() => setConnectionStatus("idle"), 3000);
      } else {
        setConnectionStatus("error");
        toast.error("Backend returned an error");
        setTimeout(() => setConnectionStatus("idle"), 3000);
      }
    } catch (error) {
      setConnectionStatus("error");
      toast.error("Failed to connect to backend");
      setTimeout(() => setConnectionStatus("idle"), 3000);
    }
  };

  const handleGeminiKeyChange = (index: number, value: string) => {
    const newKeys = [...geminiKeys];
    newKeys[index] = value;
    setGeminiKeys(newKeys);
  };

  const handleGroqKeyChange = (index: number, value: string) => {
    const newKeys = [...groqKeys];
    newKeys[index] = value;
    setGroqKeys(newKeys);
  };

  const handleReorderProviders = (fromIndex: number, toIndex: number) => {
    const newProviders = [...providers];
    const [moved] = newProviders.splice(fromIndex, 1);
    newProviders.splice(toIndex, 0, moved);
    // Update priorities
    const updated = newProviders.map((p, i) => ({ ...p, priority: i + 1 }));
    setProviders(updated);
  };

  return (
    <div className="p-8 space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-3xl font-mono font-700 text-foreground mb-2">
          Settings
        </h1>
        <p className="text-muted text-sm font-mono">
          Configure API keys and agent preferences
        </p>
      </motion.div>

      <div className="space-y-6">
        {/* Backend Configuration */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="terminal-card p-6 space-y-4"
        >
          <h2 className="text-lg font-mono font-700 text-foreground uppercase">
            Backend Configuration
          </h2>

          <div className="space-y-3">
            <label className="block text-sm font-mono text-muted uppercase">
              Backend URL
            </label>
            <input
              type="text"
              value={backendUrl}
              onChange={(e) => setBackendUrl(e.target.value)}
              className="terminal-input w-full"
              placeholder="http://localhost:8000"
            />
          </div>

          <button
            onClick={handleTestConnection}
            disabled={connectionStatus === "testing"}
            className={`flex items-center gap-2 px-4 py-2 rounded-sm font-mono text-sm transition-all ${
              connectionStatus === "success"
                ? "bg-green-500/20 text-green-300 border border-green-500/30"
                : connectionStatus === "error"
                  ? "bg-red-500/20 text-red-300 border border-red-500/30"
                  : "border border-primary text-primary hover:bg-primary/10"
            }`}
          >
            {connectionStatus === "testing" && (
              <div className="animate-spin">⚙️</div>
            )}
            {connectionStatus === "success" && <Check className="w-4 h-4" />}
            {connectionStatus === "error" && <X className="w-4 h-4" />}
            {connectionStatus === "idle" ? "Test Connection" : "Testing..."}
          </button>
        </motion.div>

        {/* API Keys */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="terminal-card p-6 space-y-6"
        >
          <h2 className="text-lg font-mono font-700 text-foreground uppercase">
            API Keys
          </h2>

          {/* Gemini Keys */}
          <div className="space-y-3">
            <label className="block text-sm font-mono text-muted uppercase">
              Gemini API Keys (up to 3)
            </label>
            <div className="space-y-2">
              {geminiKeys.map((key, index) => (
                <input
                  key={`gemini-${index}`}
                  type="password"
                  value={key}
                  onChange={(e) => handleGeminiKeyChange(index, e.target.value)}
                  className="terminal-input w-full"
                  placeholder={`Gemini Key ${index + 1}`}
                />
              ))}
            </div>
          </div>

          {/* Groq Keys */}
          <div className="space-y-3">
            <label className="block text-sm font-mono text-muted uppercase">
              Groq API Keys (up to 2)
            </label>
            <div className="space-y-2">
              {groqKeys.map((key, index) => (
                <input
                  key={`groq-${index}`}
                  type="password"
                  value={key}
                  onChange={(e) => handleGroqKeyChange(index, e.target.value)}
                  className="terminal-input w-full"
                  placeholder={`Groq Key ${index + 1}`}
                />
              ))}
            </div>
          </div>

          {/* Tavily Key */}
          <div className="space-y-3">
            <label className="block text-sm font-mono text-muted uppercase">
              Tavily API Key
            </label>
            <input
              type="password"
              value={tavilyKey}
              onChange={(e) => setTavilyKey(e.target.value)}
              className="terminal-input w-full"
              placeholder="Tavily API Key"
            />
          </div>
        </motion.div>

        {/* Agent Preferences */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="terminal-card p-6 space-y-4"
        >
          <h2 className="text-lg font-mono font-700 text-foreground uppercase">
            Agent Preferences
          </h2>

          <div className="flex items-center justify-between">
            <label className="text-sm font-mono text-foreground">
              Headless Mode
            </label>
            <button
              onClick={() => setHeadlessMode(!headlessMode)}
              className={`relative w-12 h-6 rounded-full transition-colors ${
                headlessMode ? "bg-green-500/30" : "bg-slate-500/30"
              }`}
            >
              <motion.div
                layout
                className={`absolute top-1 w-4 h-4 rounded-full transition-colors ${
                  headlessMode ? "bg-green-500 right-1" : "bg-slate-500 left-1"
                }`}
              />
            </button>
          </div>

          <p className="text-xs text-muted font-mono">
            {headlessMode
              ? "Browser runs in background (faster)"
              : "Browser runs with UI (slower, for debugging)"}
          </p>
        </motion.div>

        {/* Provider Priority */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="terminal-card p-6 space-y-4"
        >
          <h2 className="text-lg font-mono font-700 text-foreground uppercase">
            Provider Priority
          </h2>
          <p className="text-xs text-muted font-mono mb-4">
            Drag to reorder. Higher priority providers are used first.
          </p>

          <div className="space-y-2">
            {providers.map((provider, index) => (
              <motion.div
                key={provider.id}
                draggable
                onDragOver={(e) => e.preventDefault()}
                onDrop={() => {
                  // Simple reorder - in production, use a library like react-beautiful-dnd
                }}
                className="flex items-center gap-3 p-3 border border-border rounded-sm hover:border-primary transition-colors cursor-move"
              >
                <GripVertical className="w-4 h-4 text-muted" />
                <div className="flex-1">
                  <div className="font-mono font-semibold text-foreground">
                    {provider.name}
                  </div>
                  <div className="text-xs text-muted font-mono">
                    Priority: {provider.priority}
                  </div>
                </div>
                <div className="flex gap-1">
                  {index > 0 && (
                    <button
                      onClick={() => handleReorderProviders(index, index - 1)}
                      className="px-2 py-1 text-xs border border-border rounded hover:border-primary transition-colors"
                    >
                      ↑
                    </button>
                  )}
                  {index < providers.length - 1 && (
                    <button
                      onClick={() => handleReorderProviders(index, index + 1)}
                      className="px-2 py-1 text-xs border border-border rounded hover:border-primary transition-colors"
                    >
                      ↓
                    </button>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Save Button */}
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          onClick={saveSettings}
          className="glow-button w-full"
        >
          Save All Settings
        </motion.button>
      </div>
    </div>
  );
}
