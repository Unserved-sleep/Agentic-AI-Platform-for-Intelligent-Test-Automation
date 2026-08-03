import os
from typing import Optional, List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

# Setup paths to ensure we can import from agents and models
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.test_scenario import TestScenario
from models.playwright_script import PlaywrightScript
from agents.scenario_agent import generate_test_scenarios
from agents.playwright_agent import generate_playwright_script
from agents.failure_analysis_agent import analyze_failure, FailureDiagnosis
from shared.deps import AgentDeps
from rag.retriever import rag_retriever

# Import Engineer 3 Execution Framework
from execution.services.execution_service import ExecutionService
from execution.adapters.script_adapter import create_test_callable
from execution.adapters.execution_request_builder import build_execution_request
from execution.adapters.result_adapter import ResultAdapter

# Initialize common dependencies for all agents in the loop
global_deps = AgentDeps(rag_retriever=rag_retriever)

# Initialize ExecutionService (Engineer 3)
execution_service = ExecutionService()


class GraphState(TypedDict):
    requirement: str
    scenarios: List[TestScenario]
    current_scenario_idx: int
    scenario: Optional[TestScenario]
    script: Optional[PlaywrightScript]
    execution_stdout: str
    execution_stderr: str
    execution_exit_code: int
    passed: bool
    feedback: str
    retries: int
    is_script_repairable: bool
    # NEW: Store execution result for artifact access
    execution_result: Optional[dict]

MAX_RETRIES = 2

def planner_node(state: GraphState):
    print("\n--- [NODE: PLANNER] ---")
    requirement = state.get("requirement", "")
    scenarios = state.get("scenarios", [])
    current_idx = state.get("current_scenario_idx", 0)
    
    if not scenarios:
        print("Generating test scenarios from requirement...")
        scenarios_result = generate_test_scenarios(requirement, deps=global_deps)
        scenarios = scenarios_result.scenarios
        print(f"Generated {len(scenarios)} scenarios.")
    
    if current_idx < len(scenarios):
        scenario = scenarios[current_idx]
        print(f"Selected scenario: {scenario.title}")
        return {
            "scenarios": scenarios,
            "scenario": scenario,
            "current_scenario_idx": current_idx,
            "retries": 0,
            "feedback": "",
            "script": None,
            "is_script_repairable": True
        }
    else:
        print("No more scenarios to process.")
        return {"scenario": None}

def generate_node(state: GraphState):
    print("\n--- [NODE: GENERATE] ---")
    scenario = state.get("scenario")
    feedback = state.get("feedback")
    
    if not scenario:
        return {}

    # If there is feedback from a previous failure, we append it to the description
    # This acts as instructions to the code generator to fix the issue
    if feedback:
        print("Applying repair feedback to scenario description...")
        scenario_copy = scenario.model_copy()
        scenario_copy.description += f"\n\n[REPAIR INSTRUCTIONS]: {feedback}"
        scenario_to_gen = scenario_copy
    else:
        scenario_to_gen = scenario

    print("Generating Playwright script...")
    script_result = generate_playwright_script(scenario_to_gen, deps=global_deps)
    return {"script": script_result}

def execute_node(state: GraphState):
    """
    Execute the generated Playwright script using Engineer 3's ExecutionService.
    
    This node:
    1. Converts PlaywrightScript to a callable via ScriptAdapter
    2. Builds ExecutionRequest via ExecutionRequestBuilder
    3. Executes via ExecutionService
    4. Returns ExecutionResult adapted for Failure Analysis
    """
    print("\n--- [NODE: EXECUTE] ---")
    script = state.get("script")
    scenario = state.get("scenario")
    
    if not script:
        return {"passed": True}  # Skip if no script
    
    try:
        # Step 1: Convert script to callable
        print(f"Converting script to callable: {script.file_name}")
        test_function = create_test_callable(
            script=script,
            script_dir="execution/generated_tests"
        )
        
        # Step 2: Build ExecutionRequest
        print("Building ExecutionRequest...")
        request = build_execution_request(
            script=script,
            scenario=scenario,
            headless=True,  # Run headless for CI/automation
        )
        print(f"Run ID: {request.run_id}")
        print(f"Execution Type: {request.execution_type.value}")
        
        # Step 3: Execute via ExecutionService
        print("Executing via ExecutionService...")
        result = execution_service.execute(
            request=request,
            test_function=test_function,
        )
        
        # Step 4: Adapt result for Failure Analysis
        stdout, stderr = ResultAdapter.to_stdout_stderr(result)
        passed = ResultAdapter.is_passed(result)
        
        print(f"Execution finished. Status: {result.status.value}")
        
        # Log artifact information
        if result.artifacts:
            if result.artifacts.screenshots:
                print(f"  Screenshots captured: {len(result.artifacts.screenshots)}")
            if result.artifacts.traces:
                print(f"  Traces captured: {len(result.artifacts.traces)}")
            if result.artifacts.videos:
                print(f"  Videos captured: {len(result.artifacts.videos)}")
            if result.artifacts.logs:
                print(f"  Logs captured: {len(result.artifacts.logs)}")
        
        return {
            "execution_stdout": stdout,
            "execution_stderr": stderr,
            "execution_exit_code": 0 if passed else 1,
            "passed": passed,
            "execution_result": {
                "run_id": result.run_id,
                "status": result.status.value,
                "error_message": result.error_message,
                "stack_trace": result.stack_trace,
                "screenshot_paths": ResultAdapter.get_screenshot_paths(result),
                "trace_paths": ResultAdapter.get_trace_paths(result),
            }
        }
        
    except Exception as e:
        # Handle execution errors
        import traceback
        error_msg = str(e)
        stack_trace_str = traceback.format_exc()
        
        print(f"Execution failed with error: {error_msg}")
        
        return {
            "execution_stdout": "",
            "execution_stderr": f"{error_msg}\n\n{stack_trace_str}",
            "execution_exit_code": 1,
            "passed": False,
            "execution_result": None
        }

def observe_node(state: GraphState):
    print("\n--- [NODE: OBSERVE] ---")
    # This node could extract specific insights, but for now we just log
    if state.get("passed"):
        print("Observation: Test passed successfully.")
    else:
        print(f"Observation: Test failed with exit code {state.get('execution_exit_code')}.")
    return {}

def reflect_node(state: GraphState):
    print("\n--- [NODE: REFLECT] ---")
    stdout = state.get("execution_stdout", "")
    stderr = state.get("execution_stderr", "")
    script = state.get("script")
    
    print("Analyzing logs to determine root cause...")
    diagnosis = analyze_failure(script.code, stdout, stderr)
    
    print(f"Failure Category: {diagnosis.category.value}")
    print(f"Root Cause: {diagnosis.root_cause_explanation}")
    print(f"Repairable: {diagnosis.is_script_repairable}")
    
    retries = state.get("retries", 0) + 1
    
    if diagnosis.is_script_repairable and diagnosis.repair_instructions:
        feedback = f"[{diagnosis.category.value}] {diagnosis.root_cause_explanation}\nFix Instructions: {diagnosis.repair_instructions}"
    else:
        feedback = ""
        
    print(f"Reflection complete. Retries: {retries}/{MAX_RETRIES}")
    return {
        "feedback": feedback, 
        "retries": retries,
        "is_script_repairable": diagnosis.is_script_repairable
    }

def should_repair(state: GraphState):
    passed = state.get("passed")
    retries = state.get("retries", 0)
    scenario = state.get("scenario")
    is_repairable = state.get("is_script_repairable", True)
    
    if not scenario:
        return "end_process"
        
    if passed:
        return "next_scenario"
    elif not is_repairable:
        print("Failure is not repairable (e.g. App Bug). Moving to next scenario.")
        return "next_scenario"
    elif retries >= MAX_RETRIES:
        print(f"Max retries ({MAX_RETRIES}) reached. Moving to next scenario.")
        return "next_scenario"
    else:
        print("Routing to REPAIR (generate).")
        return "repair"
        
def next_scenario_node(state: GraphState):
    print("\n--- [NODE: NEXT_SCENARIO] ---")
    current_idx = state.get("current_scenario_idx", 0)
    return {"current_scenario_idx": current_idx + 1}

def router_after_observe(state: GraphState):
    scenario = state.get("scenario")
    if not scenario:
        return "end_process"
        
    if state.get("passed"):
        return "next_scenario"
    else:
        return "reflect"

def router_after_planner(state: GraphState):
    if state.get("scenario") is None:
        return "end_process"
    return "generate"


# Build the graph
workflow = StateGraph(GraphState)

workflow.add_node("planner", planner_node)
workflow.add_node("generate", generate_node)
workflow.add_node("execute", execute_node)
workflow.add_node("observe", observe_node)
workflow.add_node("reflect", reflect_node)
workflow.add_node("next_scenario", next_scenario_node)

workflow.add_edge(START, "planner")

workflow.add_conditional_edges("planner", router_after_planner, {
    "generate": "generate",
    "end_process": END
})

workflow.add_edge("generate", "execute")
workflow.add_edge("execute", "observe")

workflow.add_conditional_edges("observe", router_after_observe, {
    "next_scenario": "next_scenario",
    "reflect": "reflect",
    "end_process": END
})

workflow.add_conditional_edges("reflect", should_repair, {
    "repair": "generate",
    "next_scenario": "next_scenario",
    "end_process": END
})

workflow.add_edge("next_scenario", "planner")

loop_graph = workflow.compile()
