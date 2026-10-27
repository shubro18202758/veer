"""Test helpers for osint-analysis: SYNTHETIC signals and a fake resolver (plan R13).

Every signal here is a synthetic replica: fictional publishers on reserved ``*.example`` hosts (the canonical
``osint_common.testing`` fixtures, plus ad-hoc ones built by :func:`make_signal`), the public-domain SACHET
publisher for official alerts with texts written here, and no real person's name anywhere. Coordinates are the
committed gazetteer's (Karnavati Club, SG Highway at Prahlad Nagar, Odhav Ring Road Circle, Paldi Cross Roads,
Nehru Bridge Road, Naroda, Bopal Junction, Maninagar).

:func:`poc_out_dir` finds the PoC outputs, which are read in place and never copied (plan R13): ``$OSINT_POC_DIR``,
else ``.veer-orchestration/osint/prototype/out`` next to an ancestor of this file; ``None`` when absent (the PoC
tests then skip).
"""

from __future__ import annotations

import itertools
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from osint_common import testing
from osint_common.kinds import SOURCE_PRIORS
from osint_common.types import Geocode, LiveEventRef, LiveStateSnapshot, RawGeoHint, RawOsintSignal, signal_id_for

#: (lon, lat) of gazetteer places used by the fixtures
KARNAVATI_CLUB = (72.503, 23.009)  # landmark, snapped to SG Highway (Prahlad Nagar) segment 1045, 190.5 m
SG_HIGHWAY_PRAHLAD = (72.5013522, 23.0082042)  # road, segment 1045
ODHAV_CIRCLE = (72.6731179, 23.0249602)  # junction 11
PALDI_CROSS_ROADS = (72.5630916, 23.0111693)  # junction 4
NEHRU_BRIDGE_ROAD = (72.5775682, 23.027165)  # road, segment 1015 (on the Kalupur pursuit spine)
KALUPUR_PURSUIT = (72.586996, 23.024353)  # the live pursuit's representative point
DISTRICT_POINT = (72.5714, 23.0225)  # the Ahmedabad district representative point
NARODA = (72.66, 23.07)  # neighbourhood, ~11 km north-east of Paldi
BOPAL_JUNCTION = (72.4764446, 23.0257902)  # junction 29, ~9 km west of Paldi
MANINAGAR = (72.603, 22.998)  # neighbourhood

#: Where the PoC outputs may be (read in place): an environment override, else a sibling of an ancestor directory.
POC_DIR_ENV = "OSINT_POC_DIR"
_POC_RELATIVE = Path(".veer-orchestration", "osint", "prototype", "out")


def poc_out_dir() -> Path | None:
    """The PoC's ``prototype/out`` directory (``signals.raw.json`` inside), or ``None`` when it is not here."""
    env = os.environ.get(POC_DIR_ENV)
    candidates = [Path(env)] if env else [p / _POC_RELATIVE for p in Path(__file__).resolve().parents]
    return next((c for c in candidates if (c / "signals.raw.json").is_file()), None)

T0 = datetime(2026, 10, 20, 13, 0, 0, tzinfo=UTC)
FETCHED = datetime(2026, 10, 20, 15, 0, 0, tzinfo=UTC)

_SEQ = itertools.count(1)


def make_signal(
    source: str = "google_news_rss",
    *,
    title: str,
    text: str | None = None,
    published_at: datetime | None = T0,
    publisher: str | None = "news-a.example",
    url: str | None = None,
    pii: int = 0,
    place_names: list[str] | None = None,
    admin_codes: list[str] | None = None,
    category_hint: list[str] | None = None,
    valid_until: datetime | None = None,
    provenance_label: str | None = None,
    source_tier: str | None = None,
    credibility_prior: float | None = None,
    fetched_at: datetime | None = None,
    source_id: str | None = None,
) -> RawOsintSignal:
    """A synthetic signal with the source's priors (overridable, to test pass-through and tier rules)."""
    prior = SOURCE_PRIORS[source]
    sid = source_id or f"synthetic:test-{next(_SEQ)}"
    if url is None and publisher and publisher.endswith(".example"):
        url = f"https://{publisher.split('/', 1)[0]}/city/{sid.split(':', 1)[-1]}"
    return RawOsintSignal(
        signal_id=signal_id_for(source, sid),
        source=source,  # type: ignore[arg-type]
        source_id=sid,
        source_tier=source_tier or prior.tier,  # type: ignore[arg-type]
        publisher=publisher,
        url=url,
        title=title,
        text=text if text is not None else title,
        language="en",
        published_at=published_at,
        fetched_at=fetched_at or max(FETCHED, published_at or FETCHED),
        valid_until=valid_until,
        fetch_mode="cached-sample",
        pii_redactions=pii,
        raw_geo_hint=RawGeoHint(place_names=place_names or [], admin_codes=admin_codes or []),
        category_hint=category_hint or [],
        tone=None,
        provenance_label=provenance_label or prior.provenance_label,  # type: ignore[arg-type]
        credibility_prior=prior.credibility_prior if credibility_prior is None else credibility_prior,
        license=prior.license,
        redistributable=prior.redistributable,
        raw={},
    )


def at(minutes: float) -> datetime:
    """``T0`` plus some minutes."""
    return T0 + timedelta(minutes=minutes)


def point(
    signal: RawOsintSignal,
    lonlat: tuple[float, float] = KARNAVATI_CLUB,
    *,
    toponym: str = "Karnavati Club (SG Highway)",
    feature_type: str = "landmark",
    segment_id: int | None = None,
    junction_id: int | None = None,
    residual_m: float | None = 0.0,
    confidence: float = 0.7,
    snapped_to: str | None = None,
) -> Geocode:
    """A point, junction or snapped-landmark geocode."""
    return Geocode(
        signal_id=signal.signal_id,
        toponym=toponym,
        feature_type=feature_type,  # type: ignore[arg-type]
        lon=lonlat[0],
        lat=lonlat[1],
        segment_id=segment_id,
        junction_id=junction_id,
        snapped_to=snapped_to,
        method="gazetteer_exact",
        residual_m=residual_m,
        confidence=confidence,
        bucket="high" if confidence >= 0.75 else "medium" if confidence >= 0.5 else "low",
    )


def karnavati(signal: RawOsintSignal, confidence: float = 0.719) -> Geocode:
    """The Karnavati Club landmark snapped to segment 1045 (190.5 m), as ``sg_highway_geocode()``."""
    return point(
        signal,
        KARNAVATI_CLUB,
        segment_id=1045,
        residual_m=190.5,
        confidence=confidence,
        snapped_to="SG Highway (Prahlad Nagar)",
    )


def road(
    signal: RawOsintSignal,
    segment_id: int = 1045,
    lonlat: tuple[float, float] = SG_HIGHWAY_PRAHLAD,
    *,
    toponym: str = "SG Highway (Prahlad Nagar)",
    confidence: float = 0.68,
) -> Geocode:
    """A road (line) geocode on its own segment."""
    return point(signal, lonlat, toponym=toponym, feature_type="road", segment_id=segment_id, confidence=confidence)


def district(
    signal: RawOsintSignal, toponym: str = "Ahmedabad (district)", lonlat: tuple[float, float] = DISTRICT_POINT
) -> Geocode:
    """A district-level area: the district point, confidence 0.4 (plan R28)."""
    return Geocode(
        signal_id=signal.signal_id,
        toponym=toponym,
        feature_type="admin",
        lon=lonlat[0],
        lat=lonlat[1],
        method="area_fallback",
        confidence=0.4,
        bucket="low",
        area_level=True,
        area_scope="district",
    )


def state(signal: RawOsintSignal, toponym: str = "Gujarat (state)") -> Geocode:
    """A state-level area: no point, confidence 0.25 (plan R28)."""
    return Geocode(
        signal_id=signal.signal_id,
        toponym=toponym,
        feature_type="admin",
        method="area_fallback",
        confidence=0.25,
        bucket="low",
        area_level=True,
        area_scope="state",
    )


class FakeResolver:
    """A :class:`osint_common.pipeline.GeoResolver` that answers from a mapping (``None`` otherwise)."""

    def __init__(self, geocodes: list[Geocode] | None = None) -> None:
        self.by_id: dict[str, Geocode] = {g.signal_id: g for g in geocodes or []}
        self.calls: list[str] = []

    def add(self, *geocodes: Geocode) -> FakeResolver:
        for g in geocodes:
            self.by_id[g.signal_id] = g
        return self

    def resolve(self, signal: RawOsintSignal) -> Geocode | None:
        self.calls.append(signal.signal_id)
        return self.by_id.get(signal.signal_id)


def sg_highway_geocodes(signals: list[RawOsintSignal] | None = None) -> list[Geocode]:
    """The synthetic SG Highway replica geocoded as the PoC geocoded the real one: the Karnavati Club reports to
    the landmark (segment 1045, 190.5 m), the Prahlad Nagar reports to the SG Highway road (segment 1045)."""
    sg = signals or testing.sg_highway_signals()
    out = []
    for s in sg:
        out.append(road(s) if "Prahlad Nagar" in s.title else karnavati(s))
    return out


def canonical_signals() -> list[RawOsintSignal]:
    """Every canonical ``osint_common.testing`` signal: the SG Highway five, the Odhav robbery, the two SACHET alerts
    (district and state-wide) and the single social post."""
    return [
        *testing.sg_highway_signals(),
        testing.odhav_robbery_signal(),
        testing.sachet_district_signal(),
        testing.sachet_state_signal(),
        testing.social_single_signal(),
    ]


def canonical_resolver() -> FakeResolver:
    """A resolver for :func:`canonical_signals`, at the precision OS-3 gives each (plan R28 for the areas)."""
    odhav = testing.odhav_robbery_signal()
    social = testing.social_single_signal()
    return FakeResolver(
        [
            *sg_highway_geocodes(),
            point(
                odhav,
                ODHAV_CIRCLE,
                toponym="Odhav Ring Road Circle (SP Ring Road)",
                feature_type="junction",
                junction_id=11,
                confidence=0.718,
            ),
            district(testing.sachet_district_signal()),
            state(testing.sachet_state_signal()),
            point(
                social,
                PALDI_CROSS_ROADS,
                toponym="Paldi Cross Roads (Ashram Road - CG Road)",
                feature_type="junction",
                junction_id=4,
                confidence=0.8,
            ),
        ]
    )


def live_state(
    *events: LiveEventRef,
    as_of: datetime = FETCHED,
    ambulance: list[tuple[str, list[int]]] | None = None,
    closures: list[tuple[int, str]] | None = None,
) -> LiveStateSnapshot:
    """A live snapshot for the attach and second-order tests."""
    return LiveStateSnapshot.model_validate(
        {
            "as_of": as_of,
            "live_events": [e.model_dump() for e in events],
            "ambulance_routes": [{"dispatch_urn": u, "segment_ids": s} for u, s in ambulance or []],
            "closures": [{"segment_id": s, "event_urn": u} for s, u in closures or []],
        }
    )


def live_event(
    urn: str = "event:00000000-0000-4000-8000-000000000001",
    *,
    kind: str = "procession",
    status: str = "active",
    lonlat: tuple[float, float] | None = None,
    segments: list[int] | None = None,
) -> LiveEventRef:
    return LiveEventRef(
        urn=urn,
        event_kind=kind,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        lon=None if lonlat is None else lonlat[0],
        lat=None if lonlat is None else lonlat[1],
        segment_ids=segments or [],
    )


def offset(lonlat: tuple[float, float], north_m: float = 0.0, east_m: float = 0.0) -> tuple[float, float]:
    """A point moved by some metres north and east (small-distance approximation)."""
    import math

    lon, lat = lonlat
    dlat = north_m / 111_195.0
    dlon = east_m / (111_195.0 * math.cos(math.radians(lat)))
    return (lon + dlon, lat + dlat)


#: The OS-4 review-3 laundering cases: an AREA-level member that says nothing about the street (a SACHET Ahmedabad
#: alert, or a district-level GDELT report), and point-level social posts it must never corroborate.
AREA_SOCIAL_CASES = ("sachet_alert_one_post", "gdelt_district_one_post", "sachet_alert_one_community")
#: The live refs of :func:`route_live_state` (synthetic URNs).
ROUTE_FLOODING_URN = "event:00000000-0000-4000-8000-0000000000f1"
ROUTE_MOVEMENT_URN = "event:00000000-0000-4000-8000-0000000000f2"
ROUTE_ACCIDENT_URN = "event:00000000-0000-4000-8000-0000000000f3"
ROUTE_CLOSURE_URN = "event:00000000-0000-4000-8000-0000000000f4"
ROUTE_DISPATCH_URN = "dispatch:00000000-0000-4000-8000-0000000000a1"


def _post_geocode(signal: RawOsintSignal, k: int, on_route: bool) -> Geocode:
    if on_route:
        return road(signal, 1015, offset(NEHRU_BRIDGE_ROAD, north_m=20 * k), toponym="Nehru Bridge Road")
    return point(
        signal,
        offset(PALDI_CROSS_ROADS, north_m=20 * k),
        toponym="Paldi Cross Roads",
        feature_type="junction",
        junction_id=4,
        confidence=0.8,
    )


def area_social_case(
    case: str, *, on_route: bool = False
) -> tuple[RawOsintSignal, list[RawOsintSignal], FakeResolver]:
    """``(area member, posts, resolver)`` for one of :data:`AREA_SOCIAL_CASES`. The posts are at Paldi Cross Roads
    (junction 4), or with ``on_route`` on Nehru Bridge Road (segment 1015, the segment of
    :func:`route_live_state`). The area member and the posts share their words (each pair links on text)."""
    place = "on Nehru Bridge road" if on_route else "at Paldi cross roads underpass"
    if case == "gdelt_district_one_post":
        area = make_signal("gdelt_doc", title="Road accident in Ahmedabad, two injured", publisher="news-b.example",
                           published_at=at(0))
        area_geo = district(area, toponym="Ahmedabad, Gujarat, India")
        titles = [f"Road accident {place}, two injured"]
    elif case in ("sachet_alert_one_post", "sachet_alert_one_community"):
        area = make_signal("sachet_cap", title="Heavy rain and waterlogging alert for Ahmedabad district",
                           publisher="sachet.ndma.gov.in", admin_codes=["LGD:AHMEDABAD"], published_at=at(0),
                           valid_until=at(600))
        area_geo = district(area)
        titles = [f"Heavy rain, waterlogging {place} right now"]
        if case == "sachet_alert_one_community":
            titles.append(f"Heavy rain, waterlogging {place} right now, still rising")
    else:  # pragma: no cover - a typo in a test
        raise ValueError(case)
    posts = [
        make_signal("reddit_rss", title=t, publisher="social-a.example/r/example_city", published_at=at(30 + 10 * k))
        for k, t in enumerate(titles)
    ]
    resolver = FakeResolver([area_geo, *(_post_geocode(p, k, on_route) for k, p in enumerate(posts))])
    return area, posts, resolver


def independent_report(case: str, tier: str = "news", *, on_route: bool = False) -> tuple[RawOsintSignal, Geocode]:
    """A point-level report of the same situation as :func:`area_social_case`'s posts, at the same place, from an
    independent publisher: a news outlet (``tier="news"``) or a civic body (``tier="official"``)."""
    place = "on Nehru Bridge road" if on_route else "at Paldi cross roads underpass"
    if case == "gdelt_district_one_post":
        title = f"Road accident {place}: two injured, traffic slow"
    else:
        title = f"Waterlogging {place} after heavy rain right now"
    if tier == "official":
        report = make_signal("amc_scrape", title=title, publisher="civic-body.example", published_at=at(40))
    else:
        report = make_signal("google_news_rss", title=title, publisher="news-c.example", published_at=at(40))
    return report, _post_geocode(report, 3, on_route)


def route_live_state(as_of: datetime | None = None) -> LiveStateSnapshot:
    """Live state on and around Nehru Bridge Road (segment 1015): an active flooding event and an active road
    accident 200 m away, an active protected movement on the segment, a 108 route on it, and a closure of it."""
    near = offset(NEHRU_BRIDGE_ROAD, east_m=200)
    return live_state(
        live_event(ROUTE_FLOODING_URN, kind="flooding", lonlat=near),
        live_event(ROUTE_ACCIDENT_URN, kind="road_accident", lonlat=near),
        live_event(ROUTE_MOVEMENT_URN, kind="protected_movement", segments=[1015]),
        as_of=as_of or at(60),
        ambulance=[(ROUTE_DISPATCH_URN, [1015])],
        closures=[(1015, ROUTE_CLOSURE_URN)],
    )
