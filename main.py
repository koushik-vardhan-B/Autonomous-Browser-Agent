#!/usr/bin/env python
"""
Main entry point for the Autonomous Browser Agent.
Can be run from command line or imported as a module.
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from browser_agent.observability.logger import setup_logging, get_log_paths
from browser_agent.orchestration import run_agent


def main():
    """
    Command-line interface for the browser agent.
    """
    parser = argparse.ArgumentParser(
        description="Autonomous Browser Agent - AI-powered web automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Open google.com and search for Python tutorials"
  python main.py "Go to amazon.com and find the price of iPhone 15"
  python main.py "Navigate to news.ycombinator.com and extract the top 5 story titles"
        """
    )
    
    parser.add_argument(
        "instruction",
        type=str,
        nargs="?",
        help="Natural language instruction for the agent"
    )
    
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Launch Streamlit UI instead of CLI mode"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a simple test task"
    )
    
    args = parser.parse_args()
    
    # --- Initialize logging (captures ALL output to log files) ---
    setup_logging()
    log_paths = get_log_paths()
    print(f"[LOG] Logs: agent.log + error.log (in project root)")
    
    # Launch UI mode
    if args.ui:
        print(">>> Launching Streamlit UI...")
        import subprocess
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(Path(__file__).parent / "src" / "browser_agent" / "ui" / "streamlit_app.py")
        ])
        return
    
    # Test mode
    if args.test:
        instruction = "Open google.com and search for 'AI automation'"
        print(f"\n[TEST] Running test task: {instruction}\n")
    elif args.instruction:
        instruction = args.instruction
    else:
        # Interactive mode
        print("\n[AGENT] Autonomous Browser Agent")
        print("=" * 50)
        instruction = input("\nEnter your instruction (or 'quit' to exit):\n> ")
        
        if instruction.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            return
    
    if not instruction.strip():
        print("[ERROR] Error: No instruction provided")
        parser.print_help()
        sys.exit(1)
    
    print(f"\n[TASK] Task: {instruction}")
    print("[RUN] Executing...\n")
    
    try:
        result = run_agent(instruction)
        
        print("\n" + "=" * 50)
        if "error" in result:
            print(f"[ERROR] Error: {result['error']}")
            sys.exit(1)
        else:
            print("[OK] Task completed successfully!")
            print("\n[OUTPUT] Output:")
            print(result.get("output", "No output"))
            print("=" * 50)
    
    except KeyboardInterrupt:
        print("\n\n[WARN] Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Always show log file locations at the end
        print(f"\n{'='*50}")
        print(f"[LOG] Full execution trace : {log_paths['agent_log']}")
        print(f"[LOG] Errors & warnings    : {log_paths['error_log']}")
        print(f"{'='*50}")


if __name__ == "__main__":
    main()
