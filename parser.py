import json
import logging
from typing import Dict, Any

logger = logging.getLogger("FilterMappingSystem.parser")

class JSONParser:
    @staticmethod
    def parse(raw_response: str) -> Dict[str, Any]:
        """Cleans and extracts the JSON object from the LLM response string."""
        if not raw_response or not raw_response.strip():
            logger.error("Received empty response from the LLM.")
            raise ValueError("The LLM returned an empty response.")

        cleaned = raw_response.strip()

        # Step 1: Strip markdown code fences (```json or ```) if present
        if cleaned.startswith("```"):
            # Find the index of the first newline after the starting backticks
            newline_idx = cleaned.find("\n")
            if newline_idx != -1:
                cleaned = cleaned[newline_idx:].strip()
            else:
                cleaned = cleaned[3:].strip()
            
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()

        # Step 2: In case there is text before or after the JSON block (e.g. explanations),
        # extract the string between the first occurrence of '{' and the last occurrence of '}'
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")

        if first_brace == -1 or last_brace == -1 or last_brace < first_brace:
            logger.error("Could not find a valid JSON object block in LLM response.")
            raise ValueError("No JSON object could be found in the LLM response.")

        json_str = cleaned[first_brace:last_brace + 1]

        # Step 3: Parse the extracted JSON string
        try:
            parsed = json.loads(json_str)
            if not isinstance(parsed, dict):
                logger.error(f"Parsed JSON is not a dictionary/object: {type(parsed)}")
                raise ValueError("LLM response did not parse into a JSON object/dictionary.")
            logger.info("Successfully parsed and cleaned LLM response JSON.")
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding failed for string: {json_str}. Error: {e}")
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")
