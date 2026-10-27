#!/usr/bin/env python3
"""PoC parity for osint_geo (OS-3) — a script, not a test (``test_poc_parity_geo.py`` asserts the same figures).

Resolves the PoC's real signals (read IN PLACE, never copied: plan R13) with :class:`GazetteerResolver` and compares
every geocode with the PoC's own ``events.geo.json`` (same directory as the signals). Prints counts, ids, place
names, methods and numbers only; never a title or a text. Usage::

    PYTHONPATH=src:../osint-common/src python tests/poc_parity.py [SIGNALS_JSON] [--geo EVENTS_GEO_JSON]

Without ``SIGNALS_JSON``, the PoC's ``out/signals.raw.json`` under ``$OSINT_POC_DIR`` (``tests/_poc.py``).

Targets (OS-3 "Done when", as corrected by F-HONEST): 25 geotagged = 15 point/segment/junction
(``gazetteer_exact``) + 1 district (``LGD:AHMEDABAD``, 0.4, the district point) + 9 state-level (``LGD:GUJARAT``,
0.25, no point); Karnavati Club → segment 1045, residual 190.5 ± 5 m, confidence 0.719 ± 0.01, bucket medium; the
Odhav robbery → the Odhav NEIGHBOURHOOD, no junction and no segment; zero India/indira false matches; all 107
resolved in < 2 s.

**Where the PoC was wrong** (F-HONEST OSINT-1 and OSINT-3; :data:`HONEST_DIVERGENCES`): the PoC pinned a bare area
word on a junction named after the area ("Odhav's Rajendra Park Bridge" → Odhav Ring Road Circle, junction 11, at
residual 0; a post naming "Sola" → Sola Cross Roads at 0.988 high; "Motera", "Paldi" likewise), and carried a
neighbourhood, or a landmark more than 900 m from its nearest segment, as that segment (Sabarmati → 1032 at 1.2 km,
Kankaria Lake → 1038 at 2.3 km, Civil Hospital Asarwa → 1043 at 2.1 km). Those rows are reported as honest
divergences with their cause, never as matches; every other row must still match the PoC.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from osint_common.types import RawOsintSignal
from osint_geo.gazetteer import load as load_gazetteer
from osint_geo.resolver import DISTRICT_AHMEDABAD, GazetteerResolver
from osint_geo.snap import load_network

_HERE = str(Path(__file__).resolve().parent)
if _HERE not in sys.path:  # the helper beside this script, however the script is loaded
    sys.path.insert(0, _HERE)
from _poc import POC_SIGNALS  # noqa: E402
CONF_TOL = 0.01
RESIDUAL_TOL = 5.0
TIME_BUDGET_S = 2.0
KARNAVATI = "Karnavati Club (SG Highway)"
ODHAV = "Odhav Ring Road Circle (SP Ring Road)"
#: PoC method → osint_geo method (the PoC's "cap_area" is R28's area fallback)
METHOD_MAP = {"gazetteer_exact": "gazetteer_exact", "gazetteer_fuzzy": "gazetteer_fuzzy", "cap_area": "area_fallback"}
_INDIA = re.compile(r"\bindia\b", re.IGNORECASE)
_INDIRA = re.compile(r"\bindira\b", re.IGNORECASE)


#: The PoC answers F-HONEST corrected: signal id prefix → the cause. A row listed here must differ from the PoC
#: in exactly that way (a junction pin lost, or a segment dropped), and no other row may differ.
HONEST_DIVERGENCES: dict[str, str] = {
    "640debde03": "OSINT-1: 'Odhav' is the neighbourhood, never the Odhav Ring Road Circle pin",
    "1545fe6f58": "OSINT-1: a bare 'Sola' names the area, not Sola Cross Roads (no Sola entry: honestly None)",
    "85be895d61": "OSINT-1: a bare 'Motera' names the area, not one of the two Motera junctions (honestly None)",
    "b7adc0f3f3": "OSINT-1: a bare 'Paldi' is the neighbourhood, not Paldi Cross Roads",
    "9ecb154a8c": "OSINT-1: a bare 'Bopal' is the neighbourhood, not Bopal Junction (Maninagar, also named, now wins)",
    "46f79d69cc": "OSINT-3: a neighbourhood (Sabarmati) is an area, never segment 1032 1.2 km away",
    "793682348a": "OSINT-3: Civil Hospital Asarwa is 2.1 km from segment 1043: not on it",
    "cd21ff9a88": "OSINT-3: Kankaria Lake is 2.3 km from segment 1038: not on it",
}


def _honest(row: dict[str, Any]) -> str | None:
    """The F-HONEST cause of a row's difference, when it is exactly the corrected one."""
    cause = next((c for k, c in HONEST_DIVERGENCES.items() if row["signal_id"].startswith(k)), None)
    if cause is None or row["poc"] is None:
        return None
    poc, mine = row["poc"], row["mine"]
    if poc.get("junction_id") is not None:  # OSINT-1: no junction pin from a bare area word
        return cause if mine is None or (mine["junction_id"] is None and mine["feature_type"] != "junction") else None
    # OSINT-3: the same place, no road anchor
    if mine and mine["toponym"] == poc["toponym"] and mine["segment_id"] is None and mine["residual_m"] is None:
        return cause
    return None


def _kind(g: dict[str, Any] | None) -> str:
    if g is None:
        return "none"
    if g.get("area_scope"):
        return g["area_scope"]
    return "point"


def run(signals_path: Path, geo_path: Path | None = None) -> dict[str, Any]:
    """Resolve the PoC signals and compare them with the PoC's geocodes; returns the whole report as data."""
    geo_path = geo_path or signals_path.parent / "events.geo.json"
    raw = json.loads(signals_path.read_text(encoding="utf-8"))
    poc_events = json.loads(geo_path.read_text(encoding="utf-8")).get("events", [])
    poc_geo = {e["osint_event_id"]: e["geo"] for e in poc_events}

    t0 = time.perf_counter()
    gaz = load_gazetteer()
    t1 = time.perf_counter()
    net = load_network()
    t2 = time.perf_counter()
    resolver = GazetteerResolver(gaz, net)
    signals = [RawOsintSignal.model_validate(r) for r in raw]
    t3 = time.perf_counter()
    geocodes = {s.signal_id: resolver.resolve(s) for s in signals}
    t4 = time.perf_counter()

    rows: list[dict[str, Any]] = []
    for s in signals:
        g = geocodes[s.signal_id]
        mine = g.model_dump(mode="json") if g is not None else None
        poc = poc_geo.get(s.signal_id)
        row: dict[str, Any] = {"signal_id": s.signal_id, "source": s.source, "poc": poc, "mine": mine, "diffs": []}
        if poc is None and mine is None:
            row["status"] = "none-both"
        elif poc is None or mine is None:
            row["status"] = "MISMATCH"
            row["diffs"].append("geotagged in one only")
        else:
            row["status"] = "match"
            if poc["toponym"] != mine["toponym"]:
                row["diffs"].append(f"toponym {poc['toponym']!r} -> {mine['toponym']!r}")
            if METHOD_MAP.get(poc["method"], poc["method"]) != mine["method"]:
                row["diffs"].append(f"method {poc['method']} -> {mine['method']}")
            if (poc.get("segment_id"), poc.get("junction_id")) != (mine["segment_id"], mine["junction_id"]):
                if not mine["area_level"]:
                    row["diffs"].append(
                        f"anchor seg {poc.get('segment_id')}/jct {poc.get('junction_id')} -> "
                        f"seg {mine['segment_id']}/jct {mine['junction_id']}"
                    )
            dc = round(mine["confidence"] - poc["geocode_confidence"], 3)
            row["dconf"] = dc
            if abs(dc) > CONF_TOL:
                row["diffs"].append(f"confidence {poc['geocode_confidence']} -> {mine['confidence']}")
            if row["diffs"]:
                row["status"] = "MISMATCH"
        if row["status"] == "MISMATCH" and (cause := _honest(row)) is not None:
            row["status"] = "honest-divergence"
            row["cause"] = cause
        rows.append(row)

    def find(toponym: str, *, source: str = "google_news_rss") -> dict[str, Any] | None:
        for r in rows:
            m = r["mine"]
            if m and m["toponym"] == toponym and r["source"] == source:
                return r
        return None

    karn = find(KARNAVATI)
    odhav = next((r for r in rows if r["signal_id"].startswith("640debde03")), None)
    by_id = {s.signal_id: s for s in signals}
    explain = {
        name: resolver.explain(by_id[row["signal_id"]]) for name, row in (("karnavati", karn), ("odhav", odhav)) if row
    }
    karn_line_m = (
        net.line_distance_m(karn["mine"]["lon"], karn["mine"]["lat"], karn["mine"]["segment_id"]) if karn else None
    )
    geotagged = [r for r in rows if r["mine"] is not None]
    points = [r for r in geotagged if _kind(r["mine"]) == "point"]
    districts = [r for r in geotagged if _kind(r["mine"]) == "district"]
    states = [r for r in geotagged if _kind(r["mine"]) == "state"]
    text_of = {s.signal_id: f"{s.title} {s.text} {' '.join(s.raw_geo_hint.place_names)}" for s in signals}
    india_signals = [sid for sid, t in text_of.items() if _INDIA.search(t)]
    indira_false = [
        r["signal_id"]
        for r in geotagged
        if "indira" in (r["mine"]["toponym"] or "").lower() and not _INDIRA.search(text_of[r["signal_id"]])
    ]
    fuzzy = [r["signal_id"] for r in geotagged if r["mine"]["method"] == "gazetteer_fuzzy"]

    checks = {
        "signals_107": len(signals) == 107,
        "geotagged_25": len(geotagged) == 25,
        "points_15_gazetteer_exact": len(points) == 15
        and all(r["mine"]["method"] == "gazetteer_exact" for r in points),
        "district_1": len(districts) == 1
        and all(
            r["mine"]["confidence"] == 0.4
            and (r["mine"]["lon"], r["mine"]["lat"]) == (DISTRICT_AHMEDABAD.lon, DISTRICT_AHMEDABAD.lat)
            and r["mine"]["segment_id"] is None and r["mine"]["junction_id"] is None
            for r in districts
        ),
        "state_9_no_point": len(states) == 9
        and all(
            r["mine"]["confidence"] == 0.25 and r["mine"]["lon"] is None and r["mine"]["lat"] is None for r in states
        ),
        "karnavati": bool(
            karn
            and karn["mine"]["segment_id"] == 1045
            and abs(karn["mine"]["residual_m"] - 190.5) <= RESIDUAL_TOL
            and abs(karn["mine"]["confidence"] - 0.719) <= CONF_TOL
            and karn["mine"]["bucket"] == "medium"
        ),
        "odhav": bool(
            odhav and odhav["mine"] and odhav["mine"]["toponym"] == "Odhav"
            and odhav["mine"]["feature_type"] == "neighbourhood"
            and odhav["mine"]["junction_id"] is None and odhav["mine"]["segment_id"] is None
        ),
        "honest_divergences_8": sum(r["status"] == "honest-divergence" for r in rows) == len(HONEST_DIVERGENCES),
        "zero_india_indira": not indira_false,
        "per_signal_method_and_confidence": all(r["status"] != "MISMATCH" for r in rows),
        "under_2s": (t4 - t3) < TIME_BUDGET_S,
    }
    return {
        "paths": {"signals": str(signals_path), "poc_geo": str(geo_path), "gazetteer": str(gaz.path),
                  "network": str(net.path)},
        "gazetteer": {"entries": len(gaz.entries), "generated_at": gaz.meta.get("generated_at"),
                      "licence": gaz.meta.get("licence")},
        "network": {"segments": len(net.segments), "junctions": len(net.junctions)},
        "timing_ms": {"load_gazetteer": (t1 - t0) * 1e3, "load_network": (t2 - t1) * 1e3,
                      "validate_signals": (t3 - t2) * 1e3, "resolve_all": (t4 - t3) * 1e3},
        "counts": {"signals": len(signals), "geotagged": len(geotagged), "points": len(points),
                   "district": len(districts), "state": len(states), "poc_geotagged": len(poc_geo),
                   "india_mentions": len(india_signals), "indira_false_matches": len(indira_false),
                   "fuzzy": len(fuzzy)},
        "karnavati": karn,
        "karnavati_line_m": karn_line_m,
        "odhav": odhav,
        "explain": explain,
        "anchors_moved": anchors_moved(signals_path),
        "rows": rows,
        "checks": checks,
        "passed": all(checks.values()),
    }


#: Why a per-signal figure may differ from the PoC (each difference printed is matched to one of these).
CAUSES = {
    "anchor": (
        "snap anchor: the PoC measured a landmark's residual to the vertex nearest its road's vertex mean; osint_geo "
        "measures it (WGS84 geodesic, pyproj) to the segment's ST_PointOnSurface anchor, the point the oracle "
        "places the segment at"
    ),
    "ctx": (
        "embedding-context term left off R (the Embedder is OS-4's): the PoC added a constant 0.10 x 0.5 to every "
        "reading, so a relative margin (R_top - R_2) / R_top shifts slightly where two different places compete"
    ),
}


def anchors_moved(signals_path: Path) -> str:
    """How many road points differ between the PoC gazetteer (read in place, if present) and the network anchors."""
    poc = signals_path.parent.parent / "ahmedabad_gazetteer.json"
    if not poc.is_file():
        return "the PoC gazetteer is not present to compare"
    old = {e["segment_id"]: (e["lon"], e["lat"]) for e in json.loads(poc.read_text(encoding="utf-8"))["entries"]
           if e["feature_type"] == "road"}
    net = load_network()
    moved = sum(1 for sid, seg in net.segments.items() if old.get(sid) != (round(seg.anchor[0], 7),
                                                                            round(seg.anchor[1], 7)))
    return f"the two points differ for {moved} of the {len(net.segments)} segments"


def _fmt_geo(g: dict[str, Any] | None, *, poc: bool) -> str:
    if g is None:
        return "None"
    conf = g["geocode_confidence"] if poc else g["confidence"]
    anchor = f"seg {g.get('segment_id')}" if g.get("segment_id") else (
        f"jct {g.get('junction_id')}" if g.get("junction_id") else "-")
    res = g.get("residual_m")
    point = "no point" if g.get("lat") is None else "point"
    return f"{g['toponym']} | {g['method']} | {conf} | {anchor} | res {res} | {point}"


def _cause(row: dict[str, Any]) -> str:
    poc, mine = row["poc"], row["mine"]
    if poc is None or mine is None:
        return ""
    if mine["area_scope"] == "state":
        return "R28: a state-level alert no longer carries the city centre's point (lon/lat None)"
    out = []
    if poc.get("residual_m") is not None and mine["residual_m"] is not None and abs(poc["residual_m"] -
                                                                                   mine["residual_m"]) > 0.05:
        out.append(f"residual {poc['residual_m']} -> {mine['residual_m']} m ({CAUSES['anchor'].split(':')[0]})")
    if row.get("dconf") and mine["alternatives"]:
        out.append("margin over a competing place moves (embedding-context term left off)")
    return "; ".join(out)


def print_report(rep: dict[str, Any]) -> None:
    p = print
    p("OS-3 osint-geo - PoC parity (real PoC signals read in place; no title or text printed)")
    p(f"signals:    {rep['paths']['signals']}")
    p(f"PoC geo:    {rep['paths']['poc_geo']}")
    p(f"gazetteer:  {rep['paths']['gazetteer']} ({rep['gazetteer']['entries']} entries, generated_at "
      f"{rep['gazetteer']['generated_at']}, licence {rep['gazetteer']['licence']})")
    p(f"network:    {rep['paths']['network']} ({rep['network']['segments']} segments, "
      f"{rep['network']['junctions']} junctions)")
    t = rep["timing_ms"]
    p("")
    p("[timing]")
    p(f"  load gazetteer {t['load_gazetteer']:.1f} ms, load network {t['load_network']:.1f} ms, validate "
      f"{rep['counts']['signals']} signals {t['validate_signals']:.1f} ms")
    p(f"  resolve all {rep['counts']['signals']} signals: {t['resolve_all']:.1f} ms "
      f"(budget {TIME_BUDGET_S * 1e3:.0f} ms)")
    c = rep["counts"]
    p("")
    p("[counts]")
    p(f"  signals {c['signals']}; geotagged {c['geotagged']} (PoC {c['poc_geotagged']})")
    p(f"    point/segment/junction (gazetteer_exact): {c['points']}")
    p(f"    district (LGD:AHMEDABAD, area_fallback, 0.4, the district point): {c['district']}")
    p(f"    state (LGD:GUJARAT, area_fallback, 0.25, lon/lat None): {c['state']}")
    p(f"  fuzzy geocodes: {c['fuzzy']}")
    p("")
    p("[headline cases]")
    k = rep["karnavati"]
    if k:
        m = k["mine"]
        p(f"  {KARNAVATI}: segment {m['segment_id']} ({m['snapped_to']}), residual {m['residual_m']} m "
          f"(target 190.5 +/- {RESIDUAL_TOL:g}), confidence {m['confidence']} (target 0.719 +/- {CONF_TOL}), "
          f"bucket {m['bucket']} (target medium)  [signal {k['signal_id'][:12]}]")
        p(f"    the residual is to the segment's anchor (ST_PointOnSurface); the road line itself passes "
          f"{rep['karnavati_line_m']:.1f} m from the landmark")
    else:
        p(f"  {KARNAVATI}: NOT FOUND")
    o = rep["odhav"]
    if o:
        m = o["mine"]
        p(f"  Odhav robbery: {m['toponym']} ({m['feature_type']}), junction {m['junction_id']}, segment "
          f"{m['segment_id']} (target: the Odhav neighbourhood, no junction, no segment; F-HONEST OSINT-1), "
          f"confidence {m['confidence']}, bucket {m['bucket']}  [signal {o['signal_id'][:12]}]")
    else:
        p("  Odhav robbery: NOT FOUND")
    p("[honest divergences from the PoC (F-HONEST)]")
    for r in rep["rows"]:
        if r["status"] == "honest-divergence":
            p(f"  {r['signal_id'][:10]}: {r['cause']}")
    for name, ex in rep["explain"].items():
        forms = ", ".join(f"{m['form']!r} -> gaz {m['gaz_ids']}" for m in ex["mentions"])
        top = ex["readings"][:3]
        tie = len(top) > 1 and top[0]["gaz_id"] == top[1]["gaz_id"] and top[0]["r"] == top[1]["r"]
        why = ("the top place is mentioned more than once, so its readings tie (margin 0), as in the PoC" if tie
               else "the best reading beats the runner-up (margin > 0)")
        p(f"  why ({name}): mentions [{forms}]; locality {ex['locality']}; best readings "
          + ", ".join(f"{r['canonical_name']} R={r['r']}" for r in top) + f" -> {why}")
    p("")
    p("[per geotagged signal: PoC events.geo.json  =>  osint_geo]")
    for r in rep["rows"]:
        if r["poc"] is None and r["mine"] is None:
            continue
        d = f" dconf {r['dconf']:+.3f}" if "dconf" in r else ""
        p(f"  {r['signal_id'][:12]} {r['source']:<15} {r['status']}{d}")
        p(f"      PoC : {_fmt_geo(r['poc'], poc=True)}")
        p(f"      mine: {_fmt_geo(r['mine'], poc=False)}")
        cause = _cause(r)
        if cause:
            p(f"      cause: {cause}")
        for diff in r["diffs"]:
            p(f"      DIFF: {diff}")
    none_both = sum(1 for r in rep["rows"] if r["status"] == "none-both")
    p(f"  ({none_both} signals are None in both: no toponym and no area code, the honest None)")
    p("")
    p("[differences and their causes]")
    p(f"  - {CAUSES['anchor']}; {rep['anchors_moved']}")
    p(f"  - {CAUSES['ctx']}")
    p("  - R28: the 9 state-level SACHET nowcasts carry no point (the PoC put them on the city centre), "
      "method cap_area -> area_fallback, bucket 'area' -> 'low'")
    p("  every per-signal confidence stays within +/- 0.01 of the PoC and every method, toponym and road anchor "
      "is the PoC's" if rep["checks"]["per_signal_method_and_confidence"] else "  SEE DIFF LINES ABOVE")
    p("")
    p("[India / indira]")
    p(f"  signals whose text says 'India': {c['india_mentions']}; geocodes on an Indira-named place without "
      f"'indira' in the text: {c['indira_false_matches']}")
    p("")
    p("[checks]")
    for name, ok in rep["checks"].items():
        p(f"  {'PASS' if ok else 'FAIL'}  {name}")
    p(f"RESULT: {'PASS' if rep['passed'] else 'FAIL'}")
    p("MACHINE_RESULT=" + json.dumps({
        "passed": rep["passed"],
        "counts": rep["counts"],
        "karnavati": rep["karnavati"]["mine"] if rep["karnavati"] else None,
        "odhav": rep["odhav"]["mine"] if rep["odhav"] else None,
        "resolve_all_ms": round(rep["timing_ms"]["resolve_all"], 1),
        "checks": rep["checks"],
    }, ensure_ascii=False, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="osint_geo PoC parity (the PoC signals read in place)")
    ap.add_argument("signals", nargs="?", type=Path, default=POC_SIGNALS)
    ap.add_argument("--geo", type=Path, default=None, help="the PoC events.geo.json (default: beside the signals)")
    args = ap.parse_args(argv)
    rep = run(args.signals, args.geo)
    print_report(rep)
    return 0 if rep["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
