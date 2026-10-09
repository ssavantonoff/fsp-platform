"""Stage 1 blind human-review CSV preparation, never scoring or human grading."""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "docs/validation/matching-v2-dataset-v1.json"
PROPOSED = ROOT / "docs/validation/matching-v2-golden-proposed-v1.json"
OUTPUT = ROOT / "docs/validation/review"
DATASET_HASH = "ef362631fc3104c50f29bca301b1fc9368b74a3a1ae95d2c0ba1e491ced0add5"
PROPOSED_HASH = "111e1a06f2a57e6c1194ce1dd5cf75e3f275cefda38de662d0bb7a0b2d6dd6ed"
INPUT_NAME = "matching-v2-human-review-input-v1.csv"
TEMPLATE_NAME = "matching-v2-human-review-template-v1.csv"
INPUT_FIELDS = (
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
)
TEMPLATE_FIELDS = (
    "need_id",
    "candidate_id",
    "reviewer_grade",
    "reviewer_rationale",
    "reviewer_uncertainty",
)
COUNTS = {"N1": 4, "N2": 5, "N3": 3, "N4": 7, "N5": 6, "N6": 3, "N7": 7, "N8": 3}
COMPATIBLE = {
    "JUNIOR": {"JUNIOR", "MIDDLE"},
    "MIDDLE": {"MIDDLE", "SENIOR"},
    "SENIOR": {"SENIOR"},
}
PROXIES = {"N3", "N5", "N7", "N8"}


def load_frozen(dataset: Path = DATASET, proposed: Path = PROPOSED) -> dict[str, Any]:
    """Hash both byte streams; only dataset is parsed. No AI label access."""
    frozen = dataset.read_bytes()
    if hashlib.sha256(frozen).hexdigest() != DATASET_HASH:
        raise ValueError("Dataset SHA256 mismatch: STOP")
    if hashlib.sha256(proposed.read_bytes()).hexdigest() != PROPOSED_HASH:
        raise ValueError("Proposed labels SHA256 mismatch: STOP")
    data = json.loads(frozen)
    if not isinstance(data, dict) or data.get("name") != "matching-v2-validation-v1":
        raise ValueError("Frozen dataset namespace mismatch")
    return data


def eligible(need: dict[str, Any], candidate: dict[str, Any]) -> bool:
    """Independent structural admission only; never production Matching."""
    return (
        candidate["personal_data_consent"] is True
        and candidate["specialization"] == need["specialization"]
        and all(
            candidate[key] is not None
            for key in (
                "verified_grade",
                "normalized_assessment_score",
                "assessment_verified_at",
            )
        )
        and candidate["verified_grade"] in COMPATIBLE[need["required_grade"]]
        and set(need["must_have_skills"]) <= set(candidate["self_declared_skills"])
    )


def scalar(value: Any) -> str:
    return "" if value is None else str(value)


def skill_list(value: list[str]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def csv_bytes(fields: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    """UTF-8, LF, quoted fields; roundtrips embedded commas/quotes/CR/newlines."""
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=fields,
        quoting=csv.QUOTE_ALL,
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    for row in rows:
        if set(row) != set(fields):
            raise ValueError("CSV schema mismatch")
        if any(
            value.lstrip().startswith(("=", "+", "-", "@")) for value in row.values()
        ):
            raise ValueError("Spreadsheet formula prefix in source cell: STOP")
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def build_package(dataset: dict[str, Any]) -> dict[str, bytes]:
    """Project caller-verified frozen data onto exact reviewer-visible allowlists."""
    needs, candidates = dataset["needs"], dataset["candidates"]
    if len(needs) != 8 or {n["id"] for n in needs} != set(COUNTS):
        raise ValueError("Need IDs/count mismatch: STOP")
    if len(candidates) != 36 or {c["id"] for c in candidates} != {
        f"C{i:02}" for i in range(1, 37)
    }:
        raise ValueError("Candidate IDs/count mismatch: STOP")
    rows: list[dict[str, str]] = []
    blanks: list[dict[str, str]] = []
    counts = dict.fromkeys(COUNTS, 0)
    for need in sorted(needs, key=lambda item: item["id"]):
        for candidate in sorted(candidates, key=lambda item: item["id"]):
            if not eligible(need, candidate):
                continue
            nid, cid = need["id"], candidate["id"]
            counts[nid] += 1
            rows.append(
                {
                    "need_id": nid,
                    "position_title": need["position_title"],
                    "need_specialization": need["specialization"],
                    "required_grade": need["required_grade"],
                    "must_have_skills": skill_list(need["must_have_skills"]),
                    "nice_to_have_skills": skill_list(need["nice_to_have_skills"]),
                    "target_experience_years": scalar(need["target_experience_years"]),
                    "description": need["description"],
                    "catalog_proxy": "CATALOG_PROXY" if nid in PROXIES else "",
                    "catalog_limitation": need["limitation"] or "",
                    "candidate_id": cid,
                    "candidate_specialization": candidate["specialization"],
                    "verified_grade": candidate["verified_grade"],
                    "normalized_assessment_score": scalar(
                        candidate["normalized_assessment_score"]
                    ),
                    "skills": skill_list(candidate["self_declared_skills"]),
                    "years_of_experience": scalar(candidate["years_of_experience"]),
                }
            )
            blanks.append(
                {
                    "need_id": nid,
                    "candidate_id": cid,
                    "reviewer_grade": "",
                    "reviewer_rationale": "",
                    "reviewer_uncertainty": "",
                }
            )
    if counts != COUNTS or len(rows) != 38:
        raise ValueError("Structural reference mismatch: STOP")
    return {
        INPUT_NAME: csv_bytes(INPUT_FIELDS, rows),
        TEMPLATE_NAME: csv_bytes(TEMPLATE_FIELDS, blanks),
    }


def check_output_directory(directory: Path) -> Path:
    resolved = directory.resolve()
    if resolved != OUTPUT or not resolved.is_relative_to(ROOT):
        if not resolved.is_relative_to(ROOT / ".cache"):
            raise ValueError("Unsafe output directory: use review directory or .cache")
    return resolved


def same_csv(left: bytes, right: bytes) -> bool:
    """Compare exact cells/rows, allowing record LF/CRLF without rewriting bytes."""
    try:
        left_rows = csv.reader(
            io.StringIO(left.decode("utf-8"), newline=""), strict=True
        )
        right_rows = csv.reader(
            io.StringIO(right.decode("utf-8"), newline=""), strict=True
        )
        return list(left_rows) == list(right_rows)
    except (UnicodeDecodeError, csv.Error):
        return False


def write_package(directory: Path, package: dict[str, bytes]) -> None:
    """Create two fixed filenames; never replace different or filled-in CSVs."""
    if set(package) != {INPUT_NAME, TEMPLATE_NAME}:
        raise ValueError("Only the two Stage 1 CSV filenames may be written")
    directory = directory.resolve()
    targets = {name: directory / name for name in package}
    for name, path in targets.items():
        if path.is_symlink() or path.resolve().parent != directory:
            raise ValueError("Symlink output target refused")
        if path.exists() and (
            not path.is_file() or not same_csv(path.read_bytes(), package[name])
        ):
            raise ValueError(f"Refusing to overwrite existing review: {name}")
    directory.mkdir(parents=True, exist_ok=True)
    for name, path in targets.items():
        if not path.exists():
            with path.open("xb") as stream:
                stream.write(package[name])


def check_package(directory: Path, package: dict[str, bytes]) -> None:
    for name, expected in package.items():
        path = directory / name
        if (
            path.is_symlink()
            or not path.is_file()
            or not same_csv(path.read_bytes(), expected)
        ):
            raise ValueError(f"Review package differs from frozen projection: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--proposed", type=Path, default=PROPOSED)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true", help="Verify files; no writes")
    args = parser.parse_args()
    dataset = load_frozen(args.dataset, args.proposed)
    package = build_package(dataset)
    directory = check_output_directory(args.output_dir)
    if args.check:
        check_package(directory, package)
    else:
        write_package(directory, package)
    print("PASS: both frozen SHA256; 38 eligible pairs; 250 excluded; neutral ID order")
    print("PASS: allowed professional fields only; all human reviewer fields blank")
    for name in package:
        digest = hashlib.sha256((directory / name).read_bytes()).hexdigest()
        print(f"{name} SHA256: {digest}")
    print("Human review NOT performed. Stage 2/production ranking NOT executed.")


if __name__ == "__main__":
    main()
