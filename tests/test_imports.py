"""
Quick verification script to test all imports from the new modular structure.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

print("=" * 80)
print("TESTING BROWSER AGENT MODULAR IMPORTS")
print("=" * 80)

# Test 1: LLM System
print("\n[1/6] Testing LLM imports...")
try:
    from browser_agent.llm import LLMConfig, LLMRouter
    from browser_agent.llm.providers import GeminiProvider, GroqProvider, SambanovaProvider, OllamaProvider
    print("[OK] LLM imports successful")
except Exception as e:
    print(f"[FAIL] LLM imports failed: {e}")

# Test 2: Core utilities
print("\n[2/6] Testing Core imports...")
try:
    from browser_agent.core import (
        Step, SupervisorOutput, Attribute_Properties,
        build_attributes_model, extract_json_from_markdown,
        load_json_from_file, parse_json_safe,
        AgentState, ExecutionAgentState
    )
    print("[OK] Core imports successful")
except Exception as e:
    print(f"[FAIL] Core imports failed: {e}")

# Test 3: Prompts
print("\n[3/6] Testing Prompt imports...")
try:
    from browser_agent.prompts import (
        get_central_agent_prompt,
        get_central_agent_prompt5,
        get_autonomous_browser_prompt4,
        get_code_analysis_prompt,
        get_vision_analysis_prompt
    )
    print("[OK] Prompt imports successful")
except Exception as e:
    print(f"[FAIL] Prompt imports failed: {e}")

# Test 4: Browser Analysis Tools
print("\n[4/6] Testing Browser Analysis imports...")
try:
    from browser_agent.browser.analysis import (
        ask_human_help,
        open_browser,
        close_browser,
        extract_and_analyze_selectors,
        analyze_using_vision,
        scrape_data_using_text
    )
    print("[OK] Browser Analysis imports successful")
except Exception as e:
    print(f"[FAIL] Browser Analysis imports failed: {e}")

# Test 5: Browser Tools (if they exist)
print("\n[5/6] Testing Browser Tools imports...")
try:
    from browser_agent.browser.tools import (
        enable_vision_overlay,
        find_element_ids,
        click_id,
        fill_id
    )
    print("[OK] Browser Tools imports successful")
except Exception as e:
    print(f"[WARN] Browser Tools not yet migrated (expected): {e}")

# Test 6: Orchestration
print("\n[6/6] Testing Orchestration imports...")
try:
    from browser_agent import run_agent, create_agent, AgentState
    from browser_agent.orchestration import (
        central_agent1,
        execution_agent,
        output_formatting_agent,
        redirector,
        rag
    )
    print("[OK] Orchestration imports successful")
except Exception as e:
    print(f"[FAIL] Orchestration imports failed: {e}")

print("\n" + "=" * 80)
print("IMPORT VERIFICATION COMPLETE")
print("=" * 80)
