"""CLI entry points for demo / analyze."""
from __future__ import annotations

from chakravyuh.cli import main


def test_cli_demo_colonial():
    assert main(["demo", "--scenario", "colonial"]) == 0


def test_cli_demo_unknown_scenario():
    assert main(["demo", "--scenario", "does-not-exist"]) == 2


def test_cli_analyze_prints_json(capsys):
    assert main(["analyze", "--scenario", "synnovis"]) == 0
    out = capsys.readouterr().out
    assert "lab_lis" in out
    assert "crown_jewel_protected" in out
