import pytest
from app.services.prompt_router import get_prompts
from app.models.enums import AnalysisModule

def test_get_prompts_message():
    system, user = get_prompts("message", "Hola")
    assert "Analiza el siguiente mensaje" in user
    assert "Hola" in user
    assert len(system) > 0

def test_get_prompts_invalid_module():
    with pytest.raises(ValueError, match="Módulo no válido"):
        get_prompts("invalid", "test")

def test_get_prompts_all_modules():
    for module in AnalysisModule:
        system, user = get_prompts(module.value, "test")
        assert len(system) > 0
        assert "test" in user
