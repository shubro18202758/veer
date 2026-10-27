"""F-HONEST OSINT-3 (pipeline part): a situation carries only the precision its report gave.

The audit's int3c rows: "Maninagar" (a neighbourhood) carried as segment 1038 Kankaria Road at 1988.5 m with
``area_level False``; Kankaria Lake as segment 1038 at 2268 m. The geocodes below are exactly what a resolver
answered before the fix (an injected resolver may still answer so); the pipeline must not pass them on.
"""

from __future__ import annotations

from analysis_fixtures import FakeResolver, make_signal, point
from osint_analysis.pipeline import run_pipeline

MANINAGAR = (72.6030, 22.9980)
KANKARIA_LAKE = (72.6020, 22.9950)
GITA_MANDIR = (72.5890, 23.0170)


def _one(signals, geocodes):
    result = run_pipeline(signals, resolver=FakeResolver(geocodes))
    assert len(result.resolved) == 1
    return result.resolved[0]


def test_a_neighbourhood_is_area_level_without_a_segment():
    a = make_signal(title="Fire breaks out in a godown in Maninagar", publisher="news-a.example")
    b = make_signal(title="Fire breaks out at a Maninagar godown, tenders rushed", publisher="news-b.example")
    geos = [point(s, MANINAGAR, toponym="Maninagar", feature_type="neighbourhood", segment_id=1038,
                  residual_m=1988.5, snapped_to="Kankaria Road", confidence=0.602) for s in (a, b)]
    r = _one([a, b], geos)
    assert r.is_event and r.toponym == "Maninagar"
    assert r.area_level is True and r.segment_id is None and r.junction_id is None
    assert r.rep_lon is not None  # the area's reference point stays


def test_a_landmark_beyond_900_m_keeps_no_segment():
    a = make_signal(title="Fire at a stall near Kankaria Lake", publisher="news-a.example")
    geos = [point(a, KANKARIA_LAKE, toponym="Kankaria Lake", feature_type="landmark", segment_id=1038,
                  residual_m=2268.1, snapped_to="Kankaria Road", confidence=0.64)]
    r = _one([a], geos)
    assert r.segment_id is None and r.area_level is False and r.toponym == "Kankaria Lake"


def test_a_landmark_within_900_m_keeps_its_segment():
    a = make_signal(title="Fire at a stall near Gita Mandir bus stand", publisher="news-a.example")
    geos = [point(a, GITA_MANDIR, toponym="Gita Mandir", feature_type="landmark", segment_id=1013,
                  residual_m=420.0, snapped_to="Gita Mandir Road", confidence=0.7)]
    assert _one([a], geos).segment_id == 1013
