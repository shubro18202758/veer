"""PoC parity, asserted: the real PoC signals read in place (skipped where the PoC directory is absent, e.g. CI).

``tests/poc_parity.py`` is loaded under its own module name, so this package's parity script never collides with
another package's ``poc_parity`` module in one interpreter.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location("osint_geo_poc_parity", Path(__file__).with_name("poc_parity.py"))
assert _SPEC is not None and _SPEC.loader is not None
poc_parity = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(poc_parity)

SIGNALS = poc_parity.POC_SIGNALS
pytestmark = pytest.mark.skipif(not SIGNALS.is_file(), reason=f"PoC signals not present at {SIGNALS}")


@pytest.fixture(scope="module")
def report():
    return poc_parity.run(SIGNALS)


def test_25_geotagged_as_15_points_1_district_9_state(report):
    # the PoC's 27/17 included two bare area words pinned on junctions ("Sola", "Motera"): F-HONEST OSINT-1
    c = report["counts"]
    assert (c["signals"], c["geotagged"], c["points"], c["district"], c["state"]) == (107, 25, 15, 1, 9)


def test_karnavati_club(report):
    m = report["karnavati"]["mine"]
    assert m["segment_id"] == 1045 and m["residual_m"] == pytest.approx(190.5, abs=5)
    assert m["confidence"] == pytest.approx(0.719, abs=0.01) and m["bucket"] == "medium"


def test_odhav_robbery_is_the_neighbourhood_not_junction_11(report):
    # F-HONEST OSINT-1: "...Abducted from Odhav's Rajendra Park Bridge" names the neighbourhood and another bridge;
    # the PoC (and Veer before the fix) pinned it on Odhav Ring Road Circle, junction 11, at residual 0
    m = report["odhav"]["mine"]
    assert m["toponym"] == "Odhav" and m["feature_type"] == "neighbourhood"
    assert m["junction_id"] is None and m["segment_id"] is None and m["residual_m"] is None


def test_every_signal_matches_the_poc_or_is_an_honest_divergence(report):
    bad = [r for r in report["rows"] if r["status"] == "MISMATCH"]
    assert bad == []
    honest = sorted(r["signal_id"][:10] for r in report["rows"] if r["status"] == "honest-divergence")
    assert honest == sorted(poc_parity.HONEST_DIVERGENCES)


def test_zero_india_indira_and_budget(report):
    assert report["counts"]["india_mentions"] > 0 and report["counts"]["indira_false_matches"] == 0
    assert report["timing_ms"]["resolve_all"] < 2000


def test_every_check(report):
    assert report["passed"], {k: v for k, v in report["checks"].items() if not v}
