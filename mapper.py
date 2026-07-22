import os
import time
import importlib.util
import logging
from typing import Dict, Any, List, Tuple
from json_loader import FilterLoader
from prompt_builder import PromptBuilder
from llm import LLMClient
from validator import FilterValidator

# Load local parser.py dynamically to prevent collision with built-in python 'parser'
_dir = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("local_parser", os.path.join(_dir, "parser.py"))
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
JSONParser = _module.JSONParser

logger = logging.getLogger("FilterMappingSystem.mapper")

class FilterMapper:
    def __init__(self, filter_filepath: str = "data/filters.json", prompt_template_path: str = "prompts/system_prompt.txt"):
        logger.info("Initializing FilterMapper engine...")
        # 1. Load filters JSON
        self.loader = FilterLoader(filter_filepath)
        self.raw_filters = self.loader.get_raw_data()
        
        # 2. Initialize prompt builder
        self.prompt_builder = PromptBuilder(prompt_template_path)
        
        # 3. Initialize LLM client
        self.llm_client = LLMClient()
        
        # 4. Initialize validator with dynamic filter structure
        self.validator = FilterValidator(self.raw_filters)

    def map_prompt(self, user_query: str) -> Tuple[Dict[str, Any], List[str]]:
        """
        Orchestrates the prompt mapping flow:
        Builds prompt -> Calls Groq -> Parses JSON -> Validates hierarchy -> Analyzes missing info.
        Measures and logs performance metrics for each stage.
        Returns:
            Tuple of (validated_json_dict, list_of_missing_information_categories)
        """
        if not user_query or not user_query.strip():
            logger.error("User query is empty.")
            raise ValueError("The input prompt cannot be empty.")

        # 1. Build system prompt
        t_prompt_start = time.perf_counter()
        system_prompt = self.prompt_builder.build(self.raw_filters, user_query)
        t_prompt = time.perf_counter() - t_prompt_start
        logger.info(f"Performance Metrics: Prompt Building took {t_prompt:.4f}s")

        # 2. Send prompt to LLM and get parsed response (supports auto-retry on parse error)
        t_llm_start = time.perf_counter()
        parsed_output = self.llm_client.generate(system_prompt, JSONParser.parse)
        t_llm = time.perf_counter() - t_llm_start
        logger.info(f"Performance Metrics: LLM Call & Parse wrapper took {t_llm:.4f}s")

        # 3. Validate against hierarchy dynamically
        t_val_start = time.perf_counter()
        validated_output = self.validator.validate(parsed_output)
        t_val = time.perf_counter() - t_val_start
        logger.info(f"Performance Metrics: Validation took {t_val:.4f}s")

        # 4. Identify missing information dynamically
        missing_info = self._get_missing_information(validated_output)

        return validated_output, missing_info

    def _get_missing_information(self, validated_output: Dict[str, Any]) -> List[str]:
        """Analyzes the validated output keys to identify key business categories that are missing."""
        missing = []
        
        # We check normalized keys in the validated output
        keys_present = {k.lower() for k in validated_output.keys()}
        
        # Check Service Head / Primary / Sub filters
        has_service = any("service" in k or "primary" in k or "sub" in k for k in keys_present)
        if not has_service:
            missing.append("Service / Filter Category")
            
        # Check Industry
        has_industry = any("industry" in k for k in keys_present)
        if not has_industry:
            missing.append("Industry")
            
        # Check Location
        has_location = any("region" in k or "location" in k or "mumbai" in k for k in keys_present)
        if not has_location:
            missing.append("Location")
            
        # Check Business Size
        has_size = any("size" in k for k in keys_present)
        if not has_size:
            missing.append("Business Size")
            
        return missing
