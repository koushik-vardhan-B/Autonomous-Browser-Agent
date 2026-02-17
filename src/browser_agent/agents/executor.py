"""
Execution agent for performing browser automation tasks.
"""

import os
import json
from langchain_core.messages import HumanMessage, AIMessage, ChatMessage
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.types import Command

from ..llm import LLMConfig
from ..prompts import get_autonomous_browser_prompt4
from ..browser.tools import (
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
from ..browser.analysis import (
    open_browser,
    scrape_data_using_text,
    analyze_using_vision,
    extract_and_analyze_selectors
)


def execution_agent(state):
    """
    Execution agent that performs browser automation tasks.
    
    Uses LLM rotation with rate limit handling to execute browser actions
    using visual IDs (Set-of-Marks) and extraction tools.
    """
    task_msg = state["execution_messages"][-1]
    task = task_msg.content if hasattr(task_msg, 'content') else str(task_msg)
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
                print(f">>> [WARN] Rate limit or size limit on {model_name}, rotating to next key...")
                continue  
            elif "failed to call a function" in error_str or "tool_call" in error_str or "model_not_found" in error_str or "does not exist" in error_str:
                # Tool calling format issue or model unavailable - try next model
                print(f">>> [WARN] Tool/model error on {model_name}, rotating to next model...")
                continue
            else:
                error_msg = f"AGENT CRASHED: {str(e)}"
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
        goto="END"
    )
