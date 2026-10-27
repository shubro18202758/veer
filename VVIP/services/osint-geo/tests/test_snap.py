"""The network of record and the snap: residuals, the junction-versus-segment rule, points outside the network."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest
from shapely.geometry import LineString

from osint_geo import snap as snap_mod
from osint_geo.gazetteer import load as load_gazetteer
from osint_geo.resolver import GazetteerResolver
from osint_geo.snap import JUNCTION_TOL_M, MAX_SNAP_M, Network, geodesic_m, interior_point, load_network, snap

REPO = Path(__file__).resolve().parents[3]
NETWORK_JSON = REPO / "scripts" / "data" / "osm_network.json"
KARNAVATI = (72.503, 23.009)  # the seed point of "Karnavati Club (SG Highway)"


@pytest.fixture(scope="module")
def net() -> Network:
    return load_network()


def _offset(lon: float, lat: float, east_m: float, north_m: float) -> tuple[float, float]:
    return (lon + east_m / (111_320.0 * math.cos(math.radians(lat))), lat + north_m / 110_574.0)


def test_network_is_the_49_segments_and_34_junctions_of_record(net):
    doc = json.loads(NETWORK_JSON.read_text(encoding="utf-8"))
    assert sorted(net.segments) == sorted(s["segment_id"] for s in doc["segments"]) == list(range(1001, 1050))
    assert sorted(net.junctions) == sorted(j["junction_id"] for j in doc["junctions"]) == list(range(1, 35))
    assert net.path is not None and net.path.name == "osm_network.json"


def test_anchor_is_st_pointonsurface_and_the_gazetteer_road_point(net):
    gaz = load_gazetteer()
    roads = {e.segment_id: e for e in gaz.entries if e.feature_type == "road"}
    for sid, seg in net.segments.items():
        pos = LineString(seg.line).point_on_surface()  # GEOS, as PostGIS ST_PointOnSurface
        assert seg.anchor == (pos.x, pos.y) == interior_point(seg.line)
        # the anchor is a vertex of the stored line (GEOS InteriorPointLine)
        assert seg.anchor in seg.line
        assert (roads[sid].lon, roads[sid].lat) == (round(seg.anchor[0], 7), round(seg.anchor[1], 7))


@pytest.mark.parametrize(
    "line",
    [
        [(0.0, 0.0), (1.0, 0.0)],  # no interior vertex: the nearer endpoint (the first on a tie)
        [(0.0, 0.0), (1.0, 0.0), (3.0, 0.0)],
        [(0.0, 0.0), (0.0, 0.0), (2.0, 0.0), (2.0, 1.0)],  # a zero-length piece
        [(1.0, 1.0), (2.0, 3.0), (2.0, 3.0), (5.0, -1.0), (0.0, 0.0)],
        [(72.5, 23.0), (72.51, 23.01), (72.52, 23.0), (72.53, 23.01), (72.54, 23.0)],
    ],
)
def test_interior_point_is_geos_interior_point_line(line):
    pos = LineString(line).point_on_surface()
    assert interior_point(line) == (pos.x, pos.y)


def test_the_anchor_is_the_stdlib_function_the_generator_uses():
    from osint_geo import geom

    assert snap_mod.interior_point is geom.interior_point is interior_point


def test_karnavati_club_snaps_to_sg_highway_1045_at_190_m(net):
    sid, jid, name, residual = snap(*KARNAVATI)
    assert (sid, jid, name) == (1045, None, "SG Highway (Prahlad Nagar)")
    assert residual == pytest.approx(190.5, abs=0.5)
    # the residual is the geodesic distance to the segment's anchor ...
    anchor = net.segments[1045].anchor
    assert residual == round(geodesic_m(*KARNAVATI, *anchor), 1)
    # ... and the road line itself passes closer (the distance shown for display)
    line_m = net.line_distance_m(*KARNAVATI, 1045)
    assert line_m == pytest.approx(137.7, abs=1.0) and line_m < residual


def test_residual_grows_with_the_distance_from_the_anchor(net):
    lon, lat = net.segments[1005].anchor  # Relief Road
    last = -1.0
    for d in (0.0, 20.0, 60.0, 150.0):
        sid, _, _, residual = net.snap(*_offset(lon, lat, 0.0, d), junction_tol_m=0.0)
        assert sid == 1005 and residual >= last
        assert residual == pytest.approx(d, abs=1.0)
        last = residual


def test_a_point_at_a_junction_node_is_at_the_junction(net):
    j = net.junctions[11]
    assert snap(j.lon, j.lat) == (None, 11, "Odhav Ring Road Circle (SP Ring Road)", 0.0)
    near = _offset(j.lon, j.lat, 15.0, 0.0)
    sid, jid, _, residual = snap(*near)
    assert (sid, jid) == (None, 11) and residual == pytest.approx(15.0, abs=0.5) and residual <= JUNCTION_TOL_M


def test_beyond_the_junction_tolerance_a_point_is_on_a_segment(net):
    j = net.junctions[11]
    sid, jid, name, residual = snap(*_offset(j.lon, j.lat, 40.0, 0.0))
    assert jid is None and sid in net.segments and name == net.segments[sid].road_name
    # Odhav Ring Road Circle sits on the ring road, whose segment anchors are all farther than the 2.5 km reach:
    # the point attaches to the road line passing beside it, and the residual is the distance to that line
    assert net.nearest_segment(*_offset(j.lon, j.lat, 40.0, 0.0))[1] > MAX_SNAP_M
    assert residual <= 45.0


def test_a_landmark_near_a_segment_keeps_a_road_anchor_and_a_neighbourhood_never_does():
    r = GazetteerResolver()
    station = next(e for e in r.gazetteer.entries if e.canonical_name == "Kalupur Railway Station")
    seg, jct, snapped_to, residual, sq = r._anchor(station)
    assert seg == 1014 and jct is None and residual is not None and residual < 200.0 and sq > 0.9
    # F-HONEST OSINT-3: a neighbourhood is an area, even when its point is 13 m from a junction (Odhav)
    odhav = next(e for e in r.gazetteer.entries if e.canonical_name == "Odhav")
    assert r._anchor(odhav) == (None, None, None, None, 0.0)


def test_no_landmark_keeps_a_segment_beyond_900_m():
    # F-HONEST OSINT-3: Kankaria Lake snapped to Kankaria Road 2268 m away, Civil Hospital Asarwa to segment 1043
    # 2053 m away; both were carried as that road. Beyond fusion's on-segment limit there is no road anchor.
    r = GazetteerResolver()
    for name in ("Kankaria Lake", "Civil Hospital Asarwa", "SVP International Airport"):
        e = next(x for x in r.gazetteer.entries if x.canonical_name == name)
        assert r.network.snap(e.lon, e.lat, junction_tol_m=0.0).residual_m > 900.0, name
        assert r._anchor(e) == (None, None, None, None, 0.0), name


def test_junction_rule_off_for_landmarks(net):
    # ISKCON Temple's seed point sits about 6 m from Iskcon Cross Roads (junction 9): with the rule on it is the
    # junction, and with it off (how the resolver snaps landmarks and neighbourhoods) it is a segment
    lon, lat = 72.5070, 23.0272
    assert snap(lon, lat).junction_id == 9
    off = snap(lon, lat, junction_tol_m=0.0)
    assert off.junction_id is None and off.segment_id in net.segments


def test_resolver_keeps_junction_ids_and_snaps_landmarks():
    r = GazetteerResolver()
    gaz = r.gazetteer
    for e in gaz.entries:
        seg, jct, snapped_to, residual, sq = r._anchor(e)
        if e.feature_type == "junction":
            assert (seg, jct, snapped_to, residual, sq) == (None, e.junction_id, None, 0.0, 1.0)
        elif e.feature_type == "road":
            assert (seg, jct, snapped_to, residual, sq) == (e.segment_id, None, None, 0.0, 1.0)
        else:
            assert jct is None
            if e.feature_type == "neighbourhood":  # an area: never a road anchor (F-HONEST OSINT-3)
                assert (seg, snapped_to, residual, sq) == (None, None, None, 0.0)
            elif seg is None:  # beyond 900 m: no road anchor, no snap credit
                assert (snapped_to, residual, sq) == (None, None, 0.0)
            else:
                assert snapped_to == r.network.segments[seg].road_name and 0.0 <= residual <= 900.0
                assert 0.64 <= sq <= 1.0


@pytest.mark.parametrize(
    "lon,lat",
    [
        (72.0, 23.0),  # ~50 km west of the city
        (72.58, 23.40),  # ~35 km north
        (77.2090, 28.6139),  # another city altogether
    ],
)
def test_points_outside_the_network_have_no_anchor(lon, lat):
    sid, jid, name, residual = snap(lon, lat)
    assert (sid, jid, name) == (None, None, None)
    assert residual > MAX_SNAP_M


def test_the_reach_is_inclusive_and_configurable(net):
    lon, lat = net.segments[1005].anchor
    far = _offset(lon, lat, 0.0, -600.0)
    within = net.snap(*far, junction_tol_m=0.0)
    assert within.segment_id is not None
    # the reach is inclusive: exactly the residual still attaches
    assert net.snap(*far, junction_tol_m=0.0, max_m=within.residual_m).segment_id == within.segment_id
    # below the anchor distance the nearest road line, when it is within the reach, still attaches ...
    line_seg, line_d = net.nearest_line(*far)
    assert line_d < within.residual_m
    fallback = net.snap(*far, junction_tol_m=0.0, max_m=within.residual_m - 1.0)
    assert (fallback.segment_id, fallback.residual_m) == (line_seg.segment_id, round(line_d, 1))
    # ... and below both there is no road anchor
    assert net.snap(*far, junction_tol_m=0.0, max_m=line_d - 1.0).segment_id is None


def test_snap_refuses_a_non_point(net):
    with pytest.raises(ValueError):
        net.snap(float("nan"), 23.0)
    with pytest.raises(ValueError):
        net.snap(200.0, 23.0)


def test_near_ties_are_decided_by_the_geodesic_distance(net):
    # a point halfway between two anchors resolves to the truly nearer one (then the lower id): stable
    a, b = net.segments[1001].anchor, net.segments[1036].anchor
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    seg, d = net.nearest_segment(*mid)
    for other in net.segments.values():
        assert geodesic_m(*mid, *other.anchor) >= d - 1e-6
    assert net.nearest_segment(*mid) == (seg, d)


def test_path_rules_and_cache(tmp_path, monkeypatch):
    assert load_network() is load_network()
    copy = tmp_path / "net.json"
    copy.write_text(NETWORK_JSON.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setenv(snap_mod.NETWORK_ENV, str(copy))
    other = load_network()
    assert other.path == copy and other is load_network() and other is not load_network(NETWORK_JSON)
    monkeypatch.setenv(snap_mod.NETWORK_ENV, str(tmp_path / "missing.json"))
    with pytest.raises(FileNotFoundError):
        load_network()
    with pytest.raises(FileNotFoundError):
        load_network(tmp_path / "also-missing.json")


def test_a_malformed_network_is_refused():
    with pytest.raises(ValueError):
        Network.from_document({"segments": [{"segment_id": 1, "road_name": "X Road", "line": [[72.5, 23.0]]}]})
    with pytest.raises(ValueError):
        Network.from_document({"segments": [{"segment_id": True, "road_name": "X Road",
                                              "line": [[72.5, 23.0], [72.6, 23.0]]}]})
    with pytest.raises(ValueError):
        Network.from_document({"segments": []})


def test_a_junction_without_coordinates_is_refused():
    seg = {"segment_id": 1, "road_name": "X Road", "line": [[72.5, 23.0], [72.6, 23.0]]}
    with pytest.raises(ValueError):
        Network.from_document({"segments": [seg], "junctions": [{"junction_id": 1, "name": "X", "lon": None,
                                                                 "lat": 23.0}]})
