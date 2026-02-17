"""
Output formatting agent for structuring extracted data.
"""

from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Command

from ..llm import LLMConfig


def output_formatting_agent(state):
    """
    Output formatting agent that structures extracted data according to user requirements.
    
    Uses LLM rotation with rate limit handling to format raw scraped data
    into clean, structured output.
    """
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
