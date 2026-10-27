#!/usr/bin/env python3
"""OS-5 store parity on the int3c sandbox — a script (its output is evidence/OS-5/parity.txt).

    cd services/traffic-oracle
    OSINT_TEST_DSN=<the int3c sandbox DSN> PYTHONPATH=src:../osint-common/src:tests \
        python tests/fixtures/osint/parity_store.py

1. ingest the PoC's 107 signals (read in place) through the real ``POST /api/v1/osint/signals``, with
   the replay pipeline built from the PoC's ``events.fused.json`` (``fixtures/osint/replay.py``);
2. ``GET /osint/events`` returns exactly the 3 surfaced situations with the PoC's labels,
   credibilities and verification states;
3. ``/city/entities`` returns 3 ``osint_event`` entities with ``source "osint"`` and the 1–3 linked
   places; ``feeds.osint_event.held_social`` equals 7;
4. the SG Highway situation is promoted as "Sandbox Officer" → a corridor event of kind
   ``road_accident`` (status active, the officer in its ledger);
5. clean up: the event is cancelled through the lifecycle, then every test row is deleted (and the
   gazetteer rows, when this run had to sync them into an empty table).

The app runs IN PROCESS over an asyncpg pool to int3c — ``OSINT_TEST_DSN`` is required and must
name 127.0.0.1:56561 (anything else, or no DSN, is refused before a connection is opened; no DSN is
written in this file); no port is opened and no live service is called.  Nothing but counts, ids, class names,
verification labels, credibilities and gazetteer PLACE names is printed — never a title, a text, a
URL or the DSN.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path
from urllib.parse import urlsplit

import asyncpg
import structlog
from httpx import ASGITransport, AsyncClient

from fixtures.osint.replay import ADAPTER_STEPS, POC_OUT, PocReplay
from traffic_oracle.city import common
from traffic_oracle.osint import ingest, store

DSN_ENV = "OSINT_TEST_DSN"
OFFICER = "Sandbox Officer"
GAZETTEER = Path(__file__).resolve().parents[5] / "scripts" / "data" / "osint_gazetteer.json"


def _refuse(dsn: str | None) -> None:
    if not dsn:
        sys.exit(f"parity_store: set {DSN_ENV} to the int3c sandbox (127.0.0.1:56561) — refused")
    parts = urlsplit(dsn)
    if parts.hostname != "127.0.0.1" or parts.port != 56561:
        sys.exit("parity_store: only the int3c sandbox (127.0.0.1:56561) — refused")


async def _counts(conn, prefix: str, ids: list[str], event_id: str | None) -> dict[str, int]:
    like = prefix + "%"
    return {
        "raw_signals": await conn.fetchval("SELECT count(*) FROM osint.raw_signals WHERE signal_id = ANY($1::text[])", ids),
        "resolved_events": await conn.fetchval("SELECT count(*) FROM osint.resolved_events WHERE fused_event_id LIKE $1", like),
        "event_sources": await conn.fetchval("SELECT count(*) FROM osint.event_sources WHERE signal_id = ANY($1::text[])", ids),
        "geocodes": await conn.fetchval("SELECT count(*) FROM osint.geocodes WHERE signal_id = ANY($1::text[])", ids),
        "corridor_event": await conn.fetchval(
            "SELECT count(*) FROM events.corridor_events WHERE event_id = $1::uuid", event_id) if event_id else 0,
    }


async def main() -> int:
    # the oracle's own log lines go to stderr: stdout is the evidence (counts and ids only)
    structlog.configure(logger_factory=structlog.PrintLoggerFactory(file=sys.stderr))
    dsn = os.environ.get(DSN_ENV)
    _refuse(dsn)
    records = json.loads((POC_OUT / "signals.raw.json").read_text(encoding="utf-8"))
    fused = json.loads((POC_OUT / "events.fused.json").read_text(encoding="utf-8"))["fused_events"]
    poc_surfaced = {f["fused_event_id"]: f for f in fused if f["is_event"]}
    poc_held_social = sum(1 for f in fused if not f["is_event"] and set(f["source_tiers"]) == {"social_unverified"})
    ids = [r["signal_id"] for r in records]
    prefix = f"test-{uuid.uuid4()}"
    replay = PocReplay(prefix)
    sg_poc = next(f for f in poc_surfaced.values() if f["segment_id"] == 1045)

    print("# OS-5 store parity — int3c sandbox (127.0.0.1:56561), the oracle app IN PROCESS (no port opened)")
    print(f"# PoC outputs read in place from {POC_OUT} (nothing copied); run prefix {prefix}")
    print("# replay pipeline (PoC events.fused.json as it is), adapter steps:")
    for step in ADAPTER_STEPS:
        print(f"#   - {step}")
    ok = True

    pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=4, command_timeout=60)
    synced_gaz: list[int] = []
    event_id: str | None = None
    try:
        async with pool.acquire() as conn:
            if await conn.fetchval("SELECT count(*) FROM osint.raw_signals WHERE signal_id = ANY($1::text[])", ids):
                print("ABORT: PoC signals already stored on int3c — this run never touches rows it did not write")
                return 2
            gaz_before = await conn.fetchval("SELECT count(*) FROM osint.gazetteer")
            if gaz_before == 0:
                entries = json.loads(GAZETTEER.read_text(encoding="utf-8"))["entries"]
                async with conn.transaction():
                    stats = await store.sync_gazetteer(conn, entries)
                synced_gaz = [int(e["gaz_id"]) for e in entries]
                print(f"[0] osint.gazetteer was empty: synced the committed X19 gazetteer for this run {stats} "
                      "(deleted again at cleanup)")
            else:
                print(f"[0] osint.gazetteer already holds {gaz_before} places: used as it is")

        from traffic_oracle.__main__ import create_app

        common.reset_relation_cache()
        store.reset_gazetteer_sync()
        store.GAZETTEER_LOADER = lambda: []
        app = create_app()
        app.state.pool = pool
        app.state.adaptive_valkey = None
        app.state.graph_db = None
        app.dependency_overrides[ingest.get_pipeline] = lambda: ingest.Pipeline(run=replay, resolver=object())

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://127.0.0.1", timeout=120) as c:
            # [1] ingest
            r = await c.post("/api/v1/osint/signals", json={"signals": records, "run_id": "os5-poc-parity"})
            body = r.json()
            print(f"[1] POST /osint/signals: HTTP {r.status_code}; {len(records)} PoC signals → accepted "
                  f"{body.get('accepted')}, duplicates {body.get('duplicates')}, rejected {len(body.get('rejected', []))}, "
                  f"geotagged {body.get('geotagged')}")
            print(f"    trust boundary: {body.get('trust_boundary')} (news/social links withheld; priors re-derived)")
            print(f"    counts: {body.get('counts')}")
            ok &= r.status_code == 200 and body["accepted"] == 107 and not body["rejected"]
            async with pool.acquire() as conn:
                news_urls = await conn.fetchval(
                    "SELECT count(*) FROM osint.raw_signals WHERE signal_id = ANY($1::text[]) AND source_tier <> "
                    "'official' AND url IS NOT NULL", ids)
                hashed = await conn.fetchval(
                    "SELECT count(*) FROM osint.raw_signals WHERE signal_id = ANY($1::text[]) AND source_id LIKE "
                    "'sha256:%'", ids)
            print(f"    stored news/social rows with a URL: {news_urls} (must be 0); URL-shaped source ids stored "
                  f"hashed: {hashed}")
            ok &= news_urls == 0

            # [2] GET /osint/events
            r = await c.get("/api/v1/osint/events")
            listed = r.json()
            mine = [e for e in listed["events"] if e["fused_event_id"].startswith(prefix)]
            print(f"[2] GET /osint/events: HTTP {r.status_code}; this run's surfaced situations: {len(mine)} "
                  f"(PoC: {len(poc_surfaced)})")
            by_suffix = {replay.fused_id(k): v for k, v in poc_surfaced.items()}
            for e in mine:
                p = by_suffix.get(e["fused_event_id"])
                same = (p is not None and e["labels"] == p["labels"]
                        and abs(e["credibility"] - p["credibility"]) < 1e-6
                        and e["verification_state"] == p["verification_state"])
                ok &= same
                print(f"    {e['fused_event_id'][-22:-10]}… {e['event_class']:<15} labels={e['labels']} "
                      f"credibility={e['credibility']} state={e['verification_state']} sources={e['source_count']} "
                      f"segment={e['segment_id']} junction={e['junction_id']} area_level={e['area_level']} "
                      f"— {'== PoC' if same else 'DIFFERS FROM PoC'}")
            print(f"    held (counts only): {listed['held']}")
            ok &= len(mine) == 3 and {e["fused_event_id"] for e in mine} == set(by_suffix)

            # [3] /city/entities
            r = await c.get("/api/v1/city/entities")
            snap = r.json()
            ents = [e for e in snap["entities"] if e["kind"] == "osint_event"
                    and e["props"]["fused_event_id"].startswith(prefix)]
            mine_urns = {e["urn"] for e in ents}
            places = [e for e in snap["entities"] if e["kind"] == "place"
                      and set(e["links"]) & mine_urns]
            held_social = snap["feeds"]["osint_event"].get("held_social")
            print(f"[3] GET /city/entities: HTTP {r.status_code}; osint_event entities of this run: {len(ents)}, "
                  f"sources {sorted({e['source'] for e in ents})}, verification "
                  f"{sorted({e['verification_state'] for e in ents})}")
            print(f"    linked places: {len(places)} {sorted(e['props']['canonical_name'] for e in places)}")
            print(f"    feeds.osint_event.held_social = {held_social} (PoC held social-only situations: "
                  f"{poc_held_social}); feeds keyed by entity kind: "
                  f"{set(snap['feeds']) == set(common.ENTITY_KINDS)}; feeds.osint present: {'osint' in snap['feeds']}")
            ok &= (len(ents) == 3 and all(e["source"] == "osint" for e in ents) and 1 <= len(places) <= 3
                   and held_social == 7 and "osint" not in snap["feeds"])

            # [4] promote the SG Highway situation
            sg = next(e for e in mine if e["fused_event_id"] == replay.fused_id(sg_poc["fused_event_id"]))
            r = await c.post(f"/api/v1/osint/events/{sg['osint_event_id']}/promote", json={},
                             headers={"x-veer-officer": OFFICER})
            promo = r.json()
            event_id = promo.get("event_id")
            print(f"[4] promote the SG Highway situation as {OFFICER!r}: HTTP {r.status_code} → "
                  f"event_kind {promo.get('event_kind')}, status {promo.get('status')}, source_kind "
                  f"{promo.get('source_kind')}, verification {promo.get('verification_state')}")
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT e.event_kind, e.status, e.source_kind, e.verification_state, e.credibility, "
                    "(SELECT array_agg(r.segment_ids) FROM events.event_routes r WHERE r.event_id = e.event_id) AS spines, "
                    "ST_X(e.geotag) AS lon, ST_Y(e.geotag) AS lat FROM events.corridor_events e WHERE e.event_id = $1::uuid",
                    event_id)
                ledger = await conn.fetch(
                    "SELECT from_status, to_status, actor FROM events.event_status_log WHERE event_id = $1::uuid ORDER BY seq",
                    event_id)
            print(f"    corridor event: kind {row['event_kind']}, status {row['status']}, source_kind {row['source_kind']}, "
                  f"verification {row['verification_state']}, credibility {round(row['credibility'], 4)}, spine "
                  f"{[list(s) for s in row['spines']]}, geotag ({round(row['lon'], 4)}, {round(row['lat'], 4)})")
            print("    lifecycle ledger: " + "; ".join(f"{x['from_status']}→{x['to_status']} by {x['actor']}" for x in ledger))
            r2 = await c.get("/api/v1/city/feed", params={"kinds": "osint", "limit": 500})
            promo_row = next((i for i in r2.json()["items"] if i["id"] == f"osint_promotion:{event_id}"), None)
            print(f"    city feed: {promo_row['text'] if promo_row else 'NO PROMOTION ROW'} "
                  f"({promo_row['actor_kind'] if promo_row else '-'}, source {promo_row['source'] if promo_row else '-'})")
            again = await c.post(f"/api/v1/osint/events/{sg['osint_event_id']}/promote", json={},
                                 headers={"x-veer-officer": OFFICER})
            print(f"    promoting again: HTTP {again.status_code} {again.json().get('detail')} (event_id "
                  f"{'matches' if again.json().get('event_id') == event_id else 'DIFFERS'})")
            ok &= (r.status_code == 201 and promo["event_kind"] == "road_accident" and row["status"] == "active"
                   and row["source_kind"] == "osint" and [list(s) for s in row["spines"]] == [[1045]]
                   and all(x["actor"] == OFFICER for x in ledger) and promo_row is not None
                   and again.status_code == 409)

            # [5] cleanup: cancel through the lifecycle, then delete the test rows
            r = await c.post(f"/api/v1/events/{event_id}/status",
                             json={"to_status": "cancelled", "officer": OFFICER, "note": "OS-5 parity cleanup"})
            print(f"[5] cleanup: lifecycle cancel HTTP {r.status_code} ({r.json().get('from_status')}→"
                  f"{r.json().get('to_status')} by {r.json().get('actor')})")
            ok &= r.status_code == 200
    finally:
        async with pool.acquire() as conn:
            async with conn.transaction():
                like = prefix + "%"
                await conn.execute(
                    "DELETE FROM osint.event_sources WHERE signal_id = ANY($1::text[]) OR osint_event_id IN "
                    "(SELECT osint_event_id FROM osint.resolved_events WHERE fused_event_id LIKE $2)", ids, like)
                await conn.execute("DELETE FROM osint.geocodes WHERE signal_id = ANY($1::text[])", ids)
                await conn.execute("DELETE FROM osint.resolved_events WHERE fused_event_id LIKE $1", like)
                await conn.execute("DELETE FROM osint.raw_signals WHERE signal_id = ANY($1::text[])", ids)
                if event_id:
                    await conn.execute("DELETE FROM events.corridor_events WHERE event_id = $1::uuid", event_id)
                if synced_gaz:
                    await conn.execute("DELETE FROM osint.gazetteer WHERE gaz_id = ANY($1::bigint[])", synced_gaz)
            left = await _counts(conn, prefix, ids, event_id)
            gaz_left = await conn.fetchval("SELECT count(*) FROM osint.gazetteer WHERE gaz_id = ANY($1::bigint[])",
                                           synced_gaz) if synced_gaz else 0
        await pool.close()
        print(f"    test rows left after delete: {left}; gazetteer rows this run added still present: {gaz_left}")
        ok &= not any(left.values()) and not gaz_left
    print("PARITY " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
