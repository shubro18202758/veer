#!/usr/bin/env python3
"""PoC parity for osint_analysis (OS-4) — a script, not a test (``test_poc_parity.py`` asserts the same figures).

Fusion is isolated from the resolver: a REPLAY resolver hands ``run_pipeline`` the PoC's own geocodes from
``events.geo.json``, so every difference below is the analysis stage's, never the geocoder's. The PoC's
``cap_area`` geocodes are mapped by toponym at their real precision (plan R28): "Ahmedabad (district)" → area
scope ``district`` (the district point, confidence 0.4); "Gujarat (state)" → area scope ``state`` (no point,
confidence 0.25).

The real PoC outputs are READ IN PLACE and never copied (plan R13). Only counts, ids (sha1 prefixes), classes,
toponyms (places) and numbers are printed: never a title, a text, a URL, a publisher or anything of the live
capture but a live event's URN kind, status and route length (its label carries a masked registration mark and
its metadata an officer: neither is read).

Usage (from services/osint-analysis)::

    PYTHONPATH=src:../osint-common/src python tests/poc_parity.py \
        --signals <PoC out>/signals.raw.json --geo <PoC out>/events.geo.json \
        --live <PoC out>/raw/sandbox_city_entities.json [--fused <PoC out>/events.fused.json]

Exit status 0 when every check passes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

_T_IMPORT = time.perf_counter()
from osint_common.types import Geocode, LiveEventRef, LiveStateSnapshot, RawOsintSignal  # noqa: E402

from osint_analysis.pipeline import run_pipeline  # noqa: E402
from osint_analysis.classify import CAP_SOURCES, CAP_SUBTYPES  # noqa: E402

IMPORT_SEC = time.perf_counter() - _T_IMPORT


def _default_poc_out() -> Path:
    """``$OSINT_POC_DIR``, else ``.veer-orchestration/osint/prototype/out`` next to an ancestor of this file."""
    env = os.environ.get("OSINT_POC_DIR")
    if env:
        return Path(env)
    rel = Path(".veer-orchestration", "osint", "prototype", "out")
    for parent in Path(__file__).resolve().parents:
        if (parent / rel / "signals.raw.json").is_file():
            return parent / rel
    return Path("out")


POC_OUT = _default_poc_out()

#: The PoC's geocode vocabulary → the X18 Geocode vocabulary.
_FEATURE = {"landmark": "landmark", "junction": "junction", "road": "road", "neighbourhood": "neighbourhood",
            "admin_area": "admin", "poi": "poi"}
_METHOD = {"gazetteer_exact": "gazetteer_exact", "gazetteer_fuzzy": "gazetteer_fuzzy", "gdelt_actiongeo": "point"}
_BUCKET = {"high": "high", "medium": "medium", "low": "low", "area": "low"}

#: The figures OS-4's "Done when" pins (plan R23, R28).
EXPECTED = {
    "signals": 107,
    "pii_redactions": 60,
    "geotagged": 27,
    "incident_geotagged": 15,
    "fused": 14,
    "surfaced": 3,
    "correlated": 1,
    "cross_type_corroborated": 0,
    "social_held": 7,
    "outside_city_held": 1,
    "attached_to_live": 0,
}


def poc_geocode(signal_id: str, geo: dict[str, Any]) -> Geocode:
    """One PoC geocode (``events.geo.json`` ``geo``) as an X18 Geocode, area levels at their real precision."""
    if geo.get("method") == "cap_area":
        toponym = str(geo.get("toponym") or "")
        if toponym.startswith("Ahmedabad"):
            return Geocode(
                signal_id=signal_id, toponym=toponym, feature_type="admin", lon=geo["lon"], lat=geo["lat"],
                method="area_fallback", confidence=min(0.4, float(geo["geocode_confidence"])), bucket="low",
                area_level=True, area_scope="district",
            )
        return Geocode(
            signal_id=signal_id, toponym=toponym or "Gujarat (state)", feature_type="admin", lon=None, lat=None,
            method="area_fallback", confidence=min(0.25, float(geo["geocode_confidence"])), bucket="low",
            area_level=True, area_scope="state",
        )
    return Geocode(
        signal_id=signal_id,
        toponym=geo.get("toponym"),
        feature_type=_FEATURE.get(geo.get("feature_type") or ""),
        lon=geo["lon"],
        lat=geo["lat"],
        segment_id=geo.get("segment_id"),
        junction_id=geo.get("junction_id"),
        snapped_to=geo.get("snapped_to_segment"),
        method=_METHOD.get(geo.get("method") or "", "gazetteer_exact"),
        residual_m=geo.get("residual_m"),
        confidence=float(geo["geocode_confidence"]),
        bucket=_BUCKET.get(geo.get("bucket") or "", "low"),
        area_level=False,
        area_scope=None,
        alternatives=[str(a)[:200] for a in (geo.get("alternatives") or [])][:16],
    )


class ReplayResolver:
    """Replays the PoC's own geocodes (an honest ``None`` for every signal the PoC did not geotag)."""

    def __init__(self, geo_events: list[dict[str, Any]]) -> None:
        self._by_id = {e["osint_event_id"]: poc_geocode(e["osint_event_id"], e["geo"]) for e in geo_events}

    def resolve(self, signal: RawOsintSignal) -> Geocode | None:
        return self._by_id.get(signal.signal_id)


def live_from_capture(path: Path) -> LiveStateSnapshot:
    """The sandbox ``/city/entities`` capture as a LiveStateSnapshot: URN, kind, status, point and route segments
    of each event, nothing else (no label, title or metadata is read)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    events = []
    for e in data.get("entities", []):
        if e.get("kind") != "event":
            continue
        props = e.get("props") or {}
        segs: set[int] = set()
        for spine in props.get("route_spines") or []:
            segs.update(int(s) for s in (spine.get("segment_ids") or []) if isinstance(s, int) and s > 0)
        for link in e.get("links") or []:
            if isinstance(link, str) and link.startswith("segment:") and link[8:].isdigit():
                segs.add(int(link[8:]))
        events.append(
            LiveEventRef(
                urn=e["urn"],
                event_kind=props.get("event_kind"),
                status=props.get("status") or e.get("state"),
                lon=e.get("lon"),
                lat=e.get("lat"),
                segment_ids=sorted(segs),
            )
        )
    return LiveStateSnapshot(as_of=data["as_of"], live_events=events)


def _poc_situations(fused_path: Path, raw: list[dict[str, Any]]) -> list[tuple[str, frozenset[str], dict]]:
    """The PoC's fused situations as member signal-id sets (its sources carry no signal id: matched by URL)."""
    by_url: dict[str, list[str]] = {}
    for s in raw:
        if s.get("url"):
            by_url.setdefault(s["url"], []).append(s["signal_id"])
    out = []
    for f in json.loads(fused_path.read_text(encoding="utf-8"))["fused_events"]:
        ids = set()
        for src in f["sources"]:
            hits = by_url.get(src.get("url") or "", [])
            if len(hits) == 1:
                ids.add(hits[0])
        out.append((f["fused_event_id"], frozenset(ids), f))
    return out


#: Fields compared one by one between a PoC situation and the one reproducing it.
_FIELDS = (
    "event_class", "correlated_classes", "subtype", "veer_event_kind", "veer_incident_kind", "toponym", "segment_id",
    "junction_id", "geocode_confidence", "area_level", "credibility", "verification_state", "source_count",
    "source_tiers", "independent_publishers", "cross_type_corroborated", "is_event", "held_reason", "rep_lonlat",
    "attach_novel",
)
#: Intended differences: migration 021 lets the robbery row carry incident kind ``robbery`` (the PoC: ``other``).
_INTENDED = {
    ("veer_incident_kind", "other", "robbery"),
    # F-HONEST OSINT-3: a neighbourhood is an area (Sabarmati was carried as segment 1032, 1.2 km away), and a
    # landmark more than 900 m from its snapped segment is not on it (Civil Hospital Asarwa 1043 at 2.1 km,
    # Kankaria Lake 1038 at 2.3 km): the PoC's segments were never in the reports
    ("segment_id", 1032, None),
    ("area_level", False, True),
    ("segment_id", 1043, None),
    ("segment_id", 1038, None),
}


def _field_diffs(poc: dict[str, Any], r) -> list[tuple[str, Any, Any]]:
    mine = {f: getattr(r, f, None) for f in _FIELDS}
    mine["rep_lonlat"] = None if r.rep_lon is None else [round(r.rep_lon, 6), round(r.rep_lat, 6)]
    mine["attach_novel"] = r.attach.novel
    theirs = {f: poc.get(f) for f in _FIELDS}
    rep = poc.get("rep_lonlat")
    theirs["rep_lonlat"] = None if not rep else [round(rep[0], 6), round(rep[1], 6)]
    theirs["attach_novel"] = bool((poc.get("attach") or {}).get("novel"))
    return [(f, theirs[f], mine[f]) for f in _FIELDS if theirs[f] != mine[f]]


def _fmt(r) -> str:
    att = "novel" if r.attach.novel else f"corroborates {r.attach.corroborates_live_urn.split(':', 1)[0]}"
    return (
        f"class={r.event_class} subtype={r.subtype} kind={r.veer_event_kind}/{r.veer_incident_kind} "
        f"classes={r.correlated_classes} toponym={r.toponym!r} seg={r.segment_id} jct={r.junction_id} "
        f"area_level={r.area_level} point={'yes' if r.rep_lon is not None else 'no'} geoconf={r.geocode_confidence} "
        f"cred={r.credibility} state={r.verification_state} sources={r.source_count} "
        f"publishers={r.independent_publishers} tiers={r.source_tiers} attach={att} flags={len(r.second_order)}"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--signals", type=Path, default=POC_OUT / "signals.raw.json")
    ap.add_argument("--geo", type=Path, default=POC_OUT / "events.geo.json")
    ap.add_argument("--live", type=Path, default=POC_OUT / "raw" / "sandbox_city_entities.json")
    ap.add_argument("--fused", type=Path, default=None, help="the PoC's events.fused.json (default: next to --geo)")
    args = ap.parse_args(argv)
    fused_path = args.fused or args.geo.with_name("events.fused.json")

    raw = json.loads(args.signals.read_text(encoding="utf-8"))
    signals = [RawOsintSignal.model_validate(r) for r in raw]
    geo_events = json.loads(args.geo.read_text(encoding="utf-8"))["events"]
    resolver = ReplayResolver(geo_events)
    live = live_from_capture(args.live)

    timings = []
    result = None
    for _ in range(3):
        t0 = time.perf_counter()
        result = run_pipeline(signals, resolver=resolver, live=live)
        timings.append(time.perf_counter() - t0)
    assert result is not None
    again = run_pipeline(list(reversed(signals)), resolver=resolver, live=live)
    deterministic = again.model_dump_json() == result.model_dump_json()

    c = result.counts
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))

    print("# osint_analysis PoC parity (OS-4) — PoC outputs read in place, nothing copied")
    print(f"# signals: {args.signals}")
    print(f"# geocodes replayed from: {args.geo}  (fusion isolated from the resolver)")
    print(f"# live state: {args.live}")
    print()
    print("[counts] " + " ".join(f"{k}={v}" for k, v in c.model_dump().items()))
    for key, want in EXPECTED.items():
        got = getattr(c, key)
        check(f"counts.{key} == {want}", got == want, f"got {got}")

    geos = [g for g in result.geocodes.values() if g is not None]
    scope = Counter("state" if g.area_scope == "state" else "district" if g.area_scope == "district" else "point"
                    for g in geos)
    print(f"[geocodes] {len(geos)} geotagged: {scope['point']} point or segment + {scope['district']} district "
          f"+ {scope['state']} state-level")
    check("geotagged = 17 point/segment + 1 district + 9 state-level",
          (scope["point"], scope["district"], scope["state"]) == (17, 1, 9), str(dict(scope)))
    check("state-level geocodes carry no point", all(g.lon is None for g in geos if g.area_scope == "state"))

    print(f"[live] {len(live.live_events)} live event(s): "
          + ", ".join(f"{e.urn.split(':', 1)[0]} {e.event_kind} {e.status} route={len(e.segment_ids)} segs"
                      for e in live.live_events) + f"; as_of {live.as_of.isoformat()}")

    surfaced = [r for r in result.resolved if r.is_event]
    print(f"\n[surfaced] {len(surfaced)}")
    for r in surfaced:
        print(f"  {r.fused_event_id[:12]} {_fmt(r)}")
        print(f"      label={r.label!r}")
    by_class = {r.event_class: r for r in surfaced}

    w = by_class.get("weather_hazard")
    check(
        "weather_hazard/hazard, district area (Ahmedabad), 0.95, OFFICIAL-VERIFIED, 1 source",
        w is not None and w.veer_event_kind == "hazard" and w.area_level and w.rep_lon is not None
        and (w.toponym or "").startswith("Ahmedabad") and w.credibility == 0.95
        and w.verification_state == "OFFICIAL-VERIFIED" and w.source_count == 1,
        _fmt(w) if w else "missing",
    )
    a = by_class.get("road_accident")
    check(
        "road_accident affray+collision, segment 1045, 0.65, NEWS-REPORTED, 4 sources, 2 independent publishers",
        a is not None and a.subtype == "affray+collision"
        and a.correlated_classes == ["road_accident", "public_conflict"]
        and a.segment_id == 1045 and a.credibility == 0.65 and a.verification_state == "NEWS-REPORTED"
        and a.source_count == 4 and a.independent_publishers == 2,
        _fmt(a) if a else "missing",
    )
    rc = by_class.get("reported_crime")
    check(
        "reported_crime daylight_robbery at junction 11, credibility 0.60",
        rc is not None and rc.subtype == "daylight_robbery" and rc.junction_id == 11 and rc.credibility == 0.6,
        _fmt(rc) if rc else "missing",
    )
    check("all three surfaced are novel against the sandbox capture", all(r.attach.novel for r in surfaced))

    held = [r for r in result.resolved if not r.is_event]
    reasons = sorted(Counter(r.held_reason for r in held).items())
    print(f"\n[held] {len(held)}: " + ", ".join(f"{k} x{v}" for k, v in reasons))
    for r in held:
        print(f"  {r.fused_event_id[:12]} held_reason={r.held_reason!r} {_fmt(r)}")
    outside = [r for r in held if r.held_reason == "state-level area: not located in the city"]
    check(
        "1 outside-city held: the 9 state-wide nowcasts, held_reason 'state-level area: not located in the city'",
        len(outside) == 1 and outside[0].source_count == 9 and outside[0].rep_lon is None,
        f"{len(outside)} situation(s), sources {[r.source_count for r in outside]}",
    )

    kinds_out = [cl.veer_event_kind for cl in result.classifications.values()]
    kinds_out += [r.veer_event_kind for r in result.resolved]
    n_crime = sum(1 for k in kinds_out if k == "crime_incident")
    check("zero crime_incident (classifications and situations)", n_crime == 0, f"{n_crime}")

    geo_by_id = {e["osint_event_id"]: e for e in geo_events}
    def _same_subtype(sid: str, poc_subtype: str | None) -> bool:
        mine_sub = result.classifications[sid].subtype
        if mine_sub == poc_subtype:
            return True
        # F-HONEST OSINT-7 (intended): the PoC called every non-flood CAP alert "storm"; Veer names the alert's own
        # event ("rain", "thunderstorm", ...) or "weather_advisory"
        cap_subs = {sub for sub, _terms in CAP_SUBTYPES} | {"weather_advisory"}
        return poc_subtype == "storm" and by_sid[sid].source in CAP_SOURCES and mine_sub in cap_subs

    by_sid = {s.signal_id: s for s in signals}
    same = sum(
        1 for sid, e in geo_by_id.items()
        if result.classifications[sid].event_class == e["event_class"] and _same_subtype(sid, e["subtype"])
    )
    print(f"\n[classify] {same}/{len(geo_by_id)} geotagged signals classified exactly as the PoC (class and subtype)")
    check("per-signal class and subtype equal the PoC's on all 27 geotagged signals", same == len(geo_by_id) == 27)

    if fused_path.is_file():
        poc = _poc_situations(fused_path, raw)
        mine = {r.fused_event_id: frozenset(r.member_signal_ids) for r in result.resolved}
        by_members = {frozenset(r.member_signal_ids): r for r in result.resolved}
        exact, split, other = 0, [], []
        unintended: list[str] = []
        intended: list[str] = []
        for fid, ids, f in poc:
            if ids in mine.values():
                exact += 1
                for field, theirs, ours in _field_diffs(f, by_members[ids]):
                    line = f"{fid[:12]} {field}: PoC {theirs!r} -> {ours!r}"
                    (intended if (field, theirs, ours) in _INTENDED else unintended).append(line)
                continue
            parts = [m for m in mine.values() if m & ids]
            if parts and frozenset().union(*parts) == ids:
                split.append((fid, f, sorted(len(p) for p in parts)))
            else:
                other.append(fid)
        print(f"[PoC situations] {len(poc)} in the PoC: {exact} reproduced exactly (same member reports), "
              f"{len(split)} split, {len(other)} otherwise different")
        for fid, f, sizes in split:
            print(f"  split: PoC {fid[:12]} ({f['event_class']}, {f['source_count']} sources) -> {len(sizes)} "
                  f"situations of {sizes} sources")
        check("12 PoC situations reproduced exactly; the 10-alert SACHET one split into 1 district + 9 state-level",
              exact == 12 and len(split) == 1 and split[0][2] == [1, 9] and not other,
              f"exact {exact}, split {[s[2] for s in split]}, other {len(other)}")
        print(f"[field by field] {len(_FIELDS)} fields on the {exact} reproduced situations: "
              f"{len(unintended)} unintended difference(s), {len(intended)} intended")
        for line in intended:
            print(f"  intended: {line}")
        for line in unintended:
            print(f"  DIFF: {line}")
        check("the reproduced situations agree with the PoC field by field (bar the intended differences)",
              not unintended, f"{len(unintended)} unintended")

    print(f"\n[timing] run_pipeline on {len(signals)} signals, no embedder: "
          + ", ".join(f"{t * 1000:.1f} ms" for t in timings) + f" (package import {IMPORT_SEC * 1000:.0f} ms, once)")
    check("run_pipeline < 1 s on the 107 PoC signals without an embedder", max(timings) < 1.0,
          f"max {max(timings) * 1000:.1f} ms")
    check("deterministic: reversed input gives the identical result", deterministic)

    print("\n[deviations from the PoC, with their cause]")
    print("  - fused 14 (PoC 13): the PoC put its 9 Gujarat-wide SACHET nowcasts on the city centre and merged them")
    print("    into the Ahmedabad district alert; under plan R28 a state-level area blocks only with state-level")
    print("    areas, so the district alert is one surfaced situation of 1 source (PoC: 10) and the 9 nowcasts one")
    print("    held 'outside the city' situation.")
    print("  - the Odhav robbery's veer_incident_kind is 'robbery' (PoC 'other'): migration 021 added robbery,")
    print("    road_rage and public_disorder to traffic.incidents for exactly these lexicon rows.")
    print("  - fused_event_id follows the C-T identity rule sha1('anchor:' + earliest member signal_id); the PoC")
    print("    hashed all member ids, so its ids change whenever a member is added.")
    print("  - F-HONEST OSINT-3: a neighbourhood situation is area-level with no segment (Sabarmati, PoC segment")
    print("    1032 at 1.2 km), and a landmark beyond 900 m of its snapped segment keeps no segment (Civil Hospital")
    print("    Asarwa 1043, Kankaria Lake 1038): the PoC carried segments its reports never named.")
    print("  - otherwise none: the 12 other PoC situations keep their member reports and every compared field")
    print("    (classes, subtype, kinds, place, segment/junction, confidence, credibility, verification state,")
    print("    tiers, publishers, surfacing, held reason, attach) — see [field by field] above.")
    print("  - rules stricter than the PoC's, none of which moves a PoC figure here: keywords match whole words")
    print("    (regular inflections, the derived forms the substring test caught, a stem list, the month and")
    print("    'lightning strike' context rules) instead of substrings; poster handles and the Reddit trailer are")
    print("    stripped before any text is classified, tokenised or embedded; a district alert joins at most one")
    print("    point cluster and never anchors a point situation's id; the Stage-1 time bound reads report times;")
    print("    a Stage-2 situation holds at most one cluster per class; attach corroborates only an active")
    print("    'event:' of a compatible kind (the capture's one live event is a pursuit in planning) and only for")
    print("    a surfaced situation; posts of one social community count as one source; news and social source")
    print("    URLs are withheld (None).")

    print("\n[checks]")
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))
    passed = all(ok for _, ok, _ in checks)
    print("PARITY " + ("PASS" if passed else "FAIL") + f" ({sum(ok for _, ok, _ in checks)}/{len(checks)} checks)")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
