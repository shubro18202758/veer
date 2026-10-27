"""GDELT ADM1 for Gujarat is the FIPS 10-4 code ``IN09`` (plan R28), verified on the PoC's own capture; and the
bulk parser reads only the export that ``lastupdate.txt`` names."""

from __future__ import annotations

import csv
import io
import shutil
import zipfile
from pathlib import Path

import pytest
from conftest import CAPTURE, POC_RAW, needs_poc

from osint_common.kinds import GDELT_ADM1_GUJARAT
from osint_ingress.cache import Cache
from osint_ingress.connectors.base import GUJARAT_BBOX
from osint_ingress.connectors.gdelt import EVENT_COLUMNS, GdeltBulk
from osint_ingress.importer import import_capture

POC_2315 = POC_RAW / "20261023231500.export.CSV.zip"


def _rows(path: Path):
    with zipfile.ZipFile(path) as zf, zf.open(zf.namelist()[0]) as fh:
        yield from csv.reader(io.TextIOWrapper(fh, encoding="utf-8", errors="replace", newline=""),
                              delimiter="\t", quoting=csv.QUOTE_NONE)


@pytest.mark.skipif(not POC_2315.is_file(), reason="PoC capture 20261023231500.export.CSV.zip absent (CI)")
def test_every_gujarat_bbox_row_of_the_poc_capture_carries_in09():
    lat_i, lon_i, adm_i = (EVENT_COLUMNS[k] for k in ("action_geo_lat", "action_geo_long", "action_geo_adm1_code"))
    inside = []
    for row in _rows(POC_2315):
        if len(row) != 61 or not row[lat_i] or not row[lon_i]:
            continue
        lat, lon = float(row[lat_i]), float(row[lon_i])
        if GUJARAT_BBOX[0] <= lat <= GUJARAT_BBOX[1] and GUJARAT_BBOX[2] <= lon <= GUJARAT_BBOX[3]:
            inside.append(row[adm_i])
    assert len(inside) == 6 and set(inside) == {"IN09"}
    assert GDELT_ADM1_GUJARAT == "IN09"


def test_in32_daman_and_diu_is_never_used_in_the_source():
    src = Path(__file__).resolve().parents[1] / "src"
    for p in src.rglob("*.py"):
        assert "IN32" not in p.read_text(encoding="utf-8"), p


def _extra_export(name: str) -> bytes:
    """A second export zip with a Gujarat row: present in the cache, but NOT named by lastupdate.txt."""
    row = [""] * 61
    row[0], row[26], row[28], row[51], row[52], row[53], row[54], row[56], row[57], row[59] = (
        "1399999999", "190", "19", "4", "Ahmedabad, Gujarat, India", "IN", "IN09", "23.03", "72.58",
        "20261020114500")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(name.removesuffix(".zip"), "\t".join(row) + "\n")
    return buf.getvalue()


def test_bulk_parser_reads_only_the_export_lastupdate_names(tmp_path, protect):
    src = tmp_path / "capture"
    shutil.copytree(CAPTURE, src)
    (src / "20261020114500.export.CSV.zip").write_bytes(_extra_export("20261020114500.export.CSV.zip"))
    import_capture(src, tmp_path / "cache")
    entry = Cache(tmp_path / "cache").latest("gdelt_events")
    assert entry.blobs == ("20261020120000.export.CSV.zip",)
    ids = {s.source_id for s in GdeltBulk().parse(entry, protect)}
    assert ids == {"1300000001", "1300000002"} and "1399999999" not in ids


@needs_poc
def test_poc_lastupdate_names_the_2330_export_with_no_gujarat_row(tmp_path, protect):
    """The PoC's lastupdate.txt names 23:30, which has no Gujarat row; the 23:15 slice (6 rows) is ignored."""
    import_capture(POC_RAW, tmp_path / "cache")
    entry = Cache(tmp_path / "cache").latest("gdelt_events")
    assert entry.blobs == ("20261023233000.export.CSV.zip",)
    assert GdeltBulk().parse(entry, protect) == []
