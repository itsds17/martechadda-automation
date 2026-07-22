import os
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger("FilterMappingSystem.loader")

class FilterLoader:
    def __init__(self, filepath: str = "data/filters.json"):
        self.filepath = filepath
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Loads and validates the filters JSON file."""
        if not os.path.exists(self.filepath):
            logger.error(f"Filter file not found at: {self.filepath}")
            raise FileNotFoundError(f"Filter file not found at: {self.filepath}")
        
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            logger.info(f"Successfully loaded filters from {self.filepath}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format in {self.filepath}: {e}")
            raise ValueError(f"Invalid JSON format in filter file: {e}")
        except Exception as e:
            logger.error(f"Failed to read filters file: {e}")
            raise

        # Basic structure validation
        required_keys = [
            "serviceHeadToPrimaryFilters",
            "primaryToSubFilters",
            "contextAndIntentRefinement",
            "locationsAndDemographics",
            "expertDetails"
        ]
        missing_keys = [key for key in required_keys if key not in self.data]
        if missing_keys:
            logger.warning(f"Filter JSON is missing some typical keys: {missing_keys}")

    def get_raw_data(self) -> Dict[str, Any]:
        """Returns the raw loaded filters dictionary."""
        return self.data
