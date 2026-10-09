"""Stage 1 coverage, projection, CSV and preservation; no application imports."""

import copy
import csv
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "backend/prepare_matching_v2_review.py"
REVIEW = ROOT / "docs/validation/review"
INPUT = REVIEW / "matching-v2-human-review-input-v1.csv"
TEMPLATE = REVIEW / "matching-v2-human-review-template-v1.csv"
DATASET = ROOT / "docs/validation/matching-v2-dataset-v1.json"
PROPOSED = ROOT / "docs/validation/matching-v2-golden-proposed-v1.json"
INPUT_FIELDS = [
    "need_id",
    "position_title",
    "need_specialization",
    "required_grade",
    "must_have_skills",
    "nice_to_have_skills",
    "target_experience_years",
    "description",
    "catalog_proxy",
    "catalog_limitation",
    "candidate_id",
    "candidate_specialization",
    "verified_grade",
    "normalized_assessment_score",
    "skills",
    "years_of_experience",
]
TEMPLATE_FIELDS = [
    "need_id",
    "candidate_id",
    "reviewer_grade",
    "reviewer_rationale",
    "reviewer_uncertainty",
]
EXPECTED = {
    "N1": ["C01", "C02", "C03", "C04"],
    "N2": ["C05", "C06", "C07", "C08", "C10"],
    "N3": ["C08", "C09", "C10"],
    "N4": ["C13", "C14", "C16", "C17", "C18", "C19", "C21"],
    "N5": ["C16", "C17", "C18", "C20", "C22", "C24"],
    "N6": ["C20", "C22", "C24"],
    "N7": ["C25", "C26", "C28", "C29", "C30", "C32", "C35"],
    "N8": ["C29", "C30", "C35"],
}


def test_stage1_review_deliverables_exist():
    assert SCRIPT.is_file(), "Stage 1 preparation script is required"
    assert INPUT.is_file() and TEMPLATE.is_file()
    assert (REVIEW / "matching-v2-human-review-guide.md").is_file()


@pytest.fixture
def preparation():
    spec = importlib.util.spec_from_file_location("review_preparation", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(value):
    reader = csv.DictReader(io.StringIO(value.decode("utf-8"), newline=""))
    return reader.fieldnames, list(reader)


def test_exact_38_pairs_allowlisted_evidence_and_empty_reviewer_fields(preparation):
    dataset = preparation.load_frozen()
    before = {p: p.read_bytes() for p in (DATASET, PROPOSED)}
    package = preparation.build_package(dataset)
    headers, rows = read_csv(package[INPUT.name])
    template_headers, blanks = read_csv(package[TEMPLATE.name])
    expected_pairs = [(nid, cid) for nid, ids in EXPECTED.items() for cid in ids]
    assert headers == INPUT_FIELDS
    assert template_headers == TEMPLATE_FIELDS
    assert [(r["need_id"], r["candidate_id"]) for r in rows] == expected_pairs
    assert [(r["need_id"], r["candidate_id"]) for r in blanks] == expected_pairs
    assert len(rows) == len(blanks) == len(set(expected_pairs)) == 38
    needs = {n["id"]: n for n in dataset["needs"]}
    candidates = {c["id"]: c for c in dataset["candidates"]}
    for row in rows:
        n, c = needs[row["need_id"]], candidates[row["candidate_id"]]
        assert row["position_title"] == n["position_title"]
        assert row["need_specialization"] == n["specialization"]
        assert row["required_grade"] == n["required_grade"]
        assert json.loads(row["must_have_skills"]) == n["must_have_skills"]
        assert json.loads(row["nice_to_have_skills"]) == n["nice_to_have_skills"]
        assert row["target_experience_years"] == str(n["target_experience_years"])
        assert row["description"] == n["description"]
        assert row["catalog_proxy"] == (
            "CATALOG_PROXY" if n["id"] in {"N3", "N5", "N7", "N8"} else ""
        )
        assert row["catalog_limitation"] == (n["limitation"] or "")
        assert row["candidate_specialization"] == c["specialization"]
        assert row["verified_grade"] == c["verified_grade"]
        assert row["normalized_assessment_score"] == str(
            c["normalized_assessment_score"]
        )
        assert json.loads(row["skills"]) == c["self_declared_skills"]
        assert row["years_of_experience"] == (
            "" if c["years_of_experience"] is None else str(c["years_of_experience"])
        )
    assert all(r[k] == "" for r in blanks for k in TEMPLATE_FIELDS[2:])
    assert {p: p.read_bytes() for p in before} == before
    assert read_csv(INPUT.read_bytes()) == read_csv(package[INPUT.name])
    assert read_csv(TEMPLATE.read_bytes()) == read_csv(package[TEMPLATE.name])


def test_hidden_candidate_fields_never_influence_or_leak_into_projection(preparation):
    dataset = preparation.load_frozen()
    original = preparation.build_package(dataset)
    poisoned = copy.deepcopy(dataset)
    for candidate in poisoned["candidates"]:
        candidate.update(
            {
                "declared_grade": "HIDDEN_DECLARED",
                "fsp": {"achievements": ["HIDDEN_FSP"], "fsp_id": "PRIVATE_FSP"},
                "email": "PRIVATE_EMAIL_SENTINEL",
                "full_name": "PRIVATE_NAME_SENTINEL",
                "contacts": "PRIVATE_CONTACT_SENTINEL",
                "user_id": "PRIVATE_USER_SENTINEL",
                "relevance_grade": 0,
                "rationale": "HIDDEN_AI_RATIONALE",
                "professional_fit": 999,
                "ranking_score": 999,
            }
        )
    assert preparation.build_package(poisoned) == original
    assert b"SENTINEL" not in b"".join(original.values())


def test_reordered_source_records_produce_same_neutral_id_order(preparation):
    dataset = preparation.load_frozen()
    original = preparation.build_package(dataset)
    dataset["needs"].reverse()
    dataset["candidates"].reverse()
    assert preparation.build_package(dataset) == original


def test_csv_roundtrip_preserves_commas_quotes_cyrillic_and_multiline(preparation):
    dataset = preparation.load_frozen()
    description = 'Описание, с "кавычками"\nвторая строка\r\nтретья строка'
    dataset["needs"][0]["description"] = description
    package = preparation.build_package(dataset)
    _, rows = read_csv(package[INPUT.name])
    assert all(r["description"] == description for r in rows if r["need_id"] == "N1")
    assert not package[INPUT.name].startswith(b"\xef\xbb\xbf")


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@", "\t=", "\n@"])
def test_csv_refuses_spreadsheet_formula_cells_without_altering_content(
    preparation,
    prefix,
):
    dataset = preparation.load_frozen()
    dataset["needs"][0]["description"] = prefix + "unsafe_formula"
    with pytest.raises(ValueError, match="formula"):
        preparation.build_package(dataset)


@pytest.mark.parametrize("field", ["needs", "candidates"])
def test_missing_or_duplicate_source_ids_stop_generation(preparation, field):
    dataset = preparation.load_frozen()
    dataset[field][-1] = copy.deepcopy(dataset[field][0])
    with pytest.raises(ValueError, match="IDs"):
        preparation.build_package(dataset)


def test_structural_reference_drift_stops_generation(preparation):
    dataset = preparation.load_frozen()
    dataset["candidates"][0]["personal_data_consent"] = False
    with pytest.raises(ValueError, match="Structural"):
        preparation.build_package(dataset)


@pytest.mark.parametrize("changed_source", ["dataset", "proposed"])
def test_frozen_hash_change_stops_before_output(preparation, tmp_path, changed_source):
    dataset, proposed = tmp_path / "dataset.json", tmp_path / "proposed.json"
    dataset.write_bytes(DATASET.read_bytes())
    proposed.write_bytes(PROPOSED.read_bytes())
    selected = dataset if changed_source == "dataset" else proposed
    selected.write_bytes(selected.read_bytes() + b" ")
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        preparation.load_frozen(dataset, proposed)


def test_proposed_bytes_are_hash_checked_without_parsing_labels(
    preparation, monkeypatch
):
    real_loads = preparation.json.loads
    parsed = []

    def capture(value):
        parsed.append(value)
        return real_loads(value)

    monkeypatch.setattr(preparation.json, "loads", capture)
    preparation.load_frozen()
    assert parsed == [DATASET.read_bytes()]


def test_idempotence_and_refusal_to_overwrite_completed_review(preparation, tmp_path):
    package = preparation.build_package(preparation.load_frozen())
    preparation.write_package(tmp_path, package)
    before = {name: (tmp_path / name).read_bytes() for name in package}
    preparation.write_package(tmp_path, package)
    assert {name: (tmp_path / name).read_bytes() for name in package} == before
    completed = tmp_path / TEMPLATE.name
    completed.write_bytes(completed.read_bytes().replace(b'""', b'"human text"', 1))
    edited = completed.read_bytes()
    with pytest.raises(ValueError, match="overwrite"):
        preparation.write_package(tmp_path, package)
    assert completed.read_bytes() == edited
    assert (tmp_path / INPUT.name).read_bytes() == before[INPUT.name]


def test_output_preflight_avoids_partial_write_when_review_exists(
    preparation, tmp_path
):
    package = preparation.build_package(preparation.load_frozen())
    (tmp_path / TEMPLATE.name).write_bytes(b"human review must survive")
    with pytest.raises(ValueError, match="overwrite"):
        preparation.write_package(tmp_path, package)
    assert not (tmp_path / INPUT.name).exists()


def test_csv_record_lineendings_are_equivalent_without_rewriting(preparation, tmp_path):
    package = preparation.build_package(preparation.load_frozen())
    for name, content in package.items():
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
        writer.writerows(csv.reader(io.StringIO(content.decode("utf-8"), newline="")))
        (tmp_path / name).write_bytes(buffer.getvalue().encode("utf-8"))
    before = {name: (tmp_path / name).read_bytes() for name in package}
    preparation.check_package(tmp_path, package)
    preparation.write_package(tmp_path, package)
    assert {name: (tmp_path / name).read_bytes() for name in package} == before


def test_embedded_cell_newline_change_is_not_record_lineending_equivalence(
    preparation,
    tmp_path,
):
    dataset = preparation.load_frozen()
    dataset["needs"][0]["description"] = "first\nsecond"
    package = preparation.build_package(dataset)
    preparation.write_package(tmp_path, package)
    altered = (
        (tmp_path / INPUT.name)
        .read_bytes()
        .replace(b"first\nsecond", b"first\r\nsecond")
    )
    (tmp_path / INPUT.name).write_bytes(altered)
    with pytest.raises(ValueError):
        preparation.check_package(tmp_path, package)
    with pytest.raises(ValueError, match="overwrite"):
        preparation.write_package(tmp_path, package)
    assert (tmp_path / INPUT.name).read_bytes() == altered


def test_writer_rejects_arbitrary_names_and_protected_output(preparation, tmp_path):
    with pytest.raises(ValueError):
        preparation.write_package(tmp_path, {"../protected.json": b"unsafe"})
    with pytest.raises(ValueError, match="output"):
        preparation.check_output_directory(ROOT / ".git")
    with pytest.raises(ValueError, match="output"):
        preparation.check_output_directory(ROOT / "backend")


def test_cli_determinism_frozen_preservation_and_no_production_imports(preparation):
    before = {p: p.read_bytes() for p in (DATASET, PROPOSED)}
    command = [sys.executable, str(SCRIPT), "--check"]
    runs = [subprocess.run(command, capture_output=True, timeout=30) for _ in range(2)]
    assert all(r.returncode == 0 for r in runs), runs[0].stderr
    assert runs[0].stdout == runs[1].stdout
    assert b"38 eligible pairs" in runs[0].stdout
    assert {p: p.read_bytes() for p in before} == before
    # Full repository pytest may already load app through unrelated conftest.
    # Check this script's imports in a clean interpreter, not the parent session.
    import_check = subprocess.run(
        [
            sys.executable,
            "-c",
            "import runpy,sys; runpy.run_path(sys.argv[1]); "
            "assert not any(k == 'app' or k.startswith('app.') for k in sys.modules)",
            str(SCRIPT),
        ],
        capture_output=True,
        timeout=30,
    )
    assert import_check.returncode == 0, import_check.stderr
    assert hashlib.sha256(before[DATASET]).hexdigest() == (
        "ef362631fc3104c50f29bca301b1fc9368b74a3a1ae95d2c0ba1e491ced0add5"
    )
    assert hashlib.sha256(before[PROPOSED]).hexdigest() == (
        "111e1a06f2a57e6c1194ce1dd5cf75e3f275cefda38de662d0bb7a0b2d6dd6ed"
    )
