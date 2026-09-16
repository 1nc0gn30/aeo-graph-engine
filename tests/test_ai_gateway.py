"""
Unit tests for AI Gateway and Key/Port Management (ai_gateway.py).
"""

import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from aeo_graph_engine.ai_gateway import AIGateway, DEFAULT_AI_GATEWAY_CONFIG


def test_ai_gateway_defaults(tmp_path):
    cfg_file = tmp_path / "test_ai_cfg.json"
    gateway = AIGateway(cfg_file)
    status = gateway.get_public_status()

    assert status["active_provider"] == "heuristic"
    assert "ollama" in status["endpoints"]
    assert "openai" in status["endpoints"]
    assert status["endpoints"]["ollama"] == "http://127.0.0.1:11434"
    assert status["endpoints"]["lm_studio"] == "http://127.0.0.1:1234/v1"
    assert len(status["supported_providers"]) >= 7


def test_ai_gateway_save_and_load(tmp_path):
    cfg_file = tmp_path / "test_ai_cfg.json"
    gateway = AIGateway(cfg_file)

    # Save new settings
    new_settings = {
        "active_provider": "ollama",
        "active_model": "llama3.2:3b",
        "temperature": 0.5,
        "endpoints": {
            "ollama": "http://127.0.0.1:11434",
            "lm_studio": "http://127.0.0.1:1234/v1",
        },
        "keys": {
            "openai": "sk-test1234567890abcdef",
            "anthropic": "sk-ant-test9876543210",
        },
        "mcp_gateway_port": 8092,
    }
    assert gateway.save_config(new_settings) is True
    assert cfg_file.exists()

    # Load fresh gateway instance from same file
    gateway2 = AIGateway(cfg_file)
    status2 = gateway2.get_public_status()

    assert status2["active_provider"] == "ollama"
    assert status2["active_model"] == "llama3.2:3b"
    assert status2["temperature"] == 0.5
    assert status2["mcp_gateway_port"] == 8092
    assert status2["keys_status"]["openai"] is True
    assert status2["keys_status"]["anthropic"] is True
    assert status2["masked_keys"]["openai"] == "sk-t...cdef"


def test_ai_gateway_heuristic_test():
    gateway = AIGateway()
    res = gateway.test_connection("heuristic")
    assert res["success"] is True
    assert "Built-in Heuristic" in res["message"]


def test_ai_gateway_ollama_test_mocked():
    gateway = AIGateway()
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps({"models": [{"name": "llama3.2:latest"}]}).encode("utf-8")
    mock_response.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_response):
        res = gateway.test_connection("ollama", endpoint="http://127.0.0.1:11434")
        assert res["success"] is True
        assert "Connected to Ollama" in res["message"]
        assert "llama3.2:latest" in res["models"]


def test_ai_gateway_openai_test_mocked():
    gateway = AIGateway()
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps({"data": [{"id": "gpt-4o"}]}).encode("utf-8")
    mock_response.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_response):
        res = gateway.test_connection("openai", api_key="sk-testkey123")
        assert res["success"] is True
        assert "OPENAI API Key verified" in res["message"]


def test_simulate_answer_engine_perception():
    gateway = AIGateway()
    sim = gateway.simulate_answer_engine_perception("SolarYield", "solaryield.fi")
    assert sim["brand_name"] == "SolarYield"
    assert sim["domain"] == "solaryield.fi"
    assert "https://solaryield.fi/llms.txt" in sim["top_sources_cited"]
    assert len(sim["simulated_answer"]) > 50
