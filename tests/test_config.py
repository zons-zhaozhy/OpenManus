"""
Configuration module tests
"""

from pathlib import Path

import pytest
from pydantic_core import ValidationError

from app.config import AppConfig, GlobalPromptSettings, LLMSettings


def test_global_prompt_settings():
    """Test global prompt settings configuration"""
    settings = GlobalPromptSettings(
        meta_prompt="Test meta prompt",
        language_preference="en",
        thinking_language="en",
        response_language="en",
        global_instructions=["Test instruction 1", "Test instruction 2"],
    )
    assert settings.meta_prompt == "Test meta prompt"
    assert settings.language_preference == "en"
    assert len(settings.global_instructions) == 2


def test_llm_settings():
    """Test LLM configuration"""
    settings = LLMSettings(
        model="gpt-4",
        base_url="https://api.openai.com/v1",
        api_key="test_key",
        temperature=0.7,
        max_tokens=2000,
        api_type="Openai",
        api_version="2024-03-01",
    )
    assert settings.model == "gpt-4"
    assert settings.api_key == "test_key"
    assert settings.temperature == 0.7
    assert settings.max_tokens == 2000
    assert settings.api_type == "Openai"


def test_app_config(tmp_path):
    """Test App configuration"""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    llm_settings = LLMSettings(
        model="gpt-4",
        base_url="https://api.openai.com/v1",
        api_key="test_key",
        api_type="Openai",
        api_version="2024-03-01",
    )

    config = AppConfig(
        llm={"default": llm_settings},
        global_prompts=GlobalPromptSettings(
            meta_prompt="Test meta prompt",
            language_preference="en",
            thinking_language="en",
            response_language="en",
        ),
    )

    assert config.llm["default"].model == "gpt-4"
    assert config.global_prompts.meta_prompt == "Test meta prompt"


def test_invalid_llm_settings():
    """Test configuration validation"""
    with pytest.raises(ValidationError):
        LLMSettings(
            model="gpt-4",
            base_url="https://api.openai.com/v1",
            api_key="test_key",
            api_type="NonExistentProvider",  # Invalid API type
            api_version="2024-03-01",
        )

    with pytest.raises(ValueError):
        GlobalPromptSettings(
            meta_prompt="",  # Empty meta prompt
            language_preference="invalid_lang",
            thinking_language="en",
            response_language="en",
        )
