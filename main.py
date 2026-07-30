import json
import os
from agents.scenario_agent import generate_test_scenarios
from agents.playwright_agent import generate_playwright_script

def main():
    # Example User Story / BRD extract
    sample_requirement = """
    User Story: Claims Portal Approval Workflow
    
    As a Claims Adjuster, 
    I want to review and approve submitted claims on the Claims Portal, 
    so that payouts can be processed.
    
    Acceptance Criteria:
    - The Claims Adjuster must be logged in to view the dashboard.
    - Only users with the 'Claims Adjuster' role can approve a claim. Users with 'Read-Only' role cannot.
    - When a claim is approved (POST /claims/{id}/approve), the claim status must change to APPROVED.
    - A payout record must be created in the database upon successful approval.
    - If the claim ID is invalid, the API should return a 404 Not Found.
    - The UI must be accessible via keyboard navigation.
    """
    
    print("Generating Test Scenarios...\n")
    
    try:
        # Note: If running locally without a Groq key, you can switch the model
        # to a local one supported by pydantic-ai, e.g., 'ollama:qwen2.5' or similar.
        # We use a mocked print out here if API keys aren't set, or we try to run it.
        # Ensure you have your environment variables set for the chosen LLM provider.
        # For Groq: export GROQ_API_KEY='your-key'
        
        # Uncomment below to actually run if you have an API key configured.
        result = generate_test_scenarios(sample_requirement)
        
        # Save to JSON for RAG pipeline ingestion
        output_file = "generated_scenarios.json"
        with open(output_file, "w") as f:
            f.write(result.to_rag_json())
        
        print(f"Scenarios successfully generated and saved to {output_file} in JSON format.")
        
        print("\nGenerating Playwright Scripts for each scenario...")
        output_dir = "execution/generated_tests"
        os.makedirs(output_dir, exist_ok=True)
        
        for idx, scenario in enumerate(result.scenarios):
            print(f"Generating script for: {scenario.title}")
            script_result = generate_playwright_script(scenario)
            
            script_path = os.path.join(output_dir, script_result.file_name)
            with open(script_path, "w") as sf:
                sf.write(script_result.code)
                
            print(f" -> Saved to {script_path}")
        
        print("Scenarios would be generated based on the sample requirement.")
        print("Playwright scripts would then be generated for each scenario and saved to the 'execution' folder.")
        print("To run, uncomment the execution lines in main.py and ensure LLM API keys are set.")

    except Exception as e:
        print(f"Error during scenario generation: {e}")

if __name__ == "__main__":
    main()
