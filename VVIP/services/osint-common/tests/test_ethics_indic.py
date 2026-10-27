"""F-HONEST OSINT-2: Indic-script words no redactor can read for names are found (``ethics.unredactable_spans``).

``find_pii`` reads Latin-script cue patterns only, so a Gujarati or Devanagari name passed it as clean (the audit
stored "<Hindi name> के खिलाफ ..." beside its own redacted Latin copy). The names below are fictional.
"""

from __future__ import annotations

import pytest

from osint_common import ethics


def _apply(text: str) -> str:
    out = text
    for s in reversed(ethics.unredactable_spans(text)):
        out = out[: s.start] + "[W]" + out[s.end :]
    return out


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("नवरंगपुरा में फिक्टस डमीवाला की हत्या", "नवरंगपुरा में [W] की हत्या"),
        ("મણિનગરમાં કલ્પિત ઉદાહરણવાલાનું મોત", "મણિનગરમાં [W] મોત"),
        ("પાલડીમાં આગ", "પાલડીમાં આગ"),  # a gazetteer place with a case ending, and a common word
        ("ઓઢવ રિંગ રોડ સર્કલ પાસે અકસ્માત", "ઓઢવ રિંગ રોડ સર્કલ પાસે અકસ્માત"),  # a multi-word place phrase
        ("एस जी हाईवे पर टक्कर", "एस जी हाईवे पर टक्कर"),
        ("પીઆઈ કે. ડી. ફિક્ટસવાલાએ જણાવ્યું", "[W]. [W]. [W]"),  # initials are a name part, whatever they spell
        ("Plain ASCII text with no script", "Plain ASCII text with no script"),
    ],
)
def test_unknown_indic_words_are_found_and_places_kept(text, expected):
    assert _apply(text) == expected


def test_find_pii_does_not_see_indic_names_and_find_unredactable_does():
    text = "अहमदाबाद में फिक्टस डमीवाला की हत्या"
    assert ethics.find_pii(text) == []  # the documented limit of find_pii: Latin cue patterns only
    assert ethics.find_unredactable(text) == ["script:indic"]
    assert ethics.find_unredactable("अहमदाबाद में हत्या") == []
    assert ethics.find_unredactable(None) == [] and ethics.find_unredactable("") == []


def test_a_multi_word_place_keeps_its_words_only_where_the_whole_phrase_occurs():
    # "પટેલ" (a surname) is a word of the gazetteer phrase "ચીમનભાઈ પટેલ ફ્લાયઓવર": alone it is withheld
    assert _apply("ફિક્ટસ પટેલ") == "[W]"


def test_common_words_hold_no_name():
    for word in ("કિરણ", "किरण", "आशा", "विजय", "दीपक", "રાજ", "रमेश", "પટેલ", "शाह"):
        assert ethics._indic_key(word) not in ethics.INDIC_COMMON_WORDS, word
