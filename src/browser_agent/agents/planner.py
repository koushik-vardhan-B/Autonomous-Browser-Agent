"""
Planning agent for the browser automation system.
"""

from urllib.parse import urlparse
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.schema import Document
import json

from ..llm import LLMConfig
from ..prompts import get_central_agent_prompt5
from ..core import SupervisorOutput, extract_json_from_markdown
from ..browser.manager import browser_manager
from ..browser.analysis import close_browser


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
    Planning agent that generates step-by-step execution plans.
    
    Supports three modes:
    1. Fresh Start - Initial planning
    2. Phase 2 Re-planning - After data extraction
    3. Error Recovery - Replanning after failures
    """
    user_input = state["user_input"]
    user_input = user_input.replace("{", "{{").replace("}", "}}")
    
    site_names = state.get("site_names", [])
    urls = state.get("urls", [])
    current_plan = state.get("plan", [])
    current_index = state.get("step_index", 0)
    last_error = state.get("last_error", None)
    
    print(f">>> PLANNING AGENT: Step Index: {current_index}")
    
    # Import here to avoid circular dependency
    from .rag import retrieve_errors, get_vector_db
    
    if not site_names:
        historical_errors = "No previous errors"
    else:
        vector_db = get_vector_db()
        historical_errors = retrieve_errors(state) if vector_db else "No previous errors"
    historical_errors = historical_errors.replace("{", "{{").replace("}", "}}")

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
    
    start_index = state.get("current_model_index", 0)
    provider = state.get("llm_provider", None) 
    llm_rotation = LLMConfig.get_main_llm_with_rotation(start_index, provider=provider)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "Please generate the plan."),
        MessagesPlaceholder(variable_name="chat_history"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])

    tavily = TavilySearchResults(tavily_api_key="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")
    tools = [tavily, close_browser]

    sanitized_history = []
    for msg in state["messages"]:
        sanitized_content = msg.content.replace("{", "{{").replace("}", "}}")
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
            
            successful_index = (start_index + idx) % len(llm_rotation)
            print(f">>> [OK] Success with {model_name}")
            
            clean_json = extract_json_from_markdown(response["output"])
            result = json.loads(clean_json)
            
            detected_urls = result.get("target_urls", [])
            detected_sites = result.get("site_names", [])
            new_steps = result.get("steps", result) if isinstance(result, dict) else result
            
            if not isinstance(new_steps, list):
                new_steps = []

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

            final_plan = completed_steps + new_steps
            
            for i, step in enumerate(final_plan):
                step['step_number'] = i + 1

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
            
            if "429" in error_str or "rate limit" in error_str or "quota" in error_str or "resource_exhausted" in error_str:
                print(f">>> [WARN] Rate limit hit on {model_name}, rotating to next key...")
                continue  
            else:
                print(f">>> [FAIL] Planning Error (non-rate-limit): {e}")
                break

    print(f">>> All API keys exhausted or planning failed. Last error: {last_error}")
    final_plan = current_plan  

    return {
        "plan": final_plan,
        "step_index": len(completed_steps),
        "last_error": None, 
        "urls": detected_urls,
        "site_names": detected_sites,
        "messages": [HumanMessage(content=f"[Planner]: Plan updated. Phase steps: {len(new_steps)}.")]
    }
