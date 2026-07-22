import logging
import re
from typing import Dict, Any, List, Set, Tuple

logger = logging.getLogger("FilterMappingSystem.validator")

def normalize_key(s: str) -> str:
    """Normalizes key names for simple comparison."""
    s = s.lower().replace("_", "").replace("-", "")
    if s.endswith("ies"):
        s = s[:-3] + "y"
    elif s.endswith("s") and not s.endswith("ss"):
        s = s[:-1]
    return s

class FilterValidator:
    def __init__(self, filter_data: Dict[str, Any]):
        self.filter_data = filter_data
        self.flat_categories: Dict[str, Set[str]] = {}
        self.parent_child_mappings: List[Tuple[str, str, Dict[str, List[str]]]] = []
        self._analyze_filters()

    def _get_all_strings(self, node: Any) -> Set[str]:
        """Recursively collects all leaf string values from a JSON node."""
        strings = set()
        if isinstance(node, str):
            strings.add(node)
        elif isinstance(node, list):
            for item in node:
                if isinstance(item, dict) and "label" in item:
                    strings.add(item["label"])
                else:
                    strings.update(self._get_all_strings(item))
        elif isinstance(node, dict):
            for val in node.values():
                strings.update(self._get_all_strings(val))
        return strings

    def _analyze_filters(self) -> None:
        """Dynamically analyzes the filter structure to find categories, value lists, and parent-child relations."""
        dict_mappings: Dict[str, Tuple[str, str, Dict[str, List[str]]]] = {}

        def traverse(node: Any, path: List[str]):
            if not path:
                if isinstance(node, dict):
                    for k, v in node.items():
                        traverse(v, path + [k])
                return

            depth = len(path)
            cat_name = path[-1]

            if depth == 1:
                # Top-level mappings (like serviceHeadToPrimaryFilters, primaryToSubFilters)
                if isinstance(node, dict):
                    parts = cat_name.split("To")
                    if len(parts) == 2:
                        parent_name = parts[0]
                        child_name = parts[1][0].lower() + parts[1][1:]
                        
                        # Register in flat categories
                        self.flat_categories[parent_name] = set(node.keys())
                        
                        child_vals = set()
                        for v in node.values():
                            if isinstance(v, list):
                                child_vals.update(self._get_all_strings(v))
                        self.flat_categories[child_name] = child_vals
                        
                        # Store mapping dict reference
                        dict_mappings[cat_name] = (parent_name, child_name, node)
                    
                    for k, v in node.items():
                        traverse(v, path + [k])
            elif depth == 2:
                # Second-level blocks (like industrySectors, businessRelationshipTypes, languages, etc.)
                if isinstance(node, dict):
                    # Flatten structural/organizing dictionary completely under this category name
                    self.flat_categories[cat_name] = self._get_all_strings(node)
                elif isinstance(node, list):
                    self.flat_categories[cat_name] = self._get_all_strings(node)
                return

        traverse(self.filter_data, [])

        # Build hierarchical relationships dynamically
        for name_a, (p_a, c_a, dict_a) in dict_mappings.items():
            # Check overlap between child of A and parent of B
            for name_b, (p_b, c_b, dict_b) in dict_mappings.items():
                if name_a == name_b:
                    continue
                
                norm_c_a = normalize_key(c_a)
                norm_p_b = normalize_key(p_b)
                
                # Check for overlap in names (e.g. primaryFilters and primary)
                if norm_c_a == norm_p_b or norm_p_b in norm_c_a or norm_c_a in norm_p_b:
                    logger.info(f"Dynamically detected hierarchy relationship: {p_a} -> {c_b} via intermediate {c_a}/{p_b}")
                    self.parent_child_mappings.append((p_a, c_a, dict_a))
                    self.parent_child_mappings.append((p_b, c_b, dict_b))

    def _find_best_category_match(self, llm_key: str) -> str:
        """Finds the best category name matching the LLM key using token overlap comparison."""
        def tokenize(s: str) -> Set[str]:
            s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
            words = re.findall(r'[a-zA-Z0-9]+', s.lower())
            tokens = set()
            for w in words:
                if w.endswith("ies"):
                    w = w[:-3] + "y"
                elif w.endswith("s") and not w.endswith("ss"):
                    w = w[:-1]
                tokens.add(w)
            return tokens

        tokens_llm = tokenize(llm_key)
        if not tokens_llm:
            return ""

        best_match = ""
        best_score = 0.0

        for cat in self.flat_categories.keys():
            tokens_cat = tokenize(cat)
            if not tokens_cat:
                continue
            
            # Perfect exact token match
            if tokens_llm == tokens_cat:
                return cat
                
            intersection = tokens_llm.intersection(tokens_cat)
            score = len(intersection) / max(len(tokens_llm), len(tokens_cat))
            if score > best_score:
                best_score = score
                best_match = cat

        if best_score > 0.3:
            return best_match
            
        return ""

    def validate(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validates that values belong to the correct categories and respect hierarchical rules."""
        validated: Dict[str, List[str]] = {}

        # Step 1: Validate individual values exist in the matched category
        for llm_key, values in list(output_data.items()):
            if not isinstance(values, list):
                logger.warning(f"Key '{llm_key}' in LLM output does not map to a list. Skipping.")
                continue

            matched_cat = self._find_best_category_match(llm_key)
            if not matched_cat:
                logger.warning(f"Could not dynamically match LLM key '{llm_key}' to any category in filters.json. Removing key.")
                continue

            allowed_set = self.flat_categories[matched_cat]
            valid_values = []
            for val in values:
                if not isinstance(val, str):
                    continue
                # Case-insensitive matching
                matched_val = next((item for item in allowed_set if item.lower() == val.lower()), None)
                if matched_val:
                    valid_values.append(matched_val)
                else:
                    logger.warning(f"Value '{val}' not present in category '{matched_cat}' of filters.json. Removing value.")

            if valid_values:
                validated[llm_key] = valid_values

        # Step 2: Enforce dynamic hierarchical relationships
        # We run the hierarchy checks: for each parent-child dict, if parent and child keys exist in 'validated',
        # we filter child values to only those mapped under selected parent values.
        for parent_cat_name, child_cat_name, mapping in self.parent_child_mappings:
            parent_llm_key = None
            child_llm_key = None
            
            for k in validated.keys():
                matched = self._find_best_category_match(k)
                if not matched:
                    continue
                
                # Loose matching to account for naming differences (e.g. primary vs primaryFilters)
                if (normalize_key(matched) == normalize_key(parent_cat_name) or 
                    normalize_key(matched) in normalize_key(parent_cat_name) or 
                    normalize_key(parent_cat_name) in normalize_key(matched)):
                    parent_llm_key = k
                
                if (normalize_key(matched) == normalize_key(child_cat_name) or 
                    normalize_key(matched) in normalize_key(child_cat_name) or 
                    normalize_key(child_cat_name) in normalize_key(matched)):
                    child_llm_key = k

            if parent_llm_key and child_llm_key:
                parent_vals = validated[parent_llm_key]
                child_vals = validated[child_llm_key]
                
                # Get all allowed child values for the selected parent values
                allowed_children = set()
                for p_val in parent_vals:
                    if p_val in mapping:
                        allowed_children.update(mapping[p_val])
                
                # Filter child values
                filtered_children = [c for c in child_vals if c in allowed_children]
                removed_children = set(child_vals) - set(filtered_children)
                if removed_children:
                    logger.warning(f"Removing hierarchical child values not belonging to parents {parent_vals}: {removed_children}")
                validated[child_llm_key] = filtered_children

        # Remove empty lists/keys
        cleaned_validated = {k: v for k, v in validated.items() if v}
        return cleaned_validated
