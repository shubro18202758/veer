"""Canonical SYNTHETIC fixtures for every OSINT WP (X18; plan R13).

Synthetic replicas of the PoC's cases, never real captures:

* the publishers are fictional (``news-a.example``, ``news-b.example``, and ``social-a.example`` for the Reddit
  replica, whose community ``example_city`` is fictional too): no fabricated text is attributed to a real outlet
  or community. Only the official alerts name a real publisher, ``sachet.ndma.gov.in`` (public-domain NDMA CAP),
  and their text is written here;
* no real person's name appears anywhere: the person names and ages the replicas "had" are already redacted to
  ``[PERSON]`` / ``[AGE]``, exactly as a connector emits them (``pii_redactions`` counts them);
* the toponyms and class cues are the PoC's (Karnavati Club on SG Highway, segment 1045; Odhav Ring Road Circle,
  junction 11; an Ahmedabad-district SACHET alert; a state-wide SACHET nowcast naming other districts).

Every function returns fresh objects (mutating one never leaks into another test) and is deterministic: fixed
timestamps, ids derived with :func:`osint_common.types.signal_id_for` and ``uuid5``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from osint_common.kinds import SOURCE_PRIORS
from osint_common.types import (
    Ahp,
    AttachResult,
    Cascade,
    Coa,
    CoaAction,
    CoaEthics,
    CoaScore,
    Criterion,
    DecisionSupport,
    DisruptionStats,
    DssProvenance,
    DssSituation,
    EmergencyImpact,
    Geocode,
    HumanGate,
    LiveEventRef,
    LiveStateSnapshot,
    PredictedOutcome,
    RawGeoHint,
    RawOsintSignal,
    Recommendation,
    ResourceFeasibility,
    Sensitivity,
    SourceRef,
    SpilloverStats,
    ValueOfInformation,
    signal_id_for,
)

__all__ = [
    "NEWS_A",
    "NEWS_B",
    "SACHET",
    "SOCIAL_A",
    "SYNTHETIC_NAMESPACE",
    "live_state_kalupur_pursuit",
    "odhav_robbery_signal",
    "sachet_district_signal",
    "sachet_state_signal",
    "sg_highway_dss",
    "sg_highway_geocode",
    "sg_highway_signals",
    "social_single_signal",
]

#: Fictional publishers (synthetic replicas only, plan R13).
NEWS_A = "news-a.example"
NEWS_B = "news-b.example"
#: The fictional social host of the synthetic Reddit replica (never a real community).
SOCIAL_A = "social-a.example"
#: The official CAP publisher (public domain); the alert texts below are synthetic.
SACHET = "sachet.ndma.gov.in"

#: Namespace of every synthetic uuid in this kit.
SYNTHETIC_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://veer.example/osint/testing")

_FETCHED = datetime(2026, 10, 20, 15, 0, 0, tzinfo=UTC)


def _uuid(name: str) -> str:
    return str(uuid.uuid5(SYNTHETIC_NAMESPACE, name))


def _signal(
    source: str,
    source_id: str,
    *,
    title: str,
    text: str,
    published_at: datetime,
    publisher: str | None,
    url: str | None,
    pii_redactions: int = 0,
    place_names: list[str] | None = None,
    admin_codes: list[str] | None = None,
    category_hint: list[str] | None = None,
    valid_until: datetime | None = None,
    raw: dict | None = None,
) -> RawOsintSignal:
    prior = SOURCE_PRIORS[source]
    return RawOsintSignal(
        signal_id=signal_id_for(source, source_id),
        source=source,  # type: ignore[arg-type]
        source_id=source_id,
        source_tier=prior.tier,  # type: ignore[arg-type]
        publisher=publisher,
        url=url,
        title=title,
        text=text,
        language="en",
        published_at=published_at,
        fetched_at=_FETCHED,
        valid_until=valid_until,
        fetch_mode="cached-sample",
        pii_redactions=pii_redactions,
        raw_geo_hint=RawGeoHint(place_names=place_names or [], admin_codes=admin_codes or []),
        category_hint=category_hint or [],
        tone=None,
        provenance_label=prior.provenance_label,  # type: ignore[arg-type]
        credibility_prior=prior.credibility_prior,
        license=prior.license,
        redistributable=prior.redistributable,
        raw=raw or {},
    )


def _news(n: int, publisher: str, minute: int, title: str, body: str, *, pii: int = 0) -> RawOsintSignal:
    return _signal(
        "google_news_rss",
        f"synthetic:sg-highway-{n}",
        title=title,
        text=f"{title}. {body}",
        published_at=datetime(2026, 10, 20, 13, minute, 0, tzinfo=UTC),
        publisher=publisher,
        url=f"https://{publisher}/city/sg-highway-report-{n}",
        pii_redactions=pii,
        category_hint=[f"publisher:{publisher}", f"domain:{publisher}"],
        raw={"guid": f"synthetic:sg-highway-{n}", "source_domain": publisher},
    )


def sg_highway_signals() -> list[RawOsintSignal]:
    """The SG Highway case: four news reports of a multi-vehicle collision near Karnavati Club (segment 1045)
    and one report of a crowd assaulting a driver at the scene — two fictional publishers, one tier.

    The four collision reports classify ``road_accident`` and the fifth ``public_conflict``; co-located, they
    correlate into one ``affray+collision`` situation at credibility 0.65, ``NEWS-REPORTED`` (no official source).
    """
    return [
        _news(
            1,
            NEWS_A,
            40,
            "Car crashes into three vehicles near Karnavati Club on SG Highway; 3 injured",
            "A speeding car hit three vehicles near Karnavati Club on SG Highway in Prahlad Nagar on Tuesday "
            "evening, injuring three people including a [AGE] scooter rider, traffic police said.",
            pii=1,
        ),
        _news(
            2,
            NEWS_B,
            55,
            "Multi-vehicle crash on SG Highway near Prahlad Nagar leaves three injured",
            "Traffic slowed on SG Highway near Prahlad Nagar after the multi-vehicle crash; the injured were "
            "taken to a hospital.",
        ),
        _news(
            3,
            NEWS_B,
            58,
            "SG Highway accident: vehicles collided near Prahlad Nagar, one lane blocked",
            "One lane of SG Highway near Prahlad Nagar stayed blocked while the damaged vehicles were cleared.",
        ),
        _news(
            4,
            NEWS_A,
            59,
            "Three injured after car rammed vehicles on SG Highway near Karnavati Club",
            "The car rammed vehicles waiting near Karnavati Club on SG Highway; police are recording statements.",
        ),
        _news(
            5,
            NEWS_B,
            50,
            "Driver beaten by mob after SG Highway crash near Karnavati Club",
            "Locals surrounded the car near Karnavati Club after the crash and the driver, identified as "
            "[PERSON], was beaten by the mob before police arrived.",
            pii=1,
        ),
    ]


def odhav_robbery_signal() -> RawOsintSignal:
    """A reported daylight robbery at Odhav Ring Road Circle (junction 11): ``reported_crime``, credibility 0.60."""
    title = "Jewellery shop robbed at gunpoint near Odhav Ring Road Circle"
    return _signal(
        "google_news_rss",
        "synthetic:odhav-robbery-1",
        title=title,
        text=f"{title}. A jewellery shop near Odhav Ring Road Circle was robbed at gunpoint in broad daylight, "
        "police said; the area was cordoned off for an hour.",
        published_at=datetime(2026, 10, 20, 10, 15, 0, tzinfo=UTC),
        publisher=NEWS_B,
        url=f"https://{NEWS_B}/city/odhav-robbery",
        category_hint=[f"publisher:{NEWS_B}", f"domain:{NEWS_B}"],
        raw={"guid": "synthetic:odhav-robbery-1", "source_domain": NEWS_B},
    )


def _cap(identifier: str, *, title: str, text: str, ahmedabad: bool, minute: int) -> RawOsintSignal:
    area = "ahmedabad" if ahmedabad else "gujarat"
    return _signal(
        "sachet_cap",
        identifier,
        title=title,
        text=f"{title}. {text}",
        published_at=datetime(2026, 10, 20, 12, minute, 0, tzinfo=UTC),
        publisher=SACHET,
        url=None,
        place_names=["Ahmedabad"] if ahmedabad else ["Gujarat"],
        admin_codes=["LGD:AHMEDABAD"] if ahmedabad else ["LGD:GUJARAT"],
        category_hint=["CAP", f"area:{area}"],
        valid_until=datetime(2026, 10, 20, 15, minute, 0, tzinfo=UTC),
        raw={
            "cap_identifier": identifier,
            "cap_event": "Thunderstorm",
            "cap_severity": "Moderate",
            "cap_urgency": "Expected",
            "cap_certainty": "Likely",
        },
    )


def sachet_district_signal() -> RawOsintSignal:
    """An official SACHET CAP alert naming Ahmedabad: a DISTRICT-level area (``LGD:AHMEDABAD``), credibility 0.95,
    ``OFFICIAL-VERIFIED``; a thunderstorm warning, so ``weather_hazard`` (not a flood)."""
    return _cap(
        "synthetic.sachet.ahmedabad.20261020T1200",
        title="Thunderstorm and lightning warning for Ahmedabad district",
        text="Thunderstorm with lightning and gusty winds of 40-50 km/h is likely at isolated places in "
        "Ahmedabad district during the next 3 hours.",
        ahmedabad=True,
        minute=0,
    )


def sachet_state_signal() -> RawOsintSignal:
    """A state-wide SACHET nowcast (``LGD:GUJARAT``) naming OTHER districts: a STATE-level area with no point in
    the city, so its situation is held and counted in ``held.outside_city`` (plan R28), never an Ahmedabad event."""
    return _cap(
        "synthetic.sachet.gujarat-nowcast.20261020T1210",
        title="Nowcast warning: thunderstorm likely over Banaskantha, Patan and Mehsana districts",
        text="Thunderstorm with lightning is likely over Banaskantha, Patan, Mehsana and Sabarkantha districts of "
        "Gujarat during the next 3 hours.",
        ahmedabad=False,
        minute=10,
    )


def social_single_signal() -> RawOsintSignal:
    """One synthetic Reddit-replica post about a road closed for metro work at Paldi: ``social_unverified``,
    credibility 0.25, on the fictional host ``social-a.example`` in the fictional community ``example_city``.

    Its class (``road_closure``) is an event class related to none of the other fixtures, so the ONLY reason it is
    held is the aggregate-only rule: a single social source is never an event. Its author handle never existed in
    the record (dropped at parse)."""
    title = "Road closed for metro work near Paldi cross roads, traffic diverted"
    return _signal(
        "reddit_rss",
        "synthetic:t3_paldi01",
        title=title,
        text=f"{title}. Expect a slow crawl around the cross roads this evening.",
        published_at=datetime(2026, 10, 20, 14, 30, 0, tzinfo=UTC),
        publisher=SOCIAL_A,
        url=f"https://{SOCIAL_A}/r/example_city/comments/paldi01/",
        category_hint=["subreddit:example_city"],
        raw={"subreddit": "example_city"},
    )


def live_state_kalupur_pursuit() -> LiveStateSnapshot:
    """The live corridor state with one active, human-initiated vehicle pursuit in the old city near Kalupur
    (Gandhi Road → Nehru Bridge Road → Relief Road → Swami Vivekananda Road); ~9 km from the SG Highway case."""
    return LiveStateSnapshot(
        as_of=datetime(2026, 10, 20, 15, 0, 0, tzinfo=UTC),
        live_events=[
            LiveEventRef(
                urn=f"event:{_uuid('live-kalupur-pursuit')}",
                event_kind="vehicle_pursuit",
                status="active",
                lon=72.586996,
                lat=23.024353,
                segment_ids=[1012, 1015, 1005, 1013],
            )
        ],
        ambulance_routes=[],
        closures=[],
    )


def sg_highway_geocode() -> Geocode:
    """The primary SG Highway report resolved to the Karnavati Club landmark, snapped to segment 1045 (190.5 m)."""
    return Geocode(
        signal_id=sg_highway_signals()[0].signal_id,
        toponym="Karnavati Club (SG Highway)",
        feature_type="landmark",
        lon=72.503,
        lat=23.009,
        segment_id=1045,
        junction_id=None,
        snapped_to="SG Highway (Prahlad Nagar)",
        method="gazetteer_exact",
        residual_m=190.5,
        confidence=0.719,
        bucket="medium",
        area_level=False,
        area_scope=None,
        alternatives=["SG Highway (Prahlad Nagar)", "Prahlad Nagar"],
    )


# ---------------------------------------------------------------------------
# A synthetic DecisionSupport with the PoC dss_output.json structure (C-U)
# ---------------------------------------------------------------------------

_SURROGATE = (
    "DSS Monte-Carlo surrogate (SIMULATED, 240 replications, seeded); production: the seeded corridor twin for "
    "per-route disruption plus the DSS-layer cascade over the segment neighbours"
)
_CRITERIA = (
    ("safety_risk_reduction", "Public-safety risk reduction (fixed prior by COA actions, not simulated)", "benefit",
     0.3121, True),
    ("time_to_effect", "Speed of effect (nominal time by COA kind, not a unit ETA)", "benefit", 0.1075, True),
    ("resource_cost", "Resource cost", "cost", 0.0247, True),
    ("public_disruption", "Public traffic disruption", "cost", 0.0507, True),
    ("cascade_risk", "Cascade / spillover risk", "cost", 0.0739, True),
    ("reversibility", "Reversibility", "benefit", 0.0183, True),
    ("affected_population", "Affected population", "cost", 0.035, True),
    ("protocol_compliance", "Protocol compliance", "benefit", 0.2223, False),
    ("legality", "Legality", "benefit", 0.1555, False),
)
_AHP_ORDER = [
    "safety_risk_reduction",
    "protocol_compliance",
    "legality",
    "time_to_effect",
    "cascade_risk",
    "public_disruption",
    "affected_population",
    "resource_cost",
    "reversibility",
]
_CLEAN = CoaEthics(
    touches_persons=False,
    legal=True,
    protocol_ok=True,
    irreversible_without_officer=False,
    vetoed=False,
    veto_reason=None,
)


def _attrs(*values: float) -> dict[str, float]:
    return {c[0]: v for c, v in zip(_CRITERIA, values, strict=True)}


def _outcome(
    response: float | None,
    disruption: tuple[float, float, float | None],
    spill: tuple[float, float],
    neighbourhoods: list[str],
    routes: list[str],
    delay: float,
    tte: float,
    resolution: float,
) -> PredictedOutcome:
    return PredictedOutcome(
        response_time_to_scene_sec=response,
        total_disruption_vehicle_hours=DisruptionStats(
            mean=disruption[0], p90=disruption[1], p90_mean_ratio=disruption[2], replications=240
        ),
        cascade=Cascade(
            spillover_vehicle_hours=SpilloverStats(mean=spill[0], p90=spill[1]),
            neighbourhoods_touched=neighbourhoods,
            parallel_routes_loaded=routes,
            affected_segment_ids=[1045] if neighbourhoods else [],
        ),
        emergency_impact=EmergencyImpact(ambulance_delay_sec=delay, green_corridor_ok=delay <= 0),
        time_to_effect_sec=tte,
        event_resolution_prob=resolution,
        method=_SURROGATE,
    )


def _feasibility(need: dict[str, int], free: dict[str, int], eta: float | None) -> ResourceFeasibility:
    shortfalls = [f"{k}: need {n}, {free.get(k, 0)} free" for k, n in need.items() if n > free.get(k, 0)]
    return ResourceFeasibility(
        required_resources=need or {"none": 0},
        availability={k: free.get(k, 0) for k in need},
        eta_to_scene_sec=eta,
        feasible=not shortfalls,
        shortfalls=shortfalls,
    )


def _act(verb: str, target: str | None = None, requires_officer: bool = False, **params: object) -> CoaAction:
    return CoaAction(
        verb=verb,  # type: ignore[arg-type]
        target_urn=target,
        params=dict(params),
        requires_officer=requires_officer,
        reversible=True,
    )


def sg_highway_dss() -> DecisionSupport:
    """A proposed decision support for the SG Highway situation: five COAs (baseline, minimal, standard,
    aggressive, information), the full-closure COA resource-infeasible (one patrol is on the Kalupur pursuit) and
    ranked last, the standard response recommended, EVOI below the information cost (act now)."""
    signals = sg_highway_signals()
    sources = [
        SourceRef(
            signal_id=s.signal_id,
            source=s.source,
            publisher=s.publisher,
            url=s.url,
            title=s.title,
            event_class="public_conflict" if i == 4 else "road_accident",
            credibility=s.credibility_prior,
            fetch_mode=s.fetch_mode,
            role="primary" if i == 0 else "corroborating",
        )
        for i, s in enumerate(signals)
    ]
    free = {"ambulance_108": 1, "police_patrol": 1}
    place = "place:sg_highway_prahladnagar"
    seg = "segment:1045"
    parallel = ["132 Ft Ring Road", "Prahlad Nagar Road"]
    coas = [
        Coa(
            coa_id="coa_base",
            kind="baseline",
            label="Monitor only (do nothing)",
            actions=[_act("monitor")],
            predicted_outcome=_outcome(None, (0.0, 0.0, None), (0.0, 0.0), [], [], 0, 0, 0.3),
            resource_feasibility=_feasibility({}, free, None),
            attributes=_attrs(0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
            score=CoaScore(method="topsis", closeness=0.2192, rank=3, feasible=True),
            ethics=_CLEAN,
        ),
        Coa(
            coa_id="coa_min",
            kind="minimal",
            label="Driver and citizen advisory only (VMS + app push)",
            actions=[_act("advisory", place)],
            predicted_outcome=_outcome(None, (98.8, 115.1, 1.165), (40.3, 47.1), [], [], 0, 120, 0.38),
            resource_feasibility=_feasibility({}, free, None),
            attributes=_attrs(0.0, 0.8, 1.0, 0.962, 0.973, 1.0, 1.0, 1.0, 1.0),
            score=CoaScore(method="topsis", closeness=0.19, rank=4, feasible=True),
            ethics=_CLEAN,
        ),
        Coa(
            coa_id="coa_std",
            kind="standard",
            label="Advisory + 108 ambulance + 1 patrol + signal priority",
            actions=[
                _act("advisory", place),
                _act("dispatch", seg, True, agency="ambulance", count=1),
                _act("dispatch", seg, True, agency="police", count=1),
                _act("signal_hold", "junction:28", True, mode="emergency_priority"),
            ],
            predicted_outcome=_outcome(
                393, (866.7, 1062.0, 1.225), (353.6, 433.9), ["Prahlad Nagar", "Vejalpur"], parallel, -60, 300, 0.88
            ),
            resource_feasibility=_feasibility({"ambulance_108": 1, "police_patrol": 1}, free, 480),
            attributes=_attrs(0.88, 0.5, 0.5, 0.667, 0.764, 1.0, 0.4, 1.0, 1.0),
            score=CoaScore(method="topsis", closeness=0.8555, rank=1, feasible=True),
            ethics=_CLEAN,
        ),
        Coa(
            coa_id="coa_agg",
            kind="aggressive",
            label="Close carriageway + full diversion + 108 + 2 police units",
            actions=[
                _act("closure", seg, True),
                _act("diversion", seg, True, via=parallel),
                _act("dispatch", seg, True, agency="ambulance", count=1),
                _act("dispatch", seg, True, agency="police", count=2),
            ],
            predicted_outcome=_outcome(
                480,
                (2514.9, 3566.7, 1.418),
                (1026.7, 1467.0),
                ["Prahlad Nagar", "Vejalpur", "Satellite"],
                parallel,
                180,
                420,
                0.97,
            ),
            resource_feasibility=_feasibility({"ambulance_108": 1, "police_patrol": 2}, free, 480),
            attributes=_attrs(0.72, 0.3, 0.08, 0.033, 0.316, 0.75, 0.1, 1.0, 1.0),
            score=CoaScore(method="topsis", closeness=0.7098, rank=5, feasible=False),
            ethics=_CLEAN,
        ),
        Coa(
            coa_id="coa_info",
            kind="information",
            label="Verify first: 1 patrol to confirm + ICCC situation check (no identification) + 10-min hold",
            actions=[
                _act("dispatch", seg, True, agency="police", count=1, role="verify"),
                _act("request_cctv", "junction:28"),
            ],
            predicted_outcome=_outcome(None, (22.1, 25.9, 1.171), (9.0, 10.6), [], [], 0, 240, 0.68),
            resource_feasibility=_feasibility({"police_patrol": 1}, free, 420),
            attributes=_attrs(0.28, 0.6, 0.82, 0.992, 0.994, 1.0, 1.0, 1.0, 1.0),
            score=CoaScore(method="topsis", closeness=0.3529, rank=2, feasible=True),
            ethics=_CLEAN,
        ),
    ]
    discriminating = [c[0] for c in _CRITERIA if c[4]]
    gate = [c[0] for c in _CRITERIA if not c[4]]
    return DecisionSupport(
        dss_id=_uuid("dss-sg-highway"),
        event_urn=f"osint_event:{_uuid('osint-event-sg-highway')}",
        state="proposed",
        generated_at=datetime(2026, 10, 20, 15, 5, 0, tzinfo=UTC),
        horizon_min=45,
        seed=20261024,
        situation=DssSituation(
            summary=(
                "5 reports across 2 related classes (road_accident, public_conflict) correlated into one "
                "situation at Karnavati Club (SG Highway): " + signals[0].title
            ),
            event_class="road_accident",
            correlated_classes=["road_accident", "public_conflict"],
            subtype="affray+collision",
            veer_event_kind="road_accident",
            toponym="Karnavati Club (SG Highway)",
            segment_id=1045,
            junction_id=None,
            rep_lonlat=(72.503, 23.009),
            credibility=0.65,
            independent_publishers=2,
            source_tiers=["aggregator"],
            cross_type_corroborated=False,
            attach=AttachResult(novel=True),
            verification_state="NEWS-REPORTED",
            geocode_confidence=0.719,
            composite_confidence=0.688,
        ),
        criteria=[
            Criterion(
                id=cid,
                label=label,
                direction=direction,  # type: ignore[arg-type]
                weight=weight,
                weight_source="ahp",
                role="discriminating" if disc else "gate (non-discriminating)",
            )
            for cid, label, direction, weight, disc in _CRITERIA
        ],
        ahp=Ahp(consistency_ratio=0.0346, acceptable=True, rank_order=_AHP_ORDER),
        scoring_note=(
            f"TOPSIS runs over the {len(discriminating)} discriminating criteria {discriminating}; the "
            f"{len(gate)} gate criteria {gate} are constant across the surviving COAs (handled by the lexical "
            "veto) and are reported as gate-passed."
        ),
        coa_set=coas,
        # This replica mirrors the PoC's pre-floor ranking (coa_base above coa_min) for parity, so it keeps
        # public_safety_floor at its default "none"; the engine itself would hold the baseline here ("hold").
        recommendation=Recommendation(
            ranked_coa_ids=["coa_std", "coa_info", "coa_base", "coa_min", "coa_agg"],
            top_coa_id="coa_std",
            margin=0.5026,
            sensitivity=Sensitivity(rank_stability=1.0, flips_to={}),
            value_of_information=ValueOfInformation(
                evoi=-0.0105,
                L_act_now=0.36,
                L_gather_then_act=0.3705,
                info_cost=0.2,
                advise_gather=False,
                info_coa_id="coa_info",
                why=(
                    "acting now dominates: EVOI -0.011 <= info cost 0.200 (credibility 0.65 and margin 0.503 "
                    "already justify committing to the recommended feasible COA)"
                ),
            ),
            dissent=(
                "Runner-up is coa_info (verify first, closeness 0.353 vs 0.855). It is not chosen because it is "
                "dominated on the heavily weighted safety and cascade criteria, with 100% rank stability under "
                "weight perturbation. It would flip if the weighting moved toward time to effect, or if an "
                "official source (police or ICCC confirmation) changed the credibility. Corroboration is real but "
                "within one tier: 2 independent news publishers, no official confirmation yet, so the report "
                "stays NEWS-REPORTED. The full-closure COA is resource-infeasible this cycle (police_patrol: need "
                "2, 1 free) and is ranked last and labelled, not hidden."
            ),
            decision="await_officer",
            strategy_prior=None,
        ),
        provenance=DssProvenance(
            feeds=["google_news_rss"],
            publishers=[NEWS_A, NEWS_B],
            sources=sources,
            sim_run_ids=[],
            model_tiers=[],
            wargame_method="surrogate",
            brain_degraded=False,
        ),
        human_gate=HumanGate(state="proposed", required_role="duty_officer", officer=None, decided_at=None),
        labels=["NEWS-REPORTED", "SIMULATED"],
    )
