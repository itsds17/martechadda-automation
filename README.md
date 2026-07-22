# AI Filter Mapping System

A terminal-based Python application that converts natural language prompts into validated filters from `filters.json` using Gemini LLM.

## Project Structure

```
├── data/
│   └── filters.json            # Loaded filters definition (copied from new.json)
├── prompts/
│   └── system_prompt.txt       # Base system prompt template
├── .env                        # Environment configuration (API Key, Model)
├── requirements.txt            # Python dependencies
├── main.py                     # CLI Interactive entry point
├── llm.py                      # Gemini SDK wrapper with single retry on parse error
├── prompt_builder.py           # Dynamics system prompt builder
├── json_loader.py              # Dynamic JSON loader
├── mapper.py                   # Core mapping orchestrator
├── parser.py                   # Response JSON cleaner and parser
├── validator.py                # Dynamic hierarchical filter validator
└── verify_cases.py             # Automated test script for specification cases
```

## Setup & Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables in `.env`:
   - `LLM_API_KEY`: Your Gemini API key
   - `LLM_MODEL`: The Gemini model name (default: `gemini-1.5-flash`)

## Usage

### Interactive CLI

To run the interactive CLI:
```bash
python main.py
```

It will ask you to input your business requirements, process them, and output the mapped filter JSON and any missing categories.

### Automated Testing

To run the automated tests verifying the specification's 4 scenarios:
```bash
python verify_cases.py
```

## Logs

Application logs (tracebacks, errors, retry warnings) are stored in `mapping_system.log` to keep the console output clean.
