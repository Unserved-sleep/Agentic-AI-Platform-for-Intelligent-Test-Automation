import json
import os
from dotenv import load_dotenv

load_dotenv()
from agents.scenario_agent import generate_test_scenarios
from agents.playwright_agent import generate_playwright_script

def main():
    # Example User Story / API documentation
    sample_requirement = """
    User Story: Document Upload API
    
    As a system user, 
    I want to upload a document via the /api/documents POST endpoint, 
    so that it is securely stored in the system.
    
    Acceptance Criteria:
    - The API must accept multipart/form-data.
    - If the request is successful, it should return a 201 Created status code.
    - Upon successful upload, a Document record must be persisted in the PostgreSQL database with the correct filename.
    - If no file is provided, the API should return a 400 Bad Request.
    """
    
    print("Starting LangGraph Auto-QA Loop...\n")
    
    try:
        from orchestration.loop import loop_graph
        
        initial_state = {
            "requirement": sample_requirement,
            "scenarios": [],
            "current_scenario_idx": 0,
            "scenario": None,
            "script": None,
            "execution_stdout": "",
            "execution_stderr": "",
            "execution_exit_code": -1,
            "passed": False,
            "feedback": "",
            "retries": 0,
            "is_script_repairable": True,
            "execution_result": None,  # NEW: Store execution result for artifact access
            "max_scenarios": None,     # None = run all scenarios
        }
        
        print("Invoking graph...")
        # Stream the graph execution to see progress
        for event in loop_graph.stream(initial_state):
            for k, v in event.items():
                pass # The nodes themselves print progress
                
        print(f"\n=== LangGraph Auto-QA Pipeline Complete ===")
        
    except Exception as e:
        import traceback
        print(f"Error during scenario generation: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
