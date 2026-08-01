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
        
        print(f"\n=== Pipeline Complete ===")
        print(f"Scenarios generated: {len(result.scenarios)}")
        print(f"Scripts saved to: {output_dir}/")

    except Exception as e:
        import traceback
        print(f"Error during scenario generation: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
