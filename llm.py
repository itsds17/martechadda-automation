import os
import time
import logging
from typing import Dict, Any, Callable
from groq import Groq, GroqError

logger = logging.getLogger("FilterMappingSystem.llm")

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model_name = os.getenv("GROQ_MODEL")
        
        # Strict validation: GROQ_API_KEY must be present
        if not self.api_key or not self.api_key.strip():
            logger.error("GROQ_API_KEY environment variable is missing or empty.")
            raise ValueError(
                "Configuration Error: GROQ_API_KEY is missing or empty. "
                "Please configure it in your .env file."
            )
            
        # Strict validation: GROQ_MODEL must be present (no fallback)
        if not self.model_name or not self.model_name.strip():
            logger.error("GROQ_MODEL environment variable is missing or empty.")
            raise ValueError(
                "Configuration Error: GROQ_MODEL is missing or empty. "
                "Please configure it in your .env file."
            )

        logger.info(f"Initializing Groq Client with model: {self.model_name}")
        try:
            self.client = Groq(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            raise RuntimeError(f"Failed to initialize Groq client: {e}")

    def generate(self, prompt: str, parser_fn: Callable[[str], Dict[str, Any]]) -> Dict[str, Any]:
        """Calls Groq to map filters, with automatic single retry if parsing fails."""
        
        def _execute_call(temp: float) -> str:
            logger.info(f"Sending generation request to Groq (model={self.model_name}, temp={temp})...")
            
            t_api_start = time.perf_counter()
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model_name,
                temperature=temp,
            )
            t_api = time.perf_counter() - t_api_start
            logger.info(f"Performance Metrics: LLM API Call took {t_api:.4f}s")
            
            if not chat_completion.choices or not chat_completion.choices[0].message.content:
                logger.error("Groq returned an empty response.")
                raise ValueError("The LLM returned an empty response.")
                
            return chat_completion.choices[0].message.content

        try:
            # First attempt
            raw_text = _execute_call(temp=0.1)
            logger.debug(f"Raw response text: {raw_text}")
            
            t_parse_start = time.perf_counter()
            try:
                parsed_data = parser_fn(raw_text)
                t_parse = time.perf_counter() - t_parse_start
                logger.info(f"Performance Metrics: Response Parsing took {t_parse:.4f}s")
                return parsed_data
            except ValueError as parse_err:
                logger.warning(f"Initial JSON parsing failed: {parse_err}. Retrying request once...")
                
                # Single auto-retry with temperature 0.0
                retry_text = _execute_call(temp=0.0)
                
                t_parse_start = time.perf_counter()
                parsed_data = parser_fn(retry_text)
                t_parse = time.perf_counter() - t_parse_start
                logger.info(f"Performance Metrics: Retry Response Parsing took {t_parse:.4f}s")
                return parsed_data
                
        except GroqError as api_err:
            logger.error(f"Groq API exception: {api_err}")
            raise RuntimeError(f"Groq API failure: {api_err}")
        except Exception as e:
            logger.error(f"Unexpected error during LLM generation: {e}")
            raise
