"""
Structured logging for the browser agent.
Writes to:
  - Console   : INFO+  (brief, clean output)
  - agent.log : DEBUG+ (everything - full execution trace)
  - error.log : ERROR+ (only errors and warnings for quick debugging)
"""

import logging
import sys
import os
import io
from typing import Optional
from datetime import datetime


# ---------------------------------------------------------------------------
# Log directory (project root)
# ---------------------------------------------------------------------------
_LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
AGENT_LOG = os.path.join(_LOG_DIR, 'agent.log')
ERROR_LOG = os.path.join(_LOG_DIR, 'error.log')


class AgentLogger:
    """
    Structured logger for browser agent.
    Provides context-aware logging with agent names and timestamps.
    Outputs to console (INFO+), agent.log (DEBUG+), and error.log (ERROR+).
    """

    _instances = {}

    def __init__(self, name: str = "BrowserAgent", level: int = logging.DEBUG):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Avoid duplicate handlers
        if not self.logger.handlers:
            # --- Console handler (INFO+) - clean, brief format ---
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_fmt = logging.Formatter(
                '%(asctime)s | %(levelname)-7s | %(name)s | %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_fmt)
            self.logger.addHandler(console_handler)

            # --- agent.log handler (DEBUG+) - full execution trace ---
            try:
                file_handler = logging.FileHandler(
                    AGENT_LOG, mode='a', encoding='utf-8'
                )
                file_handler.setLevel(logging.DEBUG)
                file_fmt = logging.Formatter(
                    '%(asctime)s | %(levelname)-7s | %(name)-25s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_fmt)
                self.logger.addHandler(file_handler)
            except Exception as e:
                self.logger.warning(f"Could not create agent.log: {e}")

            # --- error.log handler (WARNING+) - errors only ---
            try:
                error_handler = logging.FileHandler(
                    ERROR_LOG, mode='a', encoding='utf-8'
                )
                error_handler.setLevel(logging.WARNING)
                error_fmt = logging.Formatter(
                    '%(asctime)s | %(levelname)-7s | %(name)-25s | %(message)s\n'
                    '    %(pathname)s:%(lineno)d',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                error_handler.setFormatter(error_fmt)
                self.logger.addHandler(error_handler)
            except Exception as e:
                self.logger.warning(f"Could not create error.log: {e}")

    # --- Standard log methods ---
    def info(self, message: str, agent: Optional[str] = None):
        """Log info message."""
        prefix = f"[{agent}] " if agent else ""
        self.logger.info(f"{prefix}{message}")

    def warning(self, message: str, agent: Optional[str] = None):
        """Log warning message."""
        prefix = f"[{agent}] " if agent else ""
        self.logger.warning(f"{prefix}{message}")

    def error(self, message: str, agent: Optional[str] = None, exc_info: bool = False):
        """Log error message."""
        prefix = f"[{agent}] " if agent else ""
        self.logger.error(f"{prefix}{message}", exc_info=exc_info)

    def debug(self, message: str, agent: Optional[str] = None):
        """Log debug message."""
        prefix = f"[{agent}] " if agent else ""
        self.logger.debug(f"{prefix}{message}")

    # --- Agent lifecycle methods ---
    def agent_start(self, agent_name: str, task: str):
        """Log agent start."""
        self.info(f">>> STARTED: {task}", agent=agent_name)

    def agent_complete(self, agent_name: str, task: str, duration_ms: Optional[float] = None):
        """Log agent completion."""
        duration_str = f" ({duration_ms:.0f}ms)" if duration_ms else ""
        self.info(f"<<< COMPLETED: {task}{duration_str}", agent=agent_name)

    def agent_error(self, agent_name: str, error: str):
        """Log agent error."""
        self.error(f"!!! ERROR: {error}", agent=agent_name)

    def step(self, agent_name: str, step_num: int, description: str):
        """Log a step in an agent's execution."""
        self.info(f"Step {step_num}: {description}", agent=agent_name)

    def tool_call(self, tool_name: str, args: str = ""):
        """Log a tool call."""
        self.debug(f"Tool: {tool_name}({args})", agent="Tools")

    def llm_call(self, provider: str, model: str, key_index: int = 0):
        """Log an LLM API call."""
        self.debug(f"LLM call: {provider}/{model} (key #{key_index})", agent="LLM")

    def browser_action(self, action: str, details: str = ""):
        """Log a browser action."""
        self.debug(f"Browser: {action} {details}", agent="Browser")

    def state_update(self, field: str, value: str):
        """Log a state update."""
        self.debug(f"State: {field} = {value[:100]}", agent="State")

    def separator(self, title: str = ""):
        """Log a visual separator for readability."""
        self.info(f"{'='*60}")
        if title:
            self.info(f"  {title}")
            self.info(f"{'='*60}")


# ---------------------------------------------------------------------------
# PrintLogger: Captures all print() / stdout output and mirrors to agent.log
# ---------------------------------------------------------------------------
class PrintLogger(io.TextIOBase):
    """
    Intercepts print() output and writes it to both the terminal
    and the agent.log file. This captures LangChain's verbose output,
    AgentExecutor chain logs, and any other print() calls.
    """

    def __init__(self, original_stdout, log_file_path: str):
        super().__init__()
        self._original = original_stdout
        self._log_file_path = log_file_path
        self._log_file = None
        try:
            self._log_file = open(log_file_path, 'a', encoding='utf-8')
        except Exception:
            pass  # Fall back to stdout-only

    def write(self, text):
        if text and text.strip():
            # Write to original stdout
            try:
                self._original.write(text)
            except UnicodeEncodeError:
                # Windows cp1252 fallback
                self._original.write(text.encode('ascii', 'replace').decode('ascii'))
            # Mirror to log file (skip messages already written by logging handlers)
            if self._log_file:
                stripped = text.strip()
                # Skip if it looks like it was already written by our log formatter
                # (formatted lines contain "| INFO " or "| WARNING " etc.)
                is_logger_line = any(
                    f"| {lvl}" in stripped
                    for lvl in ["INFO   ", "WARNING", "ERROR  ", "DEBUG  "]
                )
                if not is_logger_line:
                    try:
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        self._log_file.write(f"{timestamp} | PRINT   | {text}")
                        if not text.endswith('\n'):
                            self._log_file.write('\n')
                        self._log_file.flush()
                    except Exception:
                        pass
        elif text:
            # Preserve bare newlines for formatting
            try:
                self._original.write(text)
            except Exception:
                pass
        return len(text) if text else 0

    def flush(self):
        self._original.flush()
        if self._log_file:
            try:
                self._log_file.flush()
            except Exception:
                pass

    def close(self):
        if self._log_file:
            try:
                self._log_file.close()
            except Exception:
                pass

    @property
    def encoding(self):
        return getattr(self._original, 'encoding', 'utf-8')


# ---------------------------------------------------------------------------
# Module-level initialization
# ---------------------------------------------------------------------------

# Global logger instance
_global_logger: Optional[AgentLogger] = None


def get_logger(name: str = "BrowserAgent") -> AgentLogger:
    """
    Get or create a logger instance.
    Uses singleton pattern per name.
    """
    if name not in AgentLogger._instances:
        AgentLogger._instances[name] = AgentLogger(name)
    return AgentLogger._instances[name]


def setup_logging():
    """
    One-time setup: start capturing print() output to agent.log.
    Call this early in main.py before anything else runs.
    Also clears old logs at the start of each run.
    """
    # Clear old log files for a fresh run
    for log_path in [AGENT_LOG, ERROR_LOG]:
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(f"{'='*70}\n")
                f.write(f"  LOG STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"  File: {os.path.basename(log_path)}\n")
                f.write(f"{'='*70}\n\n")
        except Exception:
            pass

    # Redirect stdout to capture all print() calls
    if not isinstance(sys.stdout, PrintLogger):
        sys.stdout = PrintLogger(sys.stdout, AGENT_LOG)


def get_log_paths() -> dict:
    """Return log file paths for reference."""
    return {
        "agent_log": AGENT_LOG,
        "error_log": ERROR_LOG
    }
