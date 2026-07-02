"""Context Manager — extract only the relevant context needed by each agent.

Never loads entire files when only partial context is needed.
Provides character, location, mystery, and theme extraction from bible data.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any


def load_bible(bible_dir: str | Path) -> dict[str, Any]:
    """Load all bible JSON files from the bible directory."""
    bible_dir = Path(bible_dir)
    result = {}
    if not bible_dir.exists():
        return result
    for f in sorted(bible_dir.glob("*.json")):
        try:
            result[f.stem] = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            result[f.stem] = {}
    return result


def get_relevant_characters(section_text: str, bible_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return only characters whose name appears in the section text."""
    text_lower = section_text.lower()
    characters = bible_data.get("characters", {}).get("characters", [])
    matching = []
    for char in characters:
        name = char.get("name", "")
        if name and name.lower() in text_lower:
            matching.append(char)
    return matching


def get_relevant_locations(section_text: str, bible_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return only locations whose name appears in the section text."""
    text_lower = section_text.lower()
    locations = bible_data.get("locations", {}).get("locations", [])
    matching = []
    for loc in locations:
        name = loc.get("name", "")
        if name and name.lower() in text_lower:
            matching.append(loc)
    return matching


def get_relevant_mysteries(section_text: str, bible_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return only mysteries referenced in the section text."""
    text_lower = section_text.lower()
    mysteries = bible_data.get("unresolved_mysteries", {}).get("mysteries", [])
    matching = []
    for mystery in mysteries:
        title = mystery.get("title", "")
        desc = mystery.get("description", "")
        if (title and title.lower() in text_lower) or (desc and desc.lower() in text_lower):
            matching.append(mystery)
    return matching


def get_relevant_themes(section_text: str, bible_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return only themes referenced in the section text."""
    text_lower = section_text.lower()
    themes = bible_data.get("themes", {}).get("themes", [])
    matching = []
    for theme in themes:
        name = theme.get("name", "")
        tid = theme.get("id", "")
        if (name and name.lower() in text_lower) or (tid and tid.lower() in text_lower):
            matching.append(theme)
    return matching


def get_bible_summary(bible_data: dict[str, Any]) -> dict[str, Any]:
    """Return a condensed bible summary — name/role for characters,
    name/description for locations, theme names, mystery titles.
    Use this when there is no section text to match against (e.g. production_package)."""
    summary: dict[str, Any] = {}

    characters = bible_data.get("characters", {}).get("characters", [])
    if characters:
        summary["characters"] = [
            {"name": c.get("name"), "role": c.get("role")}
            for c in characters if c.get("name")
        ]

    locations = bible_data.get("locations", {}).get("locations", [])
    if locations:
        summary["locations"] = [
            {"name": l.get("name"), "description": l.get("description")}
            for l in locations if l.get("name")
        ]

    themes = bible_data.get("themes", {}).get("themes", [])
    if themes:
        summary["themes"] = [t.get("name") for t in themes if t.get("name")]

    mysteries = bible_data.get("unresolved_mysteries", {}).get("mysteries", [])
    if mysteries:
        summary["unresolved_mysteries"] = [
            {"title": m.get("title"), "description": m.get("description")}
            for m in mysteries if m.get("title")
        ]

    return summary


def build_context(
    section_text: str,
    bible_data: dict[str, Any],
    production_package: dict[str, Any] | None = None,
    outline_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a minimal context dict containing only relevant entities.

    Args:
        section_text: The agent's current input text to match against.
        bible_data: Full bible data (use load_bible() to get this).
        production_package: Optional production package for additional context.
        outline_data: Optional outline for additional context.

    Returns:
        A dict with only the relevant characters, locations, themes, mysteries.
    """
    context: dict[str, Any] = {}

    characters = get_relevant_characters(section_text, bible_data)
    if characters:
        context["characters"] = characters

    locations = get_relevant_locations(section_text, bible_data)
    if locations:
        context["locations"] = locations

    themes = get_relevant_themes(section_text, bible_data)
    if themes:
        context["themes"] = themes

    mysteries = get_relevant_mysteries(section_text, bible_data)
    if mysteries:
        context["mysteries"] = mysteries

    return context
