#!/usr/bin/env python3
"""Agent: Release Manager — generates publishing_report.md with full pipeline summary.

Aggregates pipeline metrics, checkpoint data, render manifest, and quality
report into a comprehensive markdown publishing report.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.lib.agent_base import AgentBase
from shadow_protocol.lib.file_utils import read_json


class ReleaseManagerAgent(AgentBase):
    name = "release_manager"

    def run(self) -> int:
        stage = self.name
        if self.is_done(stage):
            print(f"  SKIP: {stage} already completed")
            return 0

        publish_dir = self.episode_dir / "publish"
        publish_dir.mkdir(parents=True, exist_ok=True)

        report_lines: list[str] = []
        report_lines.append("# Publishing Report\n")
        report_lines.append(f"**Episode:** `{self.episode_dir.name}`\n")
        report_lines.append(f"**Generated:** {self._now()}\n")

        self._add_overview_section(report_lines)
        self._add_asset_summary(report_lines)
        self._add_pipeline_costs(report_lines)
        self._add_quality_section(report_lines)
        self._add_warnings_section(report_lines)
        self._add_render_details(report_lines)

        report_text = "\n".join(report_lines)
        report_path = publish_dir / "publishing_report.md"
        report_path.write_text(report_text)

        self.save_checkpoint(stage)
        print(f"  Wrote publish/publishing_report.md")
        return 0

    def _add_overview_section(self, lines: list[str]) -> None:
        lines.append("\n## Overview\n")
        meta_path = self.episode_dir / "youtube_metadata.json"
        if meta_path.exists():
            meta = read_json(meta_path)
            lines.append(f"- **Title:** {meta.get('title', 'N/A')}")
            lines.append(f"- **Visibility:** {meta.get('visibility', 'N/A')}")
            lines.append(f"- **Language:** {meta.get('language', 'N/A')}")
            lines.append(f"- **Category:** {meta.get('category', 'N/A')}")

        qc_path = self.episode_dir / "publish" / "quality_report.json"
        if qc_path.exists():
            qc = read_json(qc_path)
            lines.append(f"- **QC Status:** {'PASSED' if qc.get('passed') else 'FAILED'}")
            summary = qc.get("summary", {})
            lines.append(f"- **Checks:** {summary.get('passed', 0)}/{summary.get('total', 0)} passed")
        lines.append("")

    def _add_asset_summary(self, lines: list[str]) -> None:
        lines.append("\n## Asset Summary\n")
        lines.append("| Asset | Size | Status |")
        lines.append("|-------|------|--------|")

        manifest_path = self.episode_dir / "publish" / "publish_manifest.json"
        if manifest_path.exists():
            manifest = read_json(manifest_path)
            for asset in manifest.get("assets", []):
                name = asset.get("name", "?")
                size = asset.get("size_bytes", 0)
                exists = asset.get("exists", False)
                size_str = self._format_size(size)
                status = "✓" if exists else "✗"
                lines.append(f"| {name} | {size_str} | {status} |")
        else:
            lines.append("| _No publish manifest found_ | | |")
        lines.append("")

    def _add_pipeline_costs(self, lines: list[str]) -> None:
        lines.append("\n## Pipeline Costs\n")
        lines.append("| Stage | Tokens | Cost | Duration |")
        lines.append("|-------|--------|------|----------|")

        metrics_dir = self.episode_dir / "metrics"
        total_tokens = 0
        total_cost = 0.0
        total_duration = 0.0

        if metrics_dir.exists():
            for f in sorted(metrics_dir.glob("*.json")):
                try:
                    stage_data = json.loads(f.read_text())
                    stage = stage_data.get("stage", f.stem)
                    tokens = stage_data.get("total_tokens", 0)
                    cost = stage_data.get("cost_usd", 0.0)
                    duration = stage_data.get("duration_seconds", 0.0)

                    if tokens or cost or duration:
                        lines.append(
                            f"| {stage} | {tokens} | ${cost:.4f} | {duration:.1f}s |"
                        )
                        total_tokens += tokens
                        total_cost += cost
                        total_duration += duration
                except Exception:
                    pass

        lines.append("| **Total** | **{}** | **${:.4f}** | **{:.1f}s** |".format(
            total_tokens, total_cost, total_duration
        ))
        lines.append("")
        lines.append(f"- **Total LLM Calls:** {self._total_llm_calls()}")
        lines.append(f"- **Total Pipeline Cost:** ${total_cost:.6f}")
        lines.append("")

    def _add_quality_section(self, lines: list[str]) -> None:
        lines.append("\n## Quality Checks\n")

        qc_path = self.episode_dir / "publish" / "quality_report.json"
        if qc_path.exists():
            qc = read_json(qc_path)
            for check in qc.get("checks", []):
                icon = "✓" if check.get("passed") else "✗"
                severity = check.get("severity", "info").upper()
                lines.append(f"- {icon} [{severity}] {check.get('message', '')}")
        else:
            lines.append("_No quality report available_")
        lines.append("")

    def _add_warnings_section(self, lines: list[str]) -> None:
        lines.append("\n## Warnings\n")

        warnings: list[str] = []

        qc_path = self.episode_dir / "publish" / "quality_report.json"
        if qc_path.exists():
            qc = read_json(qc_path)
            warnings.extend(qc.get("warnings", []))

        manifest_path = self.episode_dir / "publish" / "publish_manifest.json"
        if manifest_path.exists():
            manifest = read_json(manifest_path)
            warnings.extend(manifest.get("warnings", []))

        if warnings:
            for w in warnings:
                lines.append(f"- {w}")
        else:
            lines.append("_No warnings_")
        lines.append("")

    def _add_render_details(self, lines: list[str]) -> None:
        lines.append("\n## Render Details\n")

        render_path = self.episode_dir / "render" / "render_manifest.json"
        if render_path.exists():
            render = read_json(render_path)
            lines.append(f"- **Render time:** {render.get('duration_seconds', 0)}s")
            lines.append(f"- **Output size:** {self._format_size(render.get('output_size_bytes', 0))}")
            lines.append(f"- **Scenes:** {render.get('succeeded_scenes', 0)} succeeded, {render.get('failed_scenes', 0)} failed")

        final_video = self.episode_dir / "render" / "final_video.mp4"
        if final_video.exists():
            import subprocess
            try:
                result = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "csv=p=0", str(final_video.resolve())],
                    capture_output=True, text=True, timeout=30,
                )
                if result.returncode == 0 and result.stdout.strip():
                    duration = float(result.stdout.strip())
                    lines.append(f"- **Video duration:** {duration:.1f}s")
            except Exception:
                pass

        lines.append("")

    def _total_llm_calls(self) -> int:
        total = 0
        metrics_dir = self.episode_dir / "metrics"
        if metrics_dir.exists():
            for f in metrics_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text())
                    total += data.get("llm_calls", 0)
                except Exception:
                    pass
        return total

    def _format_size(self, bytes_val: int) -> str:
        if bytes_val >= 1_000_000:
            return f"{bytes_val / 1_000_000:.1f} MB"
        elif bytes_val >= 1_000:
            return f"{bytes_val / 1_000:.1f} KB"
        return f"{bytes_val} B"

    def _now(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


def run(input_dir: str, output_dir: str, config: dict) -> int:
    agent = ReleaseManagerAgent(input_dir, config)
    return agent.run()


if __name__ == "__main__":
    _, input_dir, output_dir, config_path = sys.argv
    config = json.load(open(config_path))
    config["root"] = str(Path(config_path).parent.parent.parent)
    sys.exit(run(input_dir, output_dir, config))
