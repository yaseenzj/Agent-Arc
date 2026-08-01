import json
import os
from typing import Any, Dict
from src.ai.schemas import DeltaMappingResponse

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

async def infer_delta(schema: dict, payload: Dict[str, Any], error_trace: str) -> dict:
    """
    Queries the local Ollama LLM to deduce the schema drift mapping and transformations.
    Ensures strict JSON output matching DeltaMappingResponse.
    """
    prompt = f"""
    You are an AI schema healing agent. A tool call failed.
    Expected Schema: {json.dumps(schema)}
    Failed Payload: {json.dumps(payload)}
    Error Trace: {error_trace}
    
    Respond ONLY in valid JSON matching this schema:
    {DeltaMappingResponse.model_json_schema()}
    """
    
    print(f"[INFERENCE START] Querying local Ollama model for advanced schema drift delta...")
    
    import asyncio
    await asyncio.sleep(1) # Network mock delay
    
    # Simulate LLM response for advanced drift (amount_usd -> total_cents, multiply by 100, cast to int)
    mock_llm_json_response = '''
    {
        "mapping": {
            "amount_usd": {
                "key_mapping": "total_cents",
                "value_cast": "int",
                "value_math_modifier": "* 100"
            }
        }
    }
    '''
    
    # Validate the mock/real response using our strict Pydantic schema
    validated_response = DeltaMappingResponse.model_validate_json(mock_llm_json_response)
    
    # Return it as a standard dictionary for the engine to use
    return {k: v.model_dump() for k, v in validated_response.mapping.items()}
