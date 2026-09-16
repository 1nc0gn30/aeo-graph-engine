"""
Unit tests for AI prompt synthesis and agent JSON-Schema contract.
"""

from aeo_graph_engine.ai_config import synthesize_config_from_prompt, get_agent_json_schema


def test_synthesize_config_from_prompt_basic():
    prompt = "A high-performance Solana DeFi lending protocol called SolarYield on solaryield.fi"
    cfg = synthesize_config_from_prompt(prompt)

    assert cfg["site_name"] == "SolarYield"
    assert cfg["domain"] == "solaryield.fi"
    assert "SolarYield" in cfg["tagline"]
    assert len(cfg["features"]) >= 2
    assert len(cfg["faqs"]) >= 2


def test_synthesize_config_niche_detection():
    prompt_sec = "An open-source OSINT threat intelligence scanner called ThreatRadar on threatradar.io"
    cfg_sec = synthesize_config_from_prompt(prompt_sec)

    assert cfg_sec["site_name"] == "ThreatRadar"
    assert cfg_sec["niche"] == "cybersecurity"

    prompt_local = "A licensed emergency 24/7 plumbing contractor called CityPipes on citypipes.com"
    cfg_local = synthesize_config_from_prompt(prompt_local)

    assert cfg_local["site_name"] == "CityPipes"
    assert cfg_local["niche"] == "local_business"


def test_get_agent_json_schema():
    schema = get_agent_json_schema()
    assert schema["title"] == "AEOConfiguration"
    assert "site_name" in schema["properties"]
    assert "domain" in schema["properties"]
    assert "required" in schema
