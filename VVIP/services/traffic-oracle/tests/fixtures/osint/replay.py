"""A REPLAY pipeline built from the PoC's own outputs (OS-5's store parity, ``parity_store.py``).

It reproduces the PoC's fused output AS IT IS (``events.fused.json``, with the per-signal geocodes of
``events.geo.json``) for whichever PoC signals it is given, so the oracle's store, surfaces and
promotion can be checked against the PoC's 3 surfaced situations without OS-3 / OS-4.  The PoC files
are READ IN PLACE, never copied (plan R13).  Only the shapes are adapted to the canonical X18 models,
every step listed in :data:`ADAPTER_STEPS` (nothing defaulted silently).  Fused ids gain the run
prefix (``test-<uuid>-`` + the first 22 hex of the PoC id) so the rows can be found and deleted.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from osint_common import kinds
from osint_common.types import (
    AttachResult,
    Geocode,
    PipelineCounts,
    PipelineResult,
    RawOsintSignal,
    ResolvedEvent,
    SourceRef,
)

__all__ = ["ADAPTER_STEPS", "POC_OUT", "PocReplay"]

POC_OUT = Path("/home/sandy050405/argus/veer/.veer-orchestration/osint/prototype/out")

ADAPTER_STEPS: tuple[str, ...] = (
    "fused_event_id <- '<run prefix>-' + the PoC id's first 22 hex (rows findable and deletable)",
    "member signals <- the PoC sources matched to signals.raw.json by url; only the members given",
    "label <- '<Class label> . <toponym | Ahmedabad district>' (the PoC wrote none; OS-4's format)",
    "summary <- the primary member's redacted title (<= 200)",
    "window_start / window_end <- min / max published_at of the members",
    "sources[].url <- None for news and social tiers (the oracle withholds them anyway)",
    "sources[].role <- the first source primary, the rest corroborating",
    "attach <- AttachResult(novel) as the PoC recorded it; second_order <- []",
    "geocode.method cap_area -> area_fallback; feature_type admin_area -> admin; bucket area -> low",
    "geocode area_scope <- 'state' for '... (state)' (no point), 'district' for '... (district)'",
)

_METHODS = {"cap_area": "area_fallback"}
_FEATURES = {"admin_area": "admin"}
_BUCKETS = {"area": "low"}


def _geocode(signal_id: str, geo: dict[str, Any]) -> Geocode:
    toponym = geo.get("toponym")
    scope = None
    if geo.get("area_level"):
        scope = "state" if "(state)" in str(toponym) else "district"
    point = scope != "state"
    conf = float(geo.get("geocode_confidence") or 0.0)
    if scope == "state":
        conf = min(conf, 0.25)
    elif scope == "district":
        conf = min(conf, 0.4)
    return Geocode(
        signal_id=signal_id,
        toponym=toponym,
        feature_type=_FEATURES.get(geo.get("feature_type"), geo.get("feature_type")),
        lon=geo.get("lon") if point else None,
        lat=geo.get("lat") if point else None,
        segment_id=geo.get("segment_id"),
        junction_id=geo.get("junction_id"),
        snapped_to=None,
        method=_METHODS.get(geo.get("method"), geo.get("method")),
        residual_m=geo.get("residual_m"),
        confidence=round(conf, 4),
        bucket=_BUCKETS.get(geo.get("bucket"), geo.get("bucket") or "low"),
        area_level=bool(geo.get("area_level")),
        area_scope=scope,
        alternatives=[str(a) for a in (geo.get("alternatives") or [])][:16],
    )


class PocReplay:
    """``run_pipeline``-compatible: the PoC's fused output for the given PoC signals."""

    def __init__(self, prefix: str, out_dir: Path = POC_OUT) -> None:
        self.prefix = prefix
        self.fused = json.loads((out_dir / "events.fused.json").read_text(encoding="utf-8"))["fused_events"]
        geo = json.loads((out_dir / "events.geo.json").read_text(encoding="utf-8"))["events"]
        records = json.loads((out_dir / "signals.raw.json").read_text(encoding="utf-8"))
        self.by_url = {r["url"]: r["signal_id"] for r in records if r.get("url")}
        self.geo_by_signal = {e["osint_event_id"]: e["geo"] for e in geo}
        self.class_by_signal = {e["osint_event_id"]: e.get("event_class") for e in geo}
        self.calls = 0

    def fused_id(self, poc_id: str) -> str:
        return f"{self.prefix}-{poc_id[:22]}"[:64]

    def __call__(
        self,
        signals: Sequence[RawOsintSignal],
        *,
        resolver: Any = None,
        live: Any = None,
        embedder: Any = None,
        now: datetime | None = None,
    ) -> PipelineResult:
        self.calls += 1
        given = {s.signal_id: s for s in signals}
        geocodes = {
            sid: (_geocode(sid, self.geo_by_signal[sid]) if sid in self.geo_by_signal else None)
            for sid in given
        }
        resolved: list[ResolvedEvent] = []
        for fe in self.fused:
            members = [self.by_url[src["url"]] for src in fe["sources"] if self.by_url.get(src["url"]) in given]
            if not members:
                continue
            sources = []
            for i, src in enumerate(s for s in fe["sources"] if self.by_url.get(s["url"]) in given):
                sig = given[self.by_url[src["url"]]]
                tier = kinds.SOURCE_PRIORS[sig.source].tier
                sources.append(SourceRef(
                    signal_id=sig.signal_id, source=sig.source, publisher=sig.publisher,
                    url=src["url"] if tier == "official" else None, title=sig.title,
                    event_class=src["event_class"], credibility=src["credibility"],
                    fetch_mode=sig.fetch_mode, role="primary" if i == 0 else "corroborating",
                ))
            primary = given[members[0]]
            times = [given[m].published_at for m in members if given[m].published_at]
            klass = fe["event_class"].replace("_", " ").capitalize()
            lon, lat = (fe.get("rep_lonlat") or [None, None])[:2]
            resolved.append(ResolvedEvent(
                fused_event_id=self.fused_id(fe["fused_event_id"]),
                event_class=fe["event_class"],
                correlated_classes=fe["correlated_classes"],
                subtype=fe.get("subtype"),
                veer_event_kind=fe.get("veer_event_kind"),
                veer_incident_kind=fe.get("veer_incident_kind"),
                label=f"{klass} · {fe.get('toponym') or 'Ahmedabad district'}",
                summary=primary.title[:200],
                rep_lon=lon, rep_lat=lat,
                toponym=fe.get("toponym"),
                segment_id=fe.get("segment_id"),
                junction_id=fe.get("junction_id"),
                geocode_confidence=fe.get("geocode_confidence"),
                area_level=bool(fe.get("area_level")),
                window_start=min(times) if times else None,
                window_end=max(times) if times else None,
                credibility=fe["credibility"],
                verification_state=fe["verification_state"],
                source_count=len(members),
                source_tiers=fe["source_tiers"],
                independent_publishers=fe["independent_publishers"],
                cross_type_corroborated=fe["cross_type_corroborated"],
                second_order=[],
                labels=fe["labels"],
                attach=AttachResult(novel=bool((fe.get("attach") or {}).get("novel", True))),
                is_event=fe["is_event"],
                held_reason=fe.get("held_reason"),
                sources=sources,
                member_signal_ids=members,
            ))
        counts = PipelineCounts(
            signals=len(given),
            geotagged=sum(1 for g in geocodes.values() if g is not None),
            incident_geotagged=sum(
                1 for sid, g in geocodes.items()
                if g is not None and self.class_by_signal.get(sid) in kinds.INCIDENT_CLASSES
            ),
            fused=len(resolved),
            surfaced=sum(1 for e in resolved if e.is_event),
            correlated=sum(1 for e in resolved if e.is_event and len(e.correlated_classes) > 1),
            social_held=sum(1 for e in resolved if not e.is_event and set(e.source_tiers) == {"social_unverified"}),
            pii_redactions=sum(s.pii_redactions for s in given.values()),
        )
        return PipelineResult(geocodes=geocodes, resolved=resolved, counts=counts)
