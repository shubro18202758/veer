# osint-ingress test fixtures: provenance

Plan R13: only public-domain official samples (NDMA SACHET CAP) are committed verbatim. Google News, Reddit and
GDELT fixtures are synthetic replicas with fictional publishers (`*.example`) and fictional names, labelled
synthetic. The real PoC captures (`.veer-orchestration/osint/prototype/out/`) are read in place by the tests that
need them (they skip when the directory is absent, as in CI) and are never copied here. No real person's name
appears in any fixture; `tests/test_pii_redaction.py` scans every file of this package for the PoC's names in
memory and reports only SHA-256 prefixes.

| path | provenance | purpose |
|---|---|---|
| `capture/` | 1 **real** public-domain file + 5 **synthetic** | The sandbox seed, laid out like a PoC raw capture directory. Per-file provenance in [`capture/README.md`](capture/README.md). |
| `build_synthetic_gdelt.py` | script | Rebuilds the synthetic GDELT export zip and `lastupdate.txt` in `capture/` deterministically; `--check` compares. |
| `hostile/xxe.xml` | **synthetic**, hostile | An RSS document with an external entity reading a local file (XXE). `defusedxml` must refuse it. |
| `hostile/billion_laughs.xml` | **synthetic**, hostile | Exponential entity expansion ("billion laughs"). `defusedxml` must refuse it. |
| `hostile/external_dtd.xml` | **synthetic**, hostile | A DOCTYPE that points at a remote DTD. Refused (`forbid_dtd`). |
| `hostile/xxe_atom.rss` | **synthetic**, hostile | An Atom feed with an external parameter entity. Refused. |
| `pages/amc_home.html` | **synthetic** | A municipal home page replica: notice links (kept), navigation, script-injected, external, image and mail links (ignored), and a fictional officer name (redacted). |
| `pages/sachet_rss_synthetic.xml` | **synthetic** | A SACHET CAP RSS replica with fictional identifiers (`1999...`) for the CAP-detail fetch test. |
| `pages/cap_detail_synthetic.xml` | **synthetic** | A CAP 1.2 alert replica (fictional identifier, LGD codes, contact and note), for the CAP-detail parser; its `contact` and `note` must never be read. |

Common Crawl CDX lines and WARC records, robots.txt files and oracle answers are built inside the tests.
