"""
Redirector agent for routing workflow between different agents.
"""

from langchain_core.messages import HumanMessage, ChatMessage
from langgraph.types import Command
from langgraph.graph import END


def redirector(state):
    """
    Redirector agent that routes the workflow to the appropriate next agent.
    
    Routes based on the current step's agent type:
    - PLANNER: Re-planning for multi-phase workflows
    - RAG: Store error/solution in vector database
    - EXECUTION: Execute browser automation task
    - OUTPUT_FORMATTING: Format extracted data
    - end: Complete the workflow
    """
    print(">>>> Redirector WORKING")
    plan = state["plan"]
    index = state["step_index"]
    steps = plan
    
    if index >= len(plan):
        print("Plan execution completed.")
        return Command(goto=END)

    step = plan[index]
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
