"""Tests for agent implementations."""

import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.lib.agent_base import AgentBase, AgentError


def test_agent_load_prompt(tmp_path: Path):
    """AgentBase.load_prompt should find prompts by name."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "test_agent.md").write_text("You are a test agent.")

    config = {"root": str(tmp_path)}
    agent = AgentBase(tmp_path, config)
    content = agent.load_prompt("test_agent")
    assert content == "You are a test agent."


def test_agent_load_prompt_not_found(tmp_path: Path):
    config = {"root": str(tmp_path)}
    agent = AgentBase(tmp_path, config)
    try:
        agent.load_prompt("nonexistent")
        assert False, "Should have raised"
    except AgentError as e:
        assert e.code == "PROMPT_NOT_FOUND"


def test_agent_load_bible(tmp_path: Path):
    bible_dir = tmp_path / "bible"
    bible_dir.mkdir()
    (bible_dir / "characters.json").write_text(json.dumps({"characters": []}))
    (bible_dir / "themes.json").write_text(json.dumps({"themes": []}))

    config = {"root": str(tmp_path)}
    agent = AgentBase(tmp_path, config)
    bible = agent.load_bible()
    assert "characters" in bible
    assert "themes" in bible
    assert bible["characters"] == {"characters": []}


def test_agent_write_and_read(tmp_path: Path):
    config = {"root": str(tmp_path)}
    agent = AgentBase(tmp_path, config)

    agent.write_json("test.json", {"hello": "world"})
    assert (tmp_path / "test.json").exists()

    data = agent.read_json("test.json")
    assert data == {"hello": "world"}

    agent.write_text("test.txt", "hello world")
    assert agent.read_text("test.txt") == "hello world"


def test_agent_checkpoint(tmp_path: Path):
    config = {"root": str(tmp_path)}
    agent = AgentBase(tmp_path, config)

    assert agent.is_done("stage_1") is False

    agent.save_checkpoint("stage_1")
    assert agent.is_done("stage_1") is True

    assert "stage_1" in agent.completed_stages
