from dotenv import load_dotenv
from langchain_core.globals import set_verbose, set_debug
from langchain_groq.chat_models import ChatGroq
from langgraph.constants import END
from langchain_openai import ChatOpenAI
import json
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent

from app_builder.prompts import *
from app_builder.states import *
# Add to imports
from app_builder.tools import (
    write_file, read_file, get_current_directory, list_files,
    check_code_quality, validate_syntax, analyze_file_issues,
    start_preview_server, detect_project_type
)
_ = load_dotenv()

set_debug(True)
set_verbose(True)

llm = ChatGroq(model="openai/gpt-oss-120b")
model = ChatOpenAI(model="gpt-4o-mini")


def planner_agent(state: AppState) -> dict:
    """Converts user prompt into a structured Plan."""
    user_prompt = state.user_prompt
    resp = llm.with_structured_output(Plan).invoke(
        planner_prompt(user_prompt)
    )
    if resp is None:
        raise ValueError("Planner did not return a valid response.")

    # Convert Plan object to dict for AppState
    return {"plan": resp.model_dump()}  # <-- model_dump() returns dict


def architect_agent(state: AppState) -> dict:
    plan_dict = state.plan  # this is now a dict
    resp = llm.with_structured_output(TaskPlan).invoke(
        architect_prompt(plan=json.dumps(plan_dict))  # pass JSON string if needed
    )
    if resp is None:
        raise ValueError("Architect did not return a valid response.")

    # Convert TaskPlan object to dict for AppState
    return {"task_plan": resp.model_dump()}


def coder_agent(state: AppState) -> dict:
    """LangGraph tool-using coder agent."""

    # Convert dict to Pydantic object if needed
    coder_state = state.coder_state
    if isinstance(coder_state, dict):
        coder_state = CoderState.model_validate(coder_state)  # Pydantic v2

    if coder_state is None:
        coder_state = CoderState(task_plan=state.task_plan, current_step_idx=0)

    steps = coder_state.task_plan.implementation_steps
    if coder_state.current_step_idx >= len(steps):
        return {"coder_state": coder_state.model_dump(), "coder_status": "DONE"}

    current_task = steps[coder_state.current_step_idx]
    existing_content = read_file.invoke({"path": current_task.filepath})

    system_prompt = coder_system_prompt()
    user_prompt = (
        f"Task: {current_task.task_description}\n"
        f"File: {current_task.filepath}\n"
        f"Existing content:\n{existing_content}\n"
        "Use write_file(path, content) to save your changes."
    )

    coder_tools = [read_file, write_file, list_files, get_current_directory]
    react_agent = create_react_agent(model, tools=coder_tools)

    react_agent.invoke({"messages": [{"role": "system", "content": system_prompt},
                                     {"role": "user", "content": user_prompt}]})

    coder_state.current_step_idx += 1
    return {"coder_state": coder_state.model_dump()}

def reviewer_agent(state: AppState) -> dict:
    """Reviews each file one by one, fixes errors, and improves code quality."""
    print("\n=== CODE REVIEW & FIX PHASE ===")

    coder_state = state.coder_state

    # Convert dict back to Pydantic model if needed
    if isinstance(coder_state, dict):
        coder_state = CoderState.model_validate(coder_state)  # Pydantic v2

    if not coder_state:
        return {"review_status": "REVIEWED"}

    # Get all files that were created
    steps = coder_state.task_plan.implementation_steps
    files_to_review = [task.filepath for task in steps if task.filepath]

    print(f"Reviewing {len(files_to_review)} files...")

    reviewer_state = state.reviewer_state or {"current_file_idx": 0, "files_fixed": []}
    current_idx = reviewer_state.get("current_file_idx", 0)

    # If all files reviewed → end
    if current_idx >= len(files_to_review):
        print("\n✓ All files reviewed.")
        return {"reviewer_state": reviewer_state, "review_status": "REVIEWED"}

    # Review current file
    file_path = files_to_review[current_idx]
    print(f"\n[{current_idx + 1}/{len(files_to_review)}] Reviewing: {file_path}")

    file_content = read_file.invoke({"path": file_path})

    if file_content:
        syntax_check = validate_syntax.invoke({"file_path": file_path})
        quality_check = check_code_quality.invoke({"file_path": file_path})
        analysis = analyze_file_issues.invoke({"file_path": file_path})

        needs_fix = (
            "✗" in syntax_check or
            "Issues found" in quality_check or
            "Issues:" in analysis or
            "SECURITY" in analysis
        )

        if needs_fix:
            print(f"⚠️  Issues found in {file_path}. Fixing...")

            fix_prompt = f"""
Review and fix this file: {file_path}

Current file content:
{file_content}

Issues found:
- Syntax: {syntax_check}
- Quality: {quality_check}
- Analysis: {analysis}

Please:
1. Fix all syntax errors
2. Fix all bugs and logical errors
3. Improve code quality
4. Add proper error handling
5. Ensure the code is production-ready
6. Make any UI improvements if frontend

Write the full corrected file using write_file(path, content).
"""

            reviewer_tools = [
                read_file, write_file, list_files, get_current_directory,
                check_code_quality, validate_syntax, analyze_file_issues
            ]

            fix_agent = create_react_agent(model, tools=reviewer_tools)

            try:
                fix_agent.invoke({
                    "messages": [
                        {"role": "system", "content": reviewer_system_prompt()},
                        {"role": "user", "content": fix_prompt}
                    ]
                })
                reviewer_state["files_fixed"].append(file_path)
                print(f"✓ Fixed {file_path}")
            except Exception as e:
                print(f"Error fixing {file_path}: {e}")
        else:
            print(f"✓ {file_path} looks good!")

    # Move to next file
    # Move to next file
    reviewer_state["current_file_idx"] = current_idx + 1

    # Decide status
    status = "REVIEWED" if reviewer_state["current_file_idx"] >= len(files_to_review) else "IN_PROGRESS"

    return {"reviewer_state": reviewer_state, "review_status": status}


def preview_agent(state: AppState) -> dict:
    """Starts a live preview server for the generated project."""
    print("\n=== STARTING LIVE PREVIEW ===")
    
    # Detect project type
    try:
        project_type = detect_project_type.invoke({})
        print(f"Detected project type: {project_type}")
        
        # Start preview server
        preview_url = start_preview_server.invoke({"project_type": project_type})
        print(preview_url)
        print("\n✓ Live preview is running!")
        print("The browser should open automatically.")
        print("Note: The server runs in the background. Close the terminal to stop it.\n")
    except Exception as e:
        print(f"Error starting preview server: {e}")
        print("You can manually start a server:")
        print("  For HTML: python -m http.server 8000")
        print("  For Python Flask: cd generated_project && python app.py")
        print("  For Node: cd generated_project && npm start")
    
    return {"preview_status": "STARTED"}


# Update the graph
graph = StateGraph(AppState)

graph.add_node("planner", planner_agent)
graph.add_node("architect", architect_agent)
graph.add_node("coder", coder_agent)
graph.add_node("reviewer", reviewer_agent)
graph.add_node("preview", preview_agent)

graph.add_edge("planner", "architect")
graph.add_edge("architect", "coder")
graph.add_conditional_edges(
    "coder",
    lambda s: "reviewer" if s.coder_status == "DONE" else "coder",
    {"reviewer": "reviewer", "coder": "coder"}
)
graph.add_conditional_edges(
    "reviewer",
    lambda s: "preview" if s.review_status == "REVIEWED" else "reviewer",
    {"preview": "preview", "reviewer": "reviewer"}
)
graph.add_edge("preview", END)
graph.set_entry_point("planner")
agent = graph.compile()
if __name__ == "__main__":
    result = agent.invoke({"user_prompt": "Build a simple  modern calculator app in html css and js"},
                          config={"recursion_limit": 50})
    print("Final State:", result)