import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger("FilterMappingSystem.prompt_builder")

class PromptBuilder:
    def __init__(self, template_path: str = "prompts/system_prompt.txt"):
        self.template_path = template_path

    def build(self, filter_data: Dict[str, Any], user_query: str) -> str:
        """Dynamically constructs the system prompt with the filter hierarchy and user query."""
        if not os.path.exists(self.template_path):
            logger.error(f"System prompt template not found at {self.template_path}")
            raise FileNotFoundError(f"System prompt template not found at {self.template_path}")
            
        try:
            with open(self.template_path, "r", encoding="utf-8") as f:
                template = f.read()
        except Exception as e:
            logger.error(f"Failed to read prompt template: {e}")
            raise

        # Check placeholders
        if "{FILTER_HIERARCHY}" not in template:
            logger.warning("Placeholder {FILTER_HIERARCHY} not found in system prompt template.")
        if "{USER_QUERY}" not in template:
            logger.warning("Placeholder {USER_QUERY} not found in system prompt template.")

        # Serialize the entire filter hierarchy JSON to inject into the prompt
        # Optimization: Minify JSON to reduce token usage and LLM response latency
        hierarchy_str = json.dumps(filter_data, separators=(',', ':'))
        
        # Replace placeholders
        prompt = template.replace("{FILTER_HIERARCHY}", hierarchy_str)
        prompt = prompt.replace("{USER_QUERY}", user_query)
        
        logger.info("Successfully constructed system prompt with filter hierarchy and user query.")
        return prompt
