import pytest
from pydantic import ValidationError
from src.ai.schemas import DeltaMappingResponse

def test_valid_schema():
    mapping = {"old_key": "new_key"}
    resp = DeltaMappingResponse(mapping=mapping)
    assert resp.mapping == mapping

def test_invalid_schema():
    with pytest.raises(ValidationError):
        # Missing 'mapping' key, or passing invalid type
        DeltaMappingResponse(mapping="not_a_dict")
