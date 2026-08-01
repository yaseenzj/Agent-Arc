from pydantic import BaseModel, Field
from typing import Dict, Optional

class DeltaMappingRule(BaseModel):
    key_mapping: str = Field(description="The new key name expected by the schema.")
    value_cast: str = Field(description="The Python type to cast the value into (e.g., 'int', 'float', 'str').")
    value_math_modifier: Optional[str] = Field(None, description="Optional math operation string to evaluate (e.g., '* 100').")

class DeltaMappingResponse(BaseModel):
    """
    Strict JSON output format enforced on the LLM.
    We want a dictionary mapping old schema keys to their transformation rules.
    Example: {"amount_usd": {"key_mapping": "total_cents", "value_cast": "int", "value_math_modifier": "* 100"}}
    """
    mapping: Dict[str, DeltaMappingRule] = Field(
        ..., 
        description="A dictionary mapping the old rejected keys to the transformation rules."
    )
