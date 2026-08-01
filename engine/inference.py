import json
import os
from typing import Any

from groq import AsyncGroq

from engine.schemas import DeltaMappingResponse


async def infer_delta(schema: dict, payload: dict[str, Any], error_trace: str) -> dict:
    """
    Queries Groq's insanely fast LPU LLM to deduce the schema drift mapping.
    Ensures strict JSON output matching DeltaMappingResponse.
    """
    print("[INFERENCE START] Querying Groq Cloud LLM for advanced schema drift delta...")
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("[ERROR] GROQ_API_KEY not found in .env! Cannot perform inference.")
        raise ValueError("GROQ_API_KEY missing. Please add it to your .env file.")

    client = AsyncGroq(api_key=api_key)
    
    prompt = f"""
    You are an AI schema healing agent. A tool call failed.
    Expected Schema: {json.dumps(schema)}
    Failed Payload: {json.dumps(payload)}
    Error Trace: {error_trace}
    
    You must map the incorrect fields in the failed payload to the correct fields in the expected schema.
    If the value type needs to change, specify 'value_cast'. 
    If the value needs math applied (e.g. dollars to cents), specify 'value_math_modifier' (e.g. '* 100').
    
    Respond ONLY in valid JSON matching this schema:
    {json.dumps(DeltaMappingResponse.model_json_schema())}
    """
    
    messages = [
        {"role": "system", "content": "You are a specialized JSON-only schema drift resolver."},
        {"role": "user", "content": prompt}
    ]
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                messages=messages,
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            raw_json_response = response.choices[0].message.content
            print(f"[LLM RAW RESPONSE]\n{raw_json_response}\n")
            
            # Validate the response using our strict Pydantic schema
            validated_response = DeltaMappingResponse.model_validate_json(raw_json_response)
            
            # Return it as a standard dictionary for the engine to use
            return {k: v.model_dump() for k, v in validated_response.mapping.items()}
            
        except Exception as e:
            print(f"[AGENTIC REFLECTION] Attempt {attempt+1} failed: {e!s}")
            if attempt < max_retries - 1:
                print("[AGENTIC REFLECTION] Asking LLM to self-correct its mistake...")
                messages.append({"role": "assistant", "content": raw_json_response if 'raw_json_response' in locals() else "{}"})
                messages.append({"role": "user", "content": f"Your last response failed validation with error: {e!s}. Please fix your JSON and try again."})
            else:
                raise
            
async def negotiate_vendor_swap(broken_tool: str, backup_tool: str, payload: dict, backup_schema: str) -> dict:
    """
    LLM call to translate a payload from a broken vendor's format into a backup vendor's format.
    """
    prompt = f"""
    The primary API vendor '{broken_tool}' went offline (500 Error).
    We are autonomously swapping to the backup vendor '{backup_tool}'.
    
    Original Payload:
    {json.dumps(payload)}
    
    Backup Vendor Schema:
    {backup_schema}
    
    Return a JSON object containing ONLY the translated payload matching the Backup Vendor Schema.
    Do not return the mapping rules, return the actual translated payload values.
    """
    
    messages = [
        {"role": "system", "content": "You are a JSON-only API payload translator."},
        {"role": "user", "content": prompt}
    ]
    
    response = await client.chat.completions.create(
        messages=messages,
        model="llama-3.1-8b-instant",
        response_format={"type": "json_object"},
        temperature=0.0
    )
    
    raw_json_response = response.choices[0].message.content
    print(f"[VENDOR SWAP LLM] Translated Payload:\n{raw_json_response}\n")
    return json.loads(raw_json_response)
