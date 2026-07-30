import json
from agents.scenario_agent import generate_test_scenarios

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
        # Note: If running locally without an OpenAI key, you can switch the model
        # to a local one supported by pydantic-ai, e.g., 'ollama:qwen2.5' or similar.
        # We use a mocked print out here if API keys aren't set, or we try to run it.
        # Ensure you have your environment variables set for the chosen LLM provider.
        # For OpenAI: export OPENAI_API_KEY='your-key'
        
        # Uncomment below to actually run if you have an API key configured.
        # result = generate_test_scenarios(sample_requirement)
        # 
        # # Save to JSON for RAG pipeline ingestion
        # output_file = "generated_scenarios.json"
        # with open(output_file, "w") as f:
        #     f.write(result.to_rag_json())
        # 
        # print(f"Scenarios successfully generated and saved to {output_file} in JSON format.")
        
        print("Scenarios would be generated based on the sample requirement.")
        print("To run, uncomment the execution lines in main.py and ensure LLM API keys are set.")
        print("The script is now configured to save the output as a JSON file suitable for the RAG pipeline.")

    except Exception as e:
        print(f"Error during scenario generation: {e}")

if __name__ == "__main__":
    main()
