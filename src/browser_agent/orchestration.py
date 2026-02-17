"""
LangGraph orchestration for the autonomous browser agent.
This is the main workflow engine that coordinates all agents.
"""

import os
import json
import time
import re
import sys
import asyncio
from urllib.parse import urlparse
from typing import Optional, Literal, List, Annotated, Sequence
from dataclasses import field

import dotenv
import nest_asyncio
from pydantic import BaseModel, Field
from langchain_core.messages import ChatMessage, HumanMessage, BaseMessage, SystemMessage, AIMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
except ImportError:
    # Fallback for newer LangChain versions
    from langchain_core.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.tools.tavily_search import TavilySearchResults
try:
    from langchain_community.vectorstores import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.types import Command
import operator

# Import from new modular structure
from .prompts import get_central_agent_prompt2, get_autonomous_browser_prompt4, get_central_agent_prompt5
from .browser.manager import browser_manager
from .llm import LLMConfig
from .browser.tools import (
    enable_vision_overlay,
    find_element_ids,
    click_id,
    fill_id,
    scroll_one_screen,
    press_key,
    get_page_text,
    hover_element,
    get_visible_input_fields,
    extract_text_from_selector,
    extract_attribute_from_selector,
    select_dropdown_option,
    open_dropdown_and_select
)
from .browser.analysis import (
    open_browser, close_browser,
    extract_and_analyze_selectors, analyze_using_vision, scrape_data_using_text
)
from .core.schemas import Step, SupervisorOutput
from .observability.logger import get_logger

logger = get_logger("Orchestration")

# Windows async fix
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

nest_asyncio.apply()
dotenv.load_dotenv()


def extract_json_from_markdown(text) -> str:
    """Extract JSON from markdown code blocks or raw text, handling trailing data."""
    if not text:
        return "{}"
    text = str(text).strip()

    # 1. Try markdown code block: ```json ... ```
    md_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if md_match:
        candidate = md_match.group(1).strip()
        try:
            json.loads(candidate)
            return candidate
        except (json.JSONDecodeError, ValueError):
            pass  # fall through to other methods

    # 2. Try parsing the full text as-is
    try:
        json.loads(text)
        return text
    except (json.JSONDecodeError, ValueError):
        pass

    # 3. Extract the first complete JSON object {...} using brace matching
    start = text.find('{')
    if start != -1:
        depth = 0
        in_string = False
        escape_next = False
        for i in range(start, len(text)):
            ch = text[i]
            if escape_next:
                escape_next = False
                continue
            if ch == '\\' and in_string:
                escape_next = True
                continue
            if ch == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        json.loads(candidate)
                        return candidate
                    except (json.JSONDecodeError, ValueError):
                        break

    # 4. Fallback — return as-is (will likely fail at json.loads, but caller handles it)
    return text


def get_current_browser_info():
    """
    Directly inspects the open browser to get the current URL and Site Name.
    Source of Truth for where an error actually happened.
    """
    page = browser_manager.get_page()
    
    if page and not page.is_closed():
        try:
            current_url = page.url
            parsed = urlparse(current_url)
            site_name = parsed.netloc.replace("www.", "")
            
            if not site_name:
                site_name = "local_or_unknown"
                
            return current_url, site_name
        except Exception as e:
            print(f"Error reading browser URL: {e}")
            
    return "unknown_url", "unknown_site"


def central_agent1(state):
    """
    Central planning agent - generates step-by-step execution plans.
    Handles: fresh start, phase 2 re-planning, and error recovery.
    """
    import time as _time
    _start = _time.time()
    logger.agent_start("Planner", "Generating execution plan")
    
    user_input = state["user_input"]
    user_input = user_input.replace("{", "{{").replace("}", "}}")
    
    site_names = state.get("site_names", [])
    urls = state.get("urls", [])
    current_plan = state.get("plan", [])
    current_index = state.get("step_index", 0)
    last_error = state.get("last_error", None)
    
    logger.info(f"Step Index: {current_index}, Sites: {site_names}, Last Error: {bool(last_error)}", agent="Planner")
    print(f">>> PLANNING AGENT: Step Index: {current_index}")
   
    if not site_names:
        historical_errors = "No previous errors"
    else:
        vector_db = get_vector_db()
        historical_errors = retrieve_errors(state) if vector_db else "No previous errors"
    historical_errors = historical_errors.replace("{", "{{").replace("}", "}}")

    # Scan current page state
    print(">>> Planner is scanning the page...")
    if browser_manager.get_page():
        try:
            raw_text = browser_manager.get_page().evaluate("document.body.innerText")[:1000]
            current_page_state = f"Page Title: {browser_manager.get_page().title()}\nVisible Text Snippet: {raw_text}..."
        except:
            current_page_state = "Browser is open but page content is unreadable."
    else:
        current_page_state = "Browser is NOT open. First step must be 'Open Browser'."
    current_page_state = current_page_state.replace("{", "{{").replace("}", "}}")

    completed_steps = []
    completed_context_str = ""
    extracted_data_context = ""
    immediate_error_context = ""
    
    parser = JsonOutputParser(pydantic_object=SupervisorOutput)
    instructions = parser.get_format_instructions().replace("{", "{{").replace("}", "}}")

    # Determine planning mode
    if state.get("output_content") and current_index == 0:
        print(">>> PLANNER MODE: PHASE 2 (Data Driven Re-planning)")
        
        if current_plan:
            completed_context_str = "\n### COMPLETED HISTORY (PHASE 1):\n"
            for step in current_plan:
                completed_context_str += f"[OK] Step {step['step_number']}: {step['query']} (Agent: {step['agent']})\n"
        completed_context_str = completed_context_str.replace("{", "{{").replace("}", "}}")
        
        recent_data = state["output_content"][-2:]
        extracted_data_context = f"\n### DATA EXTRACTED SO FAR (Use this to plan Phase 2):\n{str(recent_data)}\n"
        extracted_data_context = extracted_data_context.replace("{", "{{").replace("}", "}}")
        
        completed_steps = []

        system_message = f"""
You are the **Browser Automation Architect**.
We have just completed Phase 1 of the user's request.

USER REQUEST: "{user_input}"

{completed_context_str}

{extracted_data_context}

THE CURRENT PAGE STATE IS:
{current_page_state}

### INSTRUCTIONS FOR PHASE 2:
1. Review the 'COMPLETED HISTORY' and 'DATA EXTRACTED'.
2. Plan the **NEXT** logical actions based on the extracted data.
- Example: If we extracted "Gladiator 2" from IMDB, your next steps should be "Go to YouTube" and "Search for Gladiator 2".
3. **DO NOT** repeat the completed steps.
4. If this next phase also requires a pause for data extraction, the FINAL step of this plan should be agent='PLANNER'.
5. If the task is fully complete, the final step should be agent='end'.

{instructions}
"""
        
    elif last_error:
        print(f">>> PLANNER MODE: ERROR RECOVERY (Step {current_index} Failed)")
        
        if current_plan:
            completed_steps = current_plan[:current_index]
            print(f">>> RETAINING {len(completed_steps)} SUCCESSFUL STEPS.")
        
        completed_context_str = "\nTHE FOLLOWING STEPS ARE ALREADY COMPLETED. DO NOT RE-PLAN THEM:\n"
        for step in completed_steps:
            completed_context_str += f"- Step {step['step_number']}: {step['query']}\n"
            
        immediate_error_context = (
            f"\n\nCRITICAL FAILURE IN PREVIOUS ATTEMPT:\n"
            f"The execution failed at Step {current_index + 1} with error: {last_error}\n"
            f"YOU MUST GENERATE A NEW PLAN STARTING FROM STEP {current_index + 1} THAT FIXES THIS ERROR."
        )

        completed_context_str = completed_context_str.replace("{", "{{").replace("}", "}}")
        immediate_error_context = immediate_error_context.replace("{", "{{").replace("}", "}}")
        
        system_message = f"""
You are the **Browser Automation Architect**.
We are in the middle of an execution that encountered an error.

USER REQUEST: "{user_input}"

{completed_context_str}

{immediate_error_context}

THE CURRENT PAGE STATE IS:
{current_page_state}

### INSTRUCTIONS FOR REFINEMENT:
1. **IGNORE** the completed steps in your output JSON (they are kept automatically).
2. **GENERATE ONLY** the remaining steps needed to fix the error and finish.
3. The first step of your new plan must address the error described above.

{instructions}
"""
    else:
        print(">>> PLANNER MODE: FRESH START")
        completed_steps = []
        system_message = get_central_agent_prompt5(user_input, historical_errors, instructions)
    
    # LLM rotation
    start_index = state.get("current_model_index", 0)
    provider = state.get("llm_provider", None)
    llm_rotation = LLMConfig.get_main_llm_with_rotation(start_index, provider=provider)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "Please generate the plan."),
        MessagesPlaceholder(variable_name="chat_history"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])

    # Get Tavily API key from environment
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        raise ValueError("TAVILY_API_KEY not found in environment variables")
    
    tavily = TavilySearchResults(tavily_api_key=tavily_key)
    tools = [tavily, close_browser]

    # Sanitize message history
    sanitized_history = []
    for msg in state["messages"]:
        raw_content = msg.content if msg.content is not None else ""
        sanitized_content = raw_content.replace("{", "{{").replace("}", "}}")
        if isinstance(msg, (HumanMessage, AIMessage)):
            sanitized_history.append(type(msg)(content=sanitized_content))
        else:
            sanitized_history.append(HumanMessage(content=sanitized_content))

    last_error = None
    for idx, (model_name, current_llm) in enumerate(llm_rotation):
        try:
            print(f"\n>>> Central Agent trying {model_name} (index {start_index + idx})...")
            
            agent = create_tool_calling_agent(current_llm, tools, prompt)
            executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                max_iterations=30,
                handle_parsing_errors=True,
                return_intermediate_steps=True
            )

            response = executor.invoke({"chat_history": sanitized_history})
            
            raw_output = response.get("output") if isinstance(response, dict) else None
            if not raw_output:
                raise ValueError("Planner LLM returned empty output — retrying with next key")
            
            successful_index = (start_index + idx) % len(llm_rotation)
            print(f">>> [OK] Success with {model_name}")
            
            # Parse response
            clean_json = extract_json_from_markdown(raw_output)
            result = json.loads(clean_json)
            
            detected_urls = result.get("target_urls", [])
            detected_sites = result.get("site_names", [])
            new_steps = result.get("steps", result) if isinstance(result, dict) else result
            
            if not isinstance(new_steps, list):
                new_steps = []

            # Store error resolution in RAG
            if state.get("last_error") and len(new_steps) > 0:
                vector_db = get_vector_db()
                if vector_db:
                    try:
                        url, site_name = get_current_browser_info()
                        fix_action = new_steps[0].get('query', 'Unknown Action')
                        rag_content = f"Error Encountered: {state.get('last_error')}\\nSuccessful Fix/Next Step: {fix_action}"
                        doc = Document(
                            page_content=rag_content,
                            metadata={
                                "url": url, "site_name": site_name,
                                "type": "error_resolution", "related_step_index": current_index
                            }
                        )
                        vector_db.add_documents([doc])
                        print(f">>> SAVED ERROR & SOLUTION TO RAG")
                    except Exception as e:
                        print(f"RAG Save Failed: {e}")

            # Combine with completed steps
            final_plan = completed_steps + new_steps
            
            for i, step in enumerate(final_plan):
                step['step_number'] = i + 1

            logger.agent_complete("Planner", f"Plan generated: {len(new_steps)} new steps, {len(final_plan)} total", (_time.time() - _start) * 1000)
            for s in new_steps:
                logger.debug(f"  Step {s.get('step_number','?')}: [{s.get('agent','?')}] {s.get('query','?')[:80]}", agent="Planner")
            print(f">>> PLAN GENERATED. New Steps: {len(new_steps)}, Total Steps: {len(final_plan)}")
            
            return {
                "plan": final_plan,
                "step_index": len(completed_steps),
                "last_error": None,
                "urls": detected_urls,
                "site_names": detected_sites,
                "current_model_index": successful_index,
                "messages": [HumanMessage(content=f"[Planner]: Plan updated. Phase steps: {len(new_steps)}.")]
            }
            
        except Exception as e:
            error_str = str(e).lower()
            last_error = str(e)
            
            if "429" in error_str or "413" in error_str or "rate limit" in error_str or "quota" in error_str or "resource_exhausted" in error_str or "request too large" in error_str or "empty output" in error_str:
                logger.warning(f"Rate limit / size limit hit on {model_name}, rotating...", agent="Planner")
                print(f">>> [WARN] Rate limit or transient error on {model_name}, rotating to next key...")
                continue
            else:
                logger.agent_error("Planner", f"Planning error: {e}")
                print(f">>> [FAIL] Planning Error (non-rate-limit): {e}")
                break

    # All keys exhausted
    print(f">>> All API keys exhausted or planning failed. Last error: {last_error}")
    final_plan = current_plan

    return {
        "plan": final_plan,
        "step_index": len(completed_steps),
        "last_error": None,
        "urls": detected_urls if 'detected_urls' in locals() else [],
        "site_names": detected_sites if 'detected_sites' in locals() else [],
        "messages": [HumanMessage(content=f"[Planner]: Planning failed. Using existing plan.")]
    }


def redirector(state):
    """
    Traffic controller - routes execution between agents based on current step.
    """
    logger.debug("Redirector invoked", agent="Redirector")
    print(">>>> Redirector WORKING")
    plan = state["plan"]
    index = state["step_index"]
    steps = plan
    
    if index >= len(plan):
        print("Plan execution completed.")
        return Command(goto=END)

    step = plan[index]
    logger.step("Redirector", index + 1, f"[{step['agent']}] {step['query'][:80]}")
    print(f"Executing step {index + 1}/{len(steps)} → {step['agent']}: {step['query']}")
    next_step_update = {"step_index": index + 1}
    
    if step["agent"] == "PLANNER":
        print(">>> Step is 'PLANNER'. Resetting plan and sending back to Architect.")
        return Command(
            update={
                "step_index": 0,
                "messages": [HumanMessage(content="Phase 1 complete. Data extracted. Please plan Phase 2.")]
            },
            goto="planner"
        )
    elif step["agent"] == "RAG":
        message_content = step["rag_message"] or step["query"]
        new_msg = HumanMessage(content=message_content)
        return Command(goto="rag_agent", update={**next_step_update, "rag_messages": [new_msg]})
    elif step["agent"] == "EXECUTION":
        new_msg = HumanMessage(content=step["query"])
        return Command(goto="executor", update={**next_step_update, "execution_messages": [new_msg]})
    elif step["agent"] == "OUTPUT_FORMATTING":
        new_msg = HumanMessage(content=step["query"])
        content_to_append = step.get("content", "")
        new_content_list = state["output_content"] + [content_to_append] if content_to_append else state["output_content"]
        return Command(goto="output_agent", update={**next_step_update, "output_agent_messages": [new_msg], "output_content": new_content_list})
    elif step["agent"] == "end":
        return Command(goto=END, update={"step_index": 0, "plan": []})
    else:
        error_msg = f"Error at step {index}: Unknown agent {step['agent']}"
        return Command(
            update={"messages": [ChatMessage(role="redirector", content=error_msg)]},
            goto="planner"
        )


def execution_agent(state):
    """
    Browser automation worker - executes actions using tools.
    """
    import time as _time
    _start = _time.time()
    task_msg = state["execution_messages"][-1]
    task = task_msg.content if hasattr(task_msg, 'content') else str(task_msg)
    logger.agent_start("Executor", task[:100])
    task = task.replace("{", "{{").replace("}", "}}")
    
    sanitized_history = []
    for msg in state["execution_messages"][:-1]:
        if isinstance(msg, HumanMessage) or isinstance(msg, AIMessage):
            sanitized_history.append(msg)
        else:
            sanitized_history.append(HumanMessage(content=str(msg.content)))
    
    # Get Tavily API key from environment
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        raise ValueError("TAVILY_API_KEY not found in environment variables")
    
    tavily = TavilySearchResults(tavily_api_key=tavily_key)
    tools = [
        tavily,
        enable_vision_overlay,
        find_element_ids,
        click_id,
        fill_id,
        scroll_one_screen,
        press_key,
        get_page_text,
        open_browser,
        scrape_data_using_text,
        analyze_using_vision,
        extract_and_analyze_selectors,
        hover_element,
        get_visible_input_fields,
        extract_text_from_selector,
        extract_attribute_from_selector,
        select_dropdown_option,
        open_dropdown_and_select
    ]
    
    start_index = state.get("current_model_index", 0)
    provider = state.get("llm_provider", None)
    llm_rotation = LLMConfig.get_execution_llm_with_rotation(start_index, provider=provider)
    
    last_error = None
    for idx, (model_name, current_llm) in enumerate(llm_rotation):
        try:
            logger.llm_call(model_name.split('/')[0] if '/' in model_name else model_name, model_name, start_index + idx)
            print(f"\n>>> Execution Agent trying {model_name} (index {start_index + idx})...")
            
            agent = create_tool_calling_agent(current_llm, tools, get_autonomous_browser_prompt4())
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                max_iterations=30,
                handle_parsing_errors=True,
                return_intermediate_steps=True
            )

            print(f">>> Starting Execution Agent Task {state['step_index']}...")
            result = agent_executor.invoke({"input": task, "chat_history": []})
            
            successful_index = (start_index + idx) % len(llm_rotation)
            logger.agent_complete("Executor", f"Success with {model_name}", (_time.time() - _start) * 1000)
            print(f">>> [OK] Success with {model_name}")
            
            output_text = result.get("output", "") or ""
            print("\n>>> FINAL OUTPUT:")
            output_lower = output_text.lower()
            trigger_word = next((w for w in ["unable", "error", "couldn't", "failed", "execution failed"] if w in output_lower), None)
            
            if trigger_word:
                if "no error" not in output_lower:
                    print(f"\n>>> Execution Agent Error: Detected potential failure keyword '{trigger_word}'")
                    return Command(
                        update={"last_error": output_text, "current_model_index": successful_index},
                        goto="planner"
                    )
            
            new_msg = ChatMessage(role="execution_agent", content=output_text)
            
            update_dict = {"execution_messages": [new_msg], "messages": [new_msg], "current_model_index": successful_index}
            extracted_data = []
            
            if "intermediate_steps" in result:
                for action, observation in result["intermediate_steps"]:
                    if action.tool in ["scrape_data_using_text", "analyze_using_vision", "extract_and_analyze_selectors"]:
                        content = json.dumps(observation) if isinstance(observation, (dict, list)) else str(observation)
                        extracted_data.append(content)

            if not extracted_data and len(output_text) > 20 and ("{" in output_text or "[" in output_text):
                extracted_data = [output_text]

            if extracted_data:
                update_dict["output_content"] = extracted_data

            return Command(update=update_dict, goto="redirector")
            
        except Exception as e:
            error_str = str(e).lower()
            last_error = str(e)
            
            if "429" in error_str or "413" in error_str or "rate limit" in error_str or "quota" in error_str or "resource_exhausted" in error_str or "request too large" in error_str:
                logger.warning(f"Rate limit / size limit hit on {model_name}, rotating...", agent="Executor")
                print(f">>> [WARN] Rate limit or size limit on {model_name}, rotating to next key...")
                continue
            elif "failed to call a function" in error_str or "tool_call" in error_str or "model_not_found" in error_str or "does not exist" in error_str:
                # Tool calling format issue or model unavailable — try next model
                logger.warning(f"Tool/model error on {model_name}, trying next model...", agent="Executor")
                print(f">>> [WARN] Tool/model error on {model_name}, rotating to next model...")
                continue
            else:
                error_msg = f"AGENT CRASHED: {str(e)}"
                logger.agent_error("Executor", error_msg)
                print(f"\n>>> {error_msg}")
                new_msg = ChatMessage(role="execution_agent", content=error_msg)
                
                return Command(
                    update={
                        "execution_messages": [new_msg],
                        "messages": [new_msg],
                        "step_index": state["step_index"],
                        "last_error": error_msg
                    },
                    goto="planner"
                )

    print(f"\n>>> ALL API KEYS EXHAUSTED. Last error: {last_error}")
    final_msg = ChatMessage(
        role="execution_agent",
        content=f"All API keys exhausted due to rate limits. Last error: {last_error}"
    )
    
    return Command(
        update={
            "messages": [final_msg],
            "last_error": f"ALL KEYS EXHAUSTED: {last_error}"
        },
        goto=END
    )


def output_formatting_agent(state):
    """
    Data formatter - converts raw scraped data into structured JSON/CSV.
    """
    import time as _time
    _start = _time.time()
    logger.agent_start("OutputFormatter", "Formatting extracted data")
    print(">>> OUTPUT FORMATTING AGENT")
    
    input_message = state["output_agent_messages"][-1]
    if hasattr(input_message, 'content'):
        input_message = input_message.content
    else:
        input_message = str(input_message)
    
    content_to_format = state["output_content"] if state["output_content"] else "No content to format."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a data extraction specialist. \nINSTRUCTIONS:\n{instructions}"),
        ("human", "RAW DATA:\n{data}")
    ])
    
    start_index = state.get("current_model_index", 0)
    provider = state.get("llm_provider", None)
    llm_rotation = LLMConfig.get_main_llm_with_rotation(start_index, provider=provider)
    
    last_error = None
    for idx, (model_name, current_llm) in enumerate(llm_rotation):
        try:
            print(f"\n>>> Output Formatting trying {model_name} (index {start_index + idx})...")
            
            chain = prompt | current_llm
            result = chain.invoke({"instructions": input_message, "data": content_to_format})
            formatted_output = result.content
    
            successful_index = (start_index + idx) % len(llm_rotation)
            logger.agent_complete("OutputFormatter", f"Formatted with {model_name}", (_time.time() - _start) * 1000)
            print(f">>> [OK] Success with {model_name}")
            print(f">>> Formatted Output: {formatted_output[:100]}...")
            
            return Command(
                update={"Output": formatted_output, "current_model_index": successful_index},
                goto="redirector"
            )
            
        except Exception as e:
            error_str = str(e).lower()
            last_error = str(e)
            
            if "429" in error_str or "rate limit" in error_str or "quota" in error_str or "resource_exhausted" in error_str:
                print(f">>> [WARN] Rate limit hit on {model_name}, rotating to next key...")
                continue
            else:
                print(f">>> [FAIL] Formatting Error: {e}")
                break
    
    print(f">>> Formatting failed. Last error: {last_error}")
    return Command(
        update={"Output": f"Formatting failed: {last_error}"},
        goto="redirector"
    )


# Lazy loading vector DB
_vector_db_instance = None

def get_vector_db():
    """
    Lazy load the vector database only when needed.
    This eliminates the startup delay from loading HuggingFaceEmbeddings and Chroma.
    Returns None if ChromaDB dependencies are not installed.
    """
    global _vector_db_instance
    
    if not HAS_CHROMADB:
        # ChromaDB dependencies not installed (disabled for Python 3.10 compatibility)
        return None
    
    if _vector_db_instance is None:
        try:
            print(">>> Initializing vector database (first use only)...")
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            _vector_db_instance = Chroma(
                persist_directory="./rag_data",
                embedding_function=embeddings,
                collection_name="agent_memories"
            )
            print(">>> Vector database initialized successfully.")
        except Exception as e:
            print(f"Error loading vector database: {str(e)}")
            _vector_db_instance = None
    
    return _vector_db_instance


def rag(state):
    """
    RAG agent - stores execution context and errors in vector database.
    """
    print(">>> RAG WORKING")
    rag_content = state["rag_messages"][-1]
    if hasattr(rag_content, 'content'):
        rag_content = rag_content.content
    else:
        rag_content = str(rag_content)
    
    url, site_name = get_current_browser_info()
    
    plan = state.get("plan", [])
    index = state.get("step_index", 0)
    
    if index < len(plan):
        task = plan[index]['query']
        agent = plan[index]['agent']
    else:
        task = "Unknown"
        agent = "Unknown"

    doc = Document(
        page_content=str(rag_content),
        metadata={
            "url": url,
            "site_name": site_name,
            "task": task,
            "agent": agent
        }
    )
    
    vector_db = get_vector_db()
    if vector_db:
        vector_db.add_documents([doc])
    
    return Command(
        update={"messages": [ChatMessage(role="RAG Agent", content=f"Memory Saved: '{rag_content[:50]}...'")]},
        goto="redirector"
    )


def retrieve_errors(state):
    """
    Retrieve past errors and solutions from RAG for current sites.
    """
    current_sites = state.get("site_names", [])
    if not current_sites:
        return "No specific sites identified yet."

    vector_db = get_vector_db()
    if not vector_db:
        return "Vector database not available."

    combined_errors = "PAST ERRORS/LESSONS:\n"
    found_any = False

    for site in current_sites:
        try:
            results = vector_db.similarity_search(
                query="error failure issue fix",
                k=3,
                filter={"site_name": site}
            )
            if results:
                found_any = True
                combined_errors += f"\n--- For {site} ---\n"
                for i, doc in enumerate(results):
                    prev_task = doc.metadata.get('task', 'General Task')
                    combined_errors += f"{i+1}. [Task: {prev_task}]: {doc.page_content}\n"
        except Exception as e:
            print(f"Error retrieving for {site}: {e}")

    if not found_any:
        return "No previous errors found for these sites."
            
    return combined_errors


class AgentState(MessagesState):
    """
    LangGraph state shared across all agents.
    """
    user_input: str
    urls: Annotated[List[str], operator.add]
    site_names: Annotated[List[str], operator.add]
    step_index: int
    plan: List[dict]
    execution_messages: Annotated[List[BaseMessage], operator.add]
    rag_messages: Annotated[List[BaseMessage], operator.add]
    output_agent_messages: Annotated[List[BaseMessage], operator.add]
    output_content: Annotated[List[str], operator.add]
    Output: str
    last_error: Optional[str] = None
    current_model_index: int = 0  # Track rotation index
    llm_provider: Optional[str] = None  # Optional provider filter


def create_agent():
    """
    Creates the LangGraph workflow connecting all agents.
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("planner", central_agent1)
    workflow.add_node("executor", execution_agent)
    workflow.add_node("output_agent", output_formatting_agent)
    workflow.add_node("redirector", redirector)
    workflow.add_node("rag_agent", rag)
    
    # Add edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "redirector")
    
    # Command-based routing (no static edges from redirector)
    app = workflow.compile()
    return app


def run_agent(input_str: str):
    """
    Main entry point - runs the autonomous browser agent.
    
    Args:
        input_str: Natural language instruction
        
    Returns:
        Dict with 'output' or 'error' key
    """
    import time as _time
    _run_start = _time.time()
    logger.separator("AGENT RUN STARTED")
    logger.info(f"User Input: {input_str[:200]}", agent="Main")
    
    state = {
        "user_input": input_str,
        "site_names": [],
        "urls": [],
        "plan": [],
        "messages": [],
        "step_index": 0,
        "execution_messages": [],
        "rag_messages": [],
        "output_agent_messages": [],
        "output_content": [],
        "Output": "",
        "llm_provider": None  # Use all providers with rotation
    }
    
    try:
        app = create_agent()
        response = app.invoke(state)
        
        for key, value in response.items():
            print(">>>>", key)
            print(value)
            print("#" * 100)
        
        logger.agent_complete("Main", f"Agent run finished", (_time.time() - _run_start) * 1000)
        logger.separator("AGENT RUN COMPLETED")
        return {"output": response["Output"]}
    except Exception as e:
        logger.error(f"Fatal error: {e}", agent="Main", exc_info=True)
        print(f"An error occurred during execution: {e}")
        return {"error": f"Error during agent running: {e}"}
    finally:
        logger.info("Cleanup: Closing browser...", agent="Main")
        print(">>> CLEANUP: Closing Browser...")
        if browser_manager.is_browser_open():
            browser_manager.close_browser()


if __name__ == "__main__":
    # Test command
    test_input = "Open google.com and search for 'Python automation'"
    output = run_agent(test_input)
    print(output)
 