import pytest
from pydantic import ValidationError

from engine.schemas import DeltaMappingResponse


def test_valid_schema():
    mapping = {"old_key": {"key_mapping": "new_key", "value_cast": "str", "value_math_modifier": None}}
    resp = DeltaMappingResponse(mapping=mapping)
    assert resp.mapping["old_key"].key_mapping == "new_key"

def test_invalid_schema():
    with pytest.raises(ValidationError):
        # Missing 'mapping' key, or passing invalid type
        DeltaMappingResponse(mapping="not_a_dict")
