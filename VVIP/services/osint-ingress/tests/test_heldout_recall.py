"""Held-out recall of parse-time person redaction (F-HONEST OSINT-2).

``ethics.find_pii(redacted) == []`` holds by construction (the redactor replaces every span of the very patterns
``find_pii`` reads), so it proves nothing about the names those patterns cannot see. This test measures the
redactor on three corpora of real-shaped headlines and posts (every person invented), each scored by recall of
its labelled name words and age markers and by the survival of its ``keep`` phrases (precision):

* ``heldout_names.json`` (A): written by the FIX-G-OSINT author BEFORE the cue-less, Indic-script and social
  age-marker rules existed. Its author also wrote those rules, so it is not independent of them;
* ``heldout_names_blind.json`` (B): written by a separate agent that never saw the code. Scored once untouched
  (latin 0.899, indic 0.967, ages 0.750, keep 1.000); the misses it showed were then fixed with general rules
  (initials, "@" aliases, compound and apostrophe surnames, Indic ages and initials), so B is no longer held out;
* ``heldout_names_blind2.json`` (C): written by another blind agent AFTER every rule, scored once and never
  tuned on. Its floors are its first score, rounded down: this is the honest figure, and its misses are known
  gaps (an ALL-CAPS headline, a given name that is also a word, single names after uncued verbs).

The floors are what a regression may not drop under, not a claim that redaction is complete: no NER runs at parse.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from osint_ingress.connectors._redact import redact_persons

FIXTURES = Path(__file__).resolve().parent / "fixtures"
#: corpus -> floors (latin name-word recall, indic name-word recall, age-marker recall, keep rate)
CORPORA: dict[str, tuple[float, float, float, float]] = {
    "heldout_names.json": (1.0, 1.0, 1.0, 1.0),
    "heldout_names_blind.json": (1.0, 1.0, 1.0, 1.0),
    "heldout_names_blind2.json": (0.88, 1.0, 0.89, 0.98),
}
CORPUS = FIXTURES / "heldout_names.json"


def _cases(corpus: Path | None = None) -> list[dict]:
    return json.loads((corpus or CORPUS).read_text(encoding="utf-8"))["cases"]


def _present(word: str, text: str) -> bool:
    if word.isascii():
        return re.search(rf"(?<![A-Za-z0-9]){re.escape(word)}(?![A-Za-z0-9])", text) is not None
    return word in text  # an Indic word may carry a case ending ("પરમારની"): a substring is a survival


def _score(protect: frozenset[str], corpus: Path | None = None) -> dict[str, object]:
    latin = [0, 0]
    indic = [0, 0]
    ages = [0, 0]
    keeps = [0, 0]
    misses: list[str] = []
    for c in _cases(corpus):
        out, _ = redact_persons(c["text"], c["tier"], protect)
        for w in c["names"]:
            bucket = latin if w.isascii() else indic
            bucket[1] += 1
            if _present(w, out):
                misses.append(f"{c['id']}: name word kept")
            else:
                bucket[0] += 1
        for a in c["ages"]:
            ages[1] += 1
            if a in out:
                misses.append(f"{c['id']}: age marker kept")
            else:
                ages[0] += 1
        for k in c["keep"]:
            keeps[1] += 1
            if k in out:
                keeps[0] += 1
            else:
                misses.append(f"{c['id']}: keep phrase lost")
    rate = lambda p: p[0] / p[1] if p[1] else 1.0  # noqa: E731
    return {
        "latin": rate(latin), "indic": rate(indic), "ages": rate(ages), "keep": rate(keeps),
        "counts": {"latin": latin, "indic": indic, "ages": ages, "keep": keeps}, "misses": misses,
    }


@pytest.mark.parametrize("name", sorted(CORPORA))
def test_the_corpus_is_well_formed(name):
    cases = _cases(FIXTURES / name)
    assert len(cases) >= 40 and len({c["id"] for c in cases}) == len(cases)
    for c in cases:
        assert c["tier"] in ("news_regional", "aggregator", "social_unverified"), c["id"]
        for w in c["names"]:
            assert _present(w, c["text"]), c["id"]  # every label is in its text before redaction
        for x in (*c["keep"], *c["ages"]):
            assert x in c["text"], c["id"]


@pytest.mark.parametrize("name", sorted(CORPORA))
def test_heldout_recall_meets_the_floors(protect, capsys, name):
    s = _score(protect, FIXTURES / name)
    with capsys.disabled():  # the honest figure is reported on every run, ids only (no name is printed)
        print(f"\n{name}: latin name recall {s['latin']:.3f}, indic {s['indic']:.3f}, age markers {s['ages']:.3f}, "
              f"keep {s['keep']:.3f}; counts {s['counts']}; misses {s['misses']}")
    latin, indic, ages, keep = CORPORA[name]
    assert s["latin"] >= latin, s
    assert s["indic"] >= indic, s
    assert s["ages"] >= ages, s
    assert s["keep"] >= keep, s


@pytest.mark.parametrize("tier", ["news_regional", "aggregator", "social_unverified"])
def test_no_indic_script_name_survives_in_any_reporting_tier(protect, tier):
    for name in CORPORA:
        for c in _cases(FIXTURES / name):
            if all(w.isascii() for w in c["names"]) or not c["names"]:
                continue
            out, n = redact_persons(c["text"], tier, protect)
            assert n > 0 and not any(_present(w, out) for w in c["names"]), c["id"]
