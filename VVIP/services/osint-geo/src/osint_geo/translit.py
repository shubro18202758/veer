"""Gujarati and Hindi aliases and transliterations of the gazetteer's places (the PoC's ``GU_LATIN_SEED``, extended).

Ahmedabad text mixes English, Gujarati, Hindi and Latin transliteration. Three reviewable tables carry what the
gazetteer needs to match all of them, in the posture of ``scripts/data/osm_network_map.json`` (a hand-kept table a
reviewer can read line by line; nothing here is fetched or learned):

* :data:`GU_LATIN_SEED` — the PoC's Gujarati → Latin seed (``build_gazetteer.GU_LATIN_SEED``), normalised;
* :data:`PLACE_SCRIPTS` — for a Latin place name the gazetteer carries, its Gujarati and Devanagari spellings;
* :data:`LATIN_VARIANTS` — Latin spelling variants seen in local text ("darwaza" for "darwaja", "iscon").

:data:`GENERIC_GU` and :data:`GENERIC_HI` map the generic place words of both scripts ("ચાર રસ્તા", "चौराहा") to the
gazetteer's Latin generic ("cross roads"), so :func:`to_latin` can read a compositional name the tables do not list
("થલતેજ ચોકડી" → "thaltej cross roads"). :data:`GU_SUFFIXES` lists the Gujarati case endings written onto a place
name ("મણિનગરમાં", in Maninagar), which the gazetteer's scanner strips when the stem is a known place word.

Deliberately absent: script spellings of a place whose name is a common word in that script (Satellite, Gota), and
any person's name on its own. Every multi-word Latin variant keeps a place-type word, like every gazetteer phrase.

The module also holds :func:`norm`, the one normal form of the package (``osint_geo.gazetteer`` re-exports it), so
the tables and the matcher can never disagree. Stdlib only, so ``scripts/gen_osint_gazetteer.py`` imports it
without a virtual environment change.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from types import MappingProxyType

__all__ = [
    "GENERIC_GU",
    "GENERIC_HI",
    "GU_LATIN_SEED",
    "GU_SUFFIXES",
    "LATIN_VARIANTS",
    "PLACE_SCRIPTS",
    "is_indic",
    "latin_variants",
    "norm",
    "script_aliases",
    "to_latin",
]


_NON_WORD = re.compile(r"[^\w\u0900-\u097F\u0A80-\u0AFF ]+")
_SPACES = re.compile(r"\s+")
_ROAD_CODE = re.compile(r"\b(nh|sh|ne)\s(\d{1,4})\b")


def _fold_latin(s: str) -> str:
    """Drop the diacritics of Latin letters ("Vastrāpur" → "Vastrapur"); every other script is left untouched
    (Gujarati and Devanagari vowel signs are letters of their word, not decoration)."""
    out: list[str] = []
    for ch in s:
        if "\u00c0" <= ch <= "\u024f" or "\u1e00" <= ch <= "\u1eff":
            base = "".join(c for c in unicodedata.normalize("NFKD", ch) if not unicodedata.combining(c))
            out.append(base or ch)
        else:
            out.append(ch)
    return "".join(out)


def norm(s: object) -> str:
    """The gazetteer's normal form of a text or a surface form (re-exported as ``osint_geo.gazetteer.norm``):
    NFKC, lower case, Unicode format characters removed (a zero-width joiner never splits a word), Latin
    diacritics folded, every run of punctuation one space (Gujarati and Devanagari letters and vowel signs kept),
    and a split road code joined ("NH-147" → ``nh147``)."""
    t = unicodedata.normalize("NFKC", "" if s is None else str(s)).lower()
    if not t.isascii():
        t = "".join(ch for ch in t if unicodedata.category(ch) != "Cf")
        t = _fold_latin(t)
    t = _NON_WORD.sub(" ", t).replace("_", " ")
    t = _SPACES.sub(" ", t).strip()
    return _ROAD_CODE.sub(r"\1\2", t)


_n = norm


#: The PoC's seed (``build_gazetteer.GU_LATIN_SEED``): Gujarati junction and area names → their Latin form.
GU_LATIN_SEED: Mapping[str, str] = MappingProxyType(
    {
        _n(gu): latin
        for gu, latin in (
            ("લાલ દરવાજા", "lal darwaja"),
            ("ઇન્કમ ટેક્સ સર્કલ", "income tax circle"),
            ("ઇસ્કોન ચાર રસ્તા", "iskcon cross roads"),
            ("પાલડી ચાર રસ્તા", "paldi cross roads"),
            ("આસ્ટોડિયા દરવાજા", "astodia darwaja"),
            ("ગાંધી આશ્રમ જંક્શન", "gandhi ashram junction"),
            ("કાલુપુર સ્ટેશન જંક્શન", "kalupur station junction"),
            ("એરપોર્ટ સર્કલ", "airport circle"),
            ("મોટેરા જંક્શન", "motera junction"),
            ("બોપલ જંક્શન", "bopal junction"),
            ("શાહીબાગ", "shahibaug"),
        )
    }
)

#: Latin place name (as the gazetteer carries it) → (Gujarati spellings, Devanagari spellings).
_PLACE_SCRIPTS_SRC: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    # neighbourhoods (the PoC seed; Satellite and Gota are common words in both scripts and are left out)
    ("navrangpura", ("નવરંગપુરા",), ("नवरंगपुरा",)),
    ("maninagar", ("મણિનગર",), ("मणिनगर",)),
    ("paldi", ("પાલડી",), ("पालडी",)),
    ("bopal", ("બોપલ",), ("बोपल",)),
    ("naranpura", ("નારણપુરા",), ("नारणपुरा",)),
    ("vastrapur", ("વસ્ત્રાપુર",), ("वस्त्रापुर",)),
    ("bodakdev", ("બોડકદેવ",), ("बोडकदेव",)),
    ("thaltej", ("થલતેજ",), ("थलतेज",)),
    ("chandkheda", ("ચાંદખેડા",), ("चांदखेड़ा",)),
    ("naroda", ("નરોડા",), ("नरोडा",)),
    ("vastral", ("વસ્ત્રાલ",), ("वस्त्राल",)),
    ("ghatlodia", ("ઘાટલોડિયા",), ("घाटलोडिया",)),
    ("sabarmati", ("સાબરમતી",), ("साबरमती",)),
    ("memnagar", ("મેમનગર",), ("मेमनगर",)),
    ("nikol", ("નિકોલ",), ("निकोल",)),
    ("ranip", ("રાણીપ",), ("राणीप", "राणिप")),
    ("ambawadi", ("આંબાવાડી",), ("आंबावाडी",)),
    ("ellisbridge", ("એલિસબ્રિજ",), ("एलिसब्रिज",)),
    ("vejalpur", ("વેજલપુર",), ("वेजलपुर",)),
    ("prahlad nagar", ("પ્રહલાદનગર", "પ્રહલાદ નગર"), ("प्रह्लादनगर", "प्रहलाद नगर")),
    ("usmanpura", ("ઉસ્માનપુરા",), ("उस्मानपुरा",)),
    ("vadaj", ("વાડજ",), ("वाडज",)),
    ("shahibaug", ("શાહીબાગ",), ("शाहीबाग",)),
    ("odhav", ("ઓઢવ",), ("ओढव",)),
    ("jamalpur", ("જમાલપુર",), ("जमालपुर",)),
    ("adalaj", ("અડાલજ",), ("अडालज",)),
    ("kalupur", ("કાલુપુર",), ("कालूपुर", "कालुपुर")),
    # landmarks
    ("karnavati club", ("કર્ણાવતી ક્લબ",), ("कर्णावती क्लब",)),
    ("kankaria", ("કાંકરિયા",), ("कांकरिया",)),
    ("kankaria lake", ("કાંકરિયા તળાવ",), ("कांकरिया झील", "कांकरिया तालाब")),
    ("narendra modi stadium", ("નરેન્દ્ર મોદી સ્ટેડિયમ",), ("नरेंद्र मोदी स्टेडियम",)),
    ("motera stadium", ("મોટેરા સ્ટેડિયમ",), ("मोटेरा स्टेडियम",)),
    ("sabarmati riverfront", ("સાબરમતી રિવરફ્રન્ટ",), ("साबरमती रिवरफ्रंट",)),
    ("riverfront", ("રિવરફ્રન્ટ",), ("रिवरफ्रंट",)),
    ("iskcon temple", ("ઇસ્કોન મંદિર",), ("इस्कॉन मंदिर",)),
    ("law garden", ("લો ગાર્ડન",), ("लॉ गार्डन",)),
    ("manek chowk", ("માણેક ચોક",), ("माणेक चौक",)),
    ("bhadra fort", ("ભદ્રનો કિલ્લો",), ("भद्र किला",)),
    ("sabarmati ashram", ("સાબરમતી આશ્રમ",), ("साबरमती आश्रम",)),
    ("gandhi ashram", ("ગાંધી આશ્રમ",), ("गांधी आश्रम",)),
    ("ahmedabad airport", ("અમદાવાદ એરપોર્ટ",), ("अहमदाबाद एयरपोर्ट", "अहमदाबाद हवाई अड्डा")),
    ("civil hospital", ("સિવિલ હોસ્પિટલ",), ("सिविल अस्पताल", "सिविल हॉस्पिटल")),
    ("gujarat university", ("ગુજરાત યુનિવર્સિટી",), ("गुजरात विश्वविद्यालय", "गुजरात यूनिवर्सिटी")),
    ("gmdc ground", ("જીએમડીસી ગ્રાઉન્ડ",), ("जीएमडीसी ग्राउंड",)),
    ("kalupur railway station", ("કાલુપુર રેલવે સ્ટેશન",), ("कालूपुर रेलवे स्टेशन", "कालुपुर रेलवे स्टेशन")),
    ("ahmedabad railway station", ("અમદાવાદ રેલવે સ્ટેશન",), ("अहमदाबाद रेलवे स्टेशन",)),
    ("teen darwaja", ("ત્રણ દરવાજા",), ("तीन दरवाजा",)),
    ("flower park", ("ફ્લાવર પાર્ક",), ("फ्लावर पार्क",)),
    # roads (base names; the junction names come with their Gujarati name from osm_network.json)
    ("sg highway", ("એસ જી હાઈવે", "એસજી હાઈવે"), ("एसजी हाईवे", "एस जी हाईवे")),
    ("sp ring road", ("એસ પી રિંગ રોડ", "એસપી રિંગ રોડ"), ("एसपी रिंग रोड", "एस पी रिंग रोड")),
    ("ring road", ("રિંગ રોડ",), ("रिंग रोड",)),
    ("cg road", ("સી જી રોડ", "સીજી રોડ"), ("सीजी रोड", "सी जी रोड")),
    ("ashram road", ("આશ્રમ રોડ",), ("आश्रम रोड",)),
    ("relief road", ("રિલીફ રોડ",), ("रिलीफ रोड",)),
    ("gandhi road", ("ગાંધી રોડ",), ("गांधी रोड",)),
    ("airport road", ("એરપોર્ટ રોડ",), ("एयरपोर्ट रोड",)),
    ("drive in road", ("ડ્રાઇવ ઇન રોડ",), ("ड्राइव इन रोड",)),
    ("satellite road", ("સેટેલાઇટ રોડ",), ("सैटेलाइट रोड",)),
    ("gandhinagar highway", ("ગાંધીનગર હાઈવે",), ("गांधीनगर हाईवे",)),
    ("naroda road", ("નરોડા રોડ",), ("नरोडा रोड",)),
    ("station road", ("સ્ટેશન રોડ",), ("स्टेशन रोड",)),
    ("nehru bridge", ("નહેરુ બ્રિજ",), ("नेहरू ब्रिज", "नेहरू पुल")),
    ("science city road", ("સાયન્સ સિટી રોડ",), ("साइंस सिटी रोड",)),
    ("kankaria road", ("કાંકરિયા રોડ",), ("कांकरिया रोड",)),
    ("riverfront road", ("રિવરફ્રન્ટ રોડ",), ("रिवरफ्रंट रोड",)),
    ("132 ft ring road", ("૧૩૨ ફૂટ રિંગ રોડ", "132 ફૂટ રિંગ રોડ"), ("१३२ फुट रिंग रोड", "132 फुट रिंग रोड")),
    ("indira bridge", ("ઇન્દિરા બ્રિજ",), ("इंदिरा ब्रिज",)),
    ("chimanbhai patel flyover", ("ચીમનભાઈ પટેલ ફ્લાયઓવર",), ("चिमनभाई पटेल फ्लाईओवर",)),
    ("dr ambedkar road", ("ડૉ આંબેડકર રોડ", "ડો આંબેડકર રોડ"), ("डॉ अंबेडकर रोड", "डॉ आंबेडकर रोड")),
    ("sarangpur road", ("સારંગપુર રોડ",), ("सारंगपुर रोड",)),
    ("motera stadium road", ("મોટેરા સ્ટેડિયમ રોડ",), ("मोटेरा स्टेडियम रोड",)),
    ("commerce college road", ("કોમર્સ કોલેજ રોડ",), ("कॉमर्स कॉलेज रोड",)),
    ("ambli bopal road", ("આંબલી બોપલ રોડ",), ("आंबली बोपल रोड",)),
)

PLACE_SCRIPTS: Mapping[str, tuple[tuple[str, ...], tuple[str, ...]]] = MappingProxyType(
    {latin: (tuple(_n(g) for g in gu), tuple(_n(h) for h in hi)) for latin, gu, hi in _PLACE_SCRIPTS_SRC}
)

#: Latin spelling variants seen in Ahmedabad text, per Latin form the gazetteer carries.
LATIN_VARIANTS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "navrangpura": ("navarangpura",),
        "ghatlodia": ("ghatlodiya",),
        "ambawadi": ("ambavadi",),
        "sabarmati": ("sabarmathi",),
        "lal darwaja": ("lal darwaza",),
        "astodia darwaja": ("astodia darwaza",),
        "iskcon": ("iscon",),
        "iskcon cross roads": ("iscon cross roads",),
        "iskcon temple": ("iscon temple",),
        "sg highway": ("sg road", "s g road"),
        "drive in road": ("drivein road",),
        # the usual local spelling, as the Gujarati alias "૧૩૨ ફૂટ રિંગ રોડ" (ફૂટ, feet) already reads
        "132 ft ring road": ("132 feet ring road", "132 foot ring road"),
    }
)
# (Variants whose place word is itself a variant, "lal darvaja" or "manek chok", are not listed: every gazetteer
# phrase keeps a recognised place-type word, and the place grammar rewrites "darvaja" and "chok" at match time.)

#: Gujarati generic place words → the gazetteer's Latin generic.
GENERIC_GU: Mapping[str, str] = MappingProxyType(
    {
        _n(gu): latin
        for gu, latin in (
            ("ચાર રસ્તા", "cross roads"),
            ("ચોકડી", "cross roads"),
            ("સર્કલ", "circle"),
            ("દરવાજા", "darwaja"),
            ("દરવાજો", "darwaja"),
            ("રોડ", "road"),
            ("બ્રિજ", "bridge"),
            ("પુલ", "bridge"),
            ("ફ્લાયઓવર", "flyover"),
            ("ઓવરબ્રિજ", "overbridge"),
            ("અંડરપાસ", "underpass"),
            ("જંક્શન", "junction"),
            ("હાઈવે", "highway"),
            ("તળાવ", "lake"),
            ("સ્ટેશન", "station"),
            ("મંદિર", "temple"),
            ("ચોક", "chowk"),
            ("ગાર્ડન", "garden"),
            ("હોસ્પિટલ", "hospital"),
            ("ક્લબ", "club"),
            ("સ્ટેડિયમ", "stadium"),
        )
    }
)

#: Hindi (Devanagari) generic place words → the gazetteer's Latin generic.
GENERIC_HI: Mapping[str, str] = MappingProxyType(
    {
        _n(hi): latin
        for hi, latin in (
            ("चार रास्ता", "cross roads"),
            ("चौराहा", "cross roads"),
            ("सर्कल", "circle"),
            ("दरवाजा", "darwaja"),
            ("रोड", "road"),
            ("मार्ग", "road"),
            ("पुल", "bridge"),
            ("ब्रिज", "bridge"),
            ("फ्लाईओवर", "flyover"),
            ("ओवरब्रिज", "overbridge"),
            ("अंडरपास", "underpass"),
            ("जंक्शन", "junction"),
            ("हाईवे", "highway"),
            ("राजमार्ग", "highway"),
            ("झील", "lake"),
            ("तालाब", "lake"),
            ("स्टेशन", "station"),
            ("मंदिर", "temple"),
            ("चौक", "chowk"),
            ("गार्डन", "garden"),
            ("अस्पताल", "hospital"),
            ("क्लब", "club"),
            ("स्टेडियम", "stadium"),
        )
    }
)

#: Gujarati case endings written onto a noun (longest first): "મણિનગરમાં" (in Maninagar), "પાલડીના" (of Paldi),
#: "ઓઢવથી" (from Odhav). The scanner strips one only when what remains is a gazetteer word. The ending -e has two
#: spellings: the vowel sign "ે" after a consonant ("સ્ટેશને", at the station; "મણિનગરે") and the vowel letter "એ"
#: after a vowel ("પાલડીએ", at Paldi).
GU_SUFFIXES: tuple[str, ...] = tuple(
    sorted(
        {_n(s) for s in ("માંથી", "માંના", "માં", "થી", "નાં", "ના", "ની", "નું", "નો", "ને", "પર", "એ", "ે")},
        key=len,
        reverse=True,
    )
)


def _script_words() -> Mapping[str, str]:
    """Script word or phrase → Latin, for :func:`to_latin`: place names and generics of both scripts, the PoC seed
    winning on a clash."""
    words: dict[str, str] = {}
    for latin, (gu, hi) in PLACE_SCRIPTS.items():
        for s in gu + hi:
            words.setdefault(s, latin)
    for s, latin in (*GENERIC_GU.items(), *GENERIC_HI.items()):
        words.setdefault(s, latin)
    words.update(GU_LATIN_SEED)
    return MappingProxyType(words)


def _aliases() -> Mapping[str, tuple[str, ...]]:
    """Latin form → its Gujarati and Devanagari spellings (the place table, then the PoC seed)."""
    out: dict[str, tuple[str, ...]] = {
        latin: tuple(dict.fromkeys(gu + hi)) for latin, (gu, hi) in PLACE_SCRIPTS.items()
    }
    for gu, latin in GU_LATIN_SEED.items():
        out[latin] = tuple(dict.fromkeys((*out.get(latin, ()), gu)))
    return MappingProxyType(out)


_WORDS = _script_words()
_MAX_WORD_TOKENS = max(k.count(" ") + 1 for k in _WORDS)
_ALIASES = _aliases()
_INDIC = re.compile(r"[\u0900-\u097F\u0A80-\u0AFF]")


def is_indic(s: str) -> bool:
    """True when ``s`` contains a Devanagari or Gujarati character."""
    return _INDIC.search(s) is not None


def script_aliases(latin_form: str) -> tuple[str, ...]:
    """The Gujarati and Devanagari spellings of a Latin gazetteer form (normalised), or ``()``."""
    return _ALIASES.get(_n(latin_form), ())


def latin_variants(latin_form: str) -> tuple[str, ...]:
    """The Latin spelling variants of a Latin gazetteer form (normalised), or ``()``."""
    return LATIN_VARIANTS.get(_n(latin_form), ())


def to_latin(name: str) -> str | None:
    """A Gujarati or Hindi place name → its Latin form (the PoC's ``translit()``, extended): a whole-name lookup,
    else word by word over the place and generic tables ("થલતેજ ચોકડી" → "thaltej cross roads"). ``None`` unless
    every word is known: a partial transliteration would be a guess."""
    key = _n(name or "")
    if not key:
        return None
    if key in _WORDS:
        return _WORDS[key]
    toks = key.split(" ")
    out: list[str] = []
    i = 0
    while i < len(toks):
        for j in range(min(len(toks), i + _MAX_WORD_TOKENS), i, -1):
            latin = _WORDS.get(" ".join(toks[i:j]))
            if latin is not None:
                out.append(latin)
                i = j
                break
        else:
            return None
    return " ".join(out)
