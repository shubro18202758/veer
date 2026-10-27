"""PoC parity, asserted: ``tests/poc_parity.py`` run in-process on the real PoC outputs, READ IN PLACE (skipped where
the PoC directory is absent, e.g. CI; ``$OSINT_POC_DIR`` points at it elsewhere). The script is loaded by path
under its own module name, so it never collides with another package's ``poc_parity``."""

from __future__ import annotations

import importlib.util
import io
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from analysis_fixtures import poc_out_dir

OUT = poc_out_dir() or Path("/nonexistent")
SCRIPT = Path(__file__).with_name("poc_parity.py")

pytestmark = pytest.mark.skipif(
    poc_out_dir() is None, reason="PoC outputs not present (read in place only; set OSINT_POC_DIR)"
)


def _script():
    spec = importlib.util.spec_from_file_location("osint_analysis_poc_parity", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_poc_parity_script_passes_every_check():
    script = _script()
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = script.main(
            [
                "--signals", str(OUT / "signals.raw.json"),
                "--geo", str(OUT / "events.geo.json"),
                "--live", str(OUT / "raw" / "sandbox_city_entities.json"),
            ]
        )
    report = buf.getvalue()
    assert code == 0, report
    assert "PARITY PASS" in report
    assert "FAIL" not in report.replace("PARITY PASS", "")


def test_the_parity_report_prints_no_title_text_url_or_publisher():
    import json

    script = _script()
    buf = io.StringIO()
    with redirect_stdout(buf):
        script.main(
            [
                "--signals", str(OUT / "signals.raw.json"),
                "--geo", str(OUT / "events.geo.json"),
                "--live", str(OUT / "raw" / "sandbox_city_entities.json"),
            ]
        )
    report = buf.getvalue()
    raw = json.loads((OUT / "signals.raw.json").read_text(encoding="utf-8"))
    for s in raw:
        for field in ("title", "url", "publisher"):
            value = s.get(field)
            if value and len(value) > 12:
                assert value not in report, field
    live = json.loads((OUT / "raw" / "sandbox_city_entities.json").read_text(encoding="utf-8"))
    for e in live.get("entities", []):
        if e.get("kind") == "event":
            assert e.get("label", "") not in report
            assert (e.get("props") or {}).get("title", "") not in report
