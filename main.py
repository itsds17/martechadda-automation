import os
import sys
import json
import logging
from dotenv import load_dotenv
from mapper import FilterMapper

# Set up logging to a local file to keep stdout/stderr clean and easy to read
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename="mapping_system.log",
    filemode="a",
    encoding="utf-8"
)
logger = logging.getLogger("FilterMappingSystem.cli")

def main():
    # Load .env variables with override=True to ensure local .env settings take precedence
    load_dotenv(override=True)
    
    print("\n" + "="*50)
    print("        AI FILTER MAPPING SYSTEM CLI")
    print("="*50)

    # 1. Check if filters.json is present
    filter_filepath = "data/filters.json"
    if not os.path.exists(filter_filepath):
        print(f"[Error] Filters configuration not found at {filter_filepath}.")
        print("Please place the filter JSON file there and try again.")
        logger.error(f"Filter file {filter_filepath} not found.")
        sys.exit(1)

    # 2. Collect user prompt
    try:
        user_query = input("\nEnter business requirement: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting. Goodbye!")
        sys.exit(0)

    if not user_query:
        print("[Error] Input prompt cannot be empty.")
        logger.warning("Empty user prompt entered.")
        sys.exit(1)

    # 3. Initialize mapping engine and execute
    print("\nMapping query to filters, please wait...")
    logger.info(f"Received query: '{user_query}'")
    
    try:
        mapper = FilterMapper(filter_filepath=filter_filepath)
        validated_output, missing_info = mapper.map_prompt(user_query)
        
        print("\n" + "-"*15 + " Mapping Results " + "-"*15)
        # Pretty-print the matched filter JSON
        print(json.dumps(validated_output, indent=2))
        
        # Display missing information if any categories were not matched
        if missing_info:
            print("\nMissing Information:")
            for item in missing_info:
                print(f"- {item}")
        print("-"*47)
        logger.info("Successfully finished mapping.")
        
    except ValueError as ve:
        # Configuration or parsing issues
        print(f"\n[Error] Mapping failed: {ve}")
        logger.error(f"Value error occurred: {ve}", exc_info=True)
        sys.exit(1)
        
    except RuntimeError as re:
        # API or network issues
        print(f"\n[Error] API failure: {re}")
        print("Please check your .env configuration, API key, and internet connection.")
        logger.error(f"Runtime error occurred: {re}", exc_info=True)
        sys.exit(1)
        
    except Exception as e:
        # Unexpected errors
        print(f"\n[Error] An unexpected error occurred: {e}")
        print("Details have been logged to mapping_system.log.")
        logger.error(f"Unexpected exception occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
