import sys
import json
import logging
from dotenv import load_dotenv
from mapper import FilterMapper

# Set up logging to console for testing purposes
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

def run_tests():
    load_dotenv(override=True)
    
    test_cases = [
        "Healthcare startup in Mumbai looking for branding.",
        "Manufacturer looking for SEO.",
        "Retail business needing social media marketing.",
        "Need marketing."
    ]
    
    print("="*60)
    print("           RUNNING AUTOMATED TEST CASES")
    print("="*60)
    
    try:
        mapper = FilterMapper()
    except Exception as e:
        print(f"Failed to initialize FilterMapper: {e}")
        sys.exit(1)
        
    for i, case in enumerate(test_cases, 1):
        print(f"\n[Test Case {i}] Prompt: '{case}'")
        try:
            validated_output, missing_info = mapper.map_prompt(case)
            print("Result JSON:")
            print(json.dumps(validated_output, indent=2))
            
            if missing_info:
                print("Missing Information:")
                for item in missing_info:
                    print(f"- {item}")
        except Exception as e:
            print(f"Error executing test case: {e}")
        print("-"*60)

if __name__ == "__main__":
    run_tests()
