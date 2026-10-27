"""Ethics rails across the package (OSINT SPEC §0, §4): no real person's name in any file, no person field in any
structure the package builds, crime_incident never emitted, and no camera, image or frame path to classify from."""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import re
from pathlib import Path

import pytest

from analysis_fixtures import poc_out_dir
from osint_common import ethics
from osint_analysis import attach, correlate, credibility, fusion

PACKAGE = Path(__file__).resolve().parents[1]
_OUT = poc_out_dir()
POC = (_OUT.parent / "veer_osint_poc.py") if _OUT is not None else Path("/nonexistent/veer_osint_poc.py")


def _files() -> list[Path]:
    return sorted(p for p in PACKAGE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)


@pytest.mark.skipif(not POC.is_file(), reason="PoC source not present (read in place only)")
def test_no_denylisted_real_name_anywhere_in_the_package():
    """The PoC's _NAME_DENYLIST names a real person: read its patterns from the PoC AT RUN TIME (ast, in place),
    keep them in memory, report only sha256 prefixes (plan R13)."""
    tree = ast.parse(POC.read_text(encoding="utf-8"))
    patterns: list[re.Pattern[str]] = []
    for node in ast.walk(tree):
        targets = node.targets if isinstance(node, ast.Assign) else []
        if any(isinstance(t, ast.Name) and t.id == "_NAME_DENYLIST" for t in targets):
            for call in node.value.elts:  # type: ignore[attr-defined]
                patterns.append(re.compile(call.args[0].value, re.I if len(call.args) > 1 else 0))
    assert patterns, "the PoC denylist is empty"
    hits = []
    for path in _files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for rx in patterns:
            if rx.search(text):
                hits.append((path.name, hashlib.sha256(rx.pattern.encode()).hexdigest()[:12]))
    assert not hits, hits


@pytest.mark.parametrize(
    "cls",
    [fusion.Member, fusion.BaseCluster, correlate.Situation, credibility.Credibility, attach.LiveSubject],
)
def test_no_internal_structure_has_a_person_field(cls):
    for f in dataclasses.fields(cls):
        assert not ethics.is_forbidden_key(f.name), f"{cls.__name__}.{f.name}"


def test_no_camera_image_or_frame_input_path():
    """Crime enters only from reported text: no module reads an image, a frame or a camera stream."""
    banned = re.compile(r"\b(?:cv2|PIL|imageio|torchvision|VideoCapture|frame_bytes|image_bytes|rtsp://)\b")
    for path in (PACKAGE / "src").rglob("*.py"):
        assert not banned.search(path.read_text(encoding="utf-8")), path.name


def test_crime_incident_appears_only_in_the_guards():
    """The string crime_incident appears in the source only to refuse it."""
    for path in (PACKAGE / "src").rglob("*.py"):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "crime_incident" in line:
                assert re.search(r"never|FORBIDDEN|refus|ANPR|guard|frozenset", line, re.I), f"{path.name}:{n}"
