"""Where the PoC's captures are read IN PLACE (never copied: plan R13). Not a test module.

``$OSINT_POC_DIR`` names the PoC prototype directory (the one holding ``ahmedabad_gazetteer.json`` and
``out/signals.raw.json``); without it, the orchestration checkout's path on the GB10 box. Tests that need the PoC
skip when its files are absent (CI, another machine), the convention of osint-common's ``test_no_real_names.py``.
"""

from __future__ import annotations

import os
from pathlib import Path

POC_DIR_ENV = "OSINT_POC_DIR"
_DEFAULT_POC_DIR = Path("/home/sandy050405/argus/veer/.veer-orchestration/osint/prototype")

POC_DIR = Path(os.environ.get(POC_DIR_ENV) or _DEFAULT_POC_DIR)
POC_SIGNALS = POC_DIR / "out" / "signals.raw.json"
POC_GAZETTEER = POC_DIR / "ahmedabad_gazetteer.json"
