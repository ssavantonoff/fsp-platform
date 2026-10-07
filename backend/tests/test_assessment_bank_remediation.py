import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

import pytest
from sqlalchemy import select

from app import question_bank
from app.assessment_validation import validate_source_bank
from app.models import AssessmentAttempt, AssessmentOption, AssessmentQuestion, User
from app.question_bank import SeedQuestion, load_bank
from app.seed import seed
from app.services import assessments

BASELINE_HASH = "7d2c7f2db8a7986d3027e250ac47786e700e4babf0c80e7c46ce6fce34442096"
B1_HASH = "079e40829c0ac41e8c893971f0b0d586ae7a071bf14d9d2a486466159ad4b30a"
REPLACEMENTS = (
    (
        "backend-junior-testing_security_debugging-5-v1",
        "backend-junior-testing_security_debugging-5-v2",
    ),
    ("backend-middle-programming-2-v1", "backend-middle-programming-2-v2"),
    ("backend-middle-programming-3-v1", "backend-middle-programming-3-v2"),
    ("backend-middle-programming-5-v1", "backend-middle-programming-5-v2"),
    ("backend-middle-http_api-2-v1", "backend-middle-http_api-2-v2"),
    ("backend-middle-http_api-3-v1", "backend-middle-http_api-3-v2"),
    ("backend-middle-http_api-4-v1", "backend-middle-http_api-4-v2"),
    ("backend-middle-databases-2-v1", "backend-middle-databases-2-v2"),
    ("backend-middle-databases-4-v1", "backend-middle-databases-4-v2"),
    ("backend-middle-architecture-3-v1", "backend-middle-architecture-3-v2"),
    (
        "backend-middle-testing_security_debugging-3-v1",
        "backend-middle-testing_security_debugging-3-v2",
    ),
    (
        "backend-middle-testing_security_debugging-4-v1",
        "backend-middle-testing_security_debugging-4-v2",
    ),
    ("backend-senior-programming-2-v1", "backend-senior-programming-2-v2"),
    ("backend-senior-programming-3-v1", "backend-senior-programming-3-v2"),
    ("backend-senior-programming-5-v1", "backend-senior-programming-5-v2"),
    ("backend-senior-http_api-1-v1", "backend-senior-http_api-1-v2"),
    ("backend-senior-http_api-2-v1", "backend-senior-http_api-2-v2"),
    ("backend-senior-http_api-3-v1", "backend-senior-http_api-3-v2"),
    ("backend-senior-http_api-4-v1", "backend-senior-http_api-4-v2"),
    ("backend-senior-http_api-5-v1", "backend-senior-http_api-5-v2"),
    ("backend-senior-databases-1-v1", "backend-senior-databases-1-v2"),
    ("backend-senior-databases-3-v1", "backend-senior-databases-3-v2"),
    ("backend-senior-databases-5-v1", "backend-senior-databases-5-v2"),
    ("backend-senior-architecture-4-v2", "backend-senior-architecture-4-v3"),
    (
        "backend-senior-testing_security_debugging-1-v1",
        "backend-senior-testing_security_debugging-1-v2",
    ),
    (
        "backend-senior-testing_security_debugging-4-v1",
        "backend-senior-testing_security_debugging-4-v2",
    ),
    (
        "backend-senior-testing_security_debugging-5-v1",
        "backend-senior-testing_security_debugging-5-v2",
    ),
)
MINOR_CODES = {
    "backend-junior-http_api-2-v1",
    "backend-junior-architecture-2-v1",
    "backend-junior-architecture-3-v1",
    "backend-junior-testing_security_debugging-3-v1",
    "backend-junior-testing_security_debugging-4-v1",
    "backend-senior-testing_security_debugging-3-v1",
}
SECOND_REPLACEMENTS = (
    ("backend-middle-http_api-5-v1", "backend-middle-http_api-5-v2"),
    ("backend-middle-databases-4-v2", "backend-middle-databases-4-v3"),
    (
        "backend-middle-testing_security_debugging-5-v1",
        "backend-middle-testing_security_debugging-5-v2",
    ),
    ("backend-senior-programming-4-v1", "backend-senior-programming-4-v2"),
    ("backend-senior-databases-2-v1", "backend-senior-databases-2-v2"),
    ("backend-senior-databases-4-v1", "backend-senior-databases-4-v2"),
    ("backend-senior-architecture-3-v1", "backend-senior-architecture-3-v2"),
    ("backend-senior-architecture-5-v1", "backend-senior-architecture-5-v2"),
    (
        "backend-senior-testing_security_debugging-2-v1",
        "backend-senior-testing_security_debugging-2-v2",
    ),
    (
        "backend-senior-testing_security_debugging-3-v1",
        "backend-senior-testing_security_debugging-3-v2",
    ),
)
SECOND_PASS_MINOR_CODES = {
    "backend-junior-http_api-2-v1",
    "backend-junior-architecture-2-v1",
    "backend-junior-architecture-3-v1",
    "backend-junior-testing_security_debugging-3-v1",
    "backend-junior-testing_security_debugging-4-v1",
    "backend-middle-programming-4-v1",
    "backend-middle-databases-3-v1",
    "backend-middle-databases-5-v1",
    "backend-middle-architecture-2-v1",
    "backend-middle-architecture-4-v1",
    "backend-middle-architecture-5-v1",
    "backend-middle-testing_security_debugging-2-v1",
    "backend-senior-architecture-2-v1",
}


def fingerprint(value):
    # Assertion output must not print real prompt/options or internal marking.
    return sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def frozen_bank(filename, expected_hash):
    content = (Path(__file__).parent / "fixtures" / filename).read_bytes()
    assert sha256(content).hexdigest() == expected_hash
    questions = [SeedQuestion.model_validate(q) for q in json.loads(content)]
    assert len(questions) == 75
    assert validate_source_bank(questions) == []
    return questions


@pytest.fixture
def baseline_bank():
    return frozen_bank("assessment-bank-pre-p3.json", BASELINE_HASH)


@pytest.fixture
def b1_bank():
    return frozen_bank("assessment-bank-p3-b1.json", B1_HASH)


@pytest.mark.parametrize("old,new", REPLACEMENTS, ids=[new for _, new in REPLACEMENTS])
def test_exact_replacement_and_frozen_metadata(baseline_bank, b1_bank, old, new):
    before = {q.code: q for q in baseline_bank}[old]
    current = {q.code: q for q in b1_bank}
    assert old not in current
    after = current[new]
    assert after.supersedes == old
    assert after.version == (3 if old.endswith("-v2") else 2)
    assert after.version == before.version + 1
    assert (after.grade, after.competency, after.difficulty) == (
        before.grade,
        before.competency,
        before.difficulty,
    )
    assert fingerprint(after.prompt) != fingerprint(before.prompt)
    assert fingerprint(after.options) != fingerprint(before.options)


def test_exact_inventory_and_48_unchanged_records(baseline_bank, b1_bank):
    current = b1_bank
    before = {q.code: q for q in baseline_bank}
    after = {q.code: q for q in current}
    old_codes = {old for old, _ in REPLACEMENTS}
    new_codes = {new for _, new in REPLACEMENTS}
    unchanged = set(before) - old_codes
    assert len(old_codes) == len(new_codes) == 27
    assert len(unchanged) == 48
    assert set(after) == unchanged | new_codes
    assert Counter(q.version for q in current) == {1: 47, 2: 27, 3: 1}
    assert Counter(q.grade for q in current) == {
        "JUNIOR": 25,
        "MIDDLE": 25,
        "SENIOR": 25,
    }
    assert Counter(before[old].grade for old in old_codes) == {
        "JUNIOR": 1,
        "MIDDLE": 11,
        "SENIOR": 15,
    }
    for code in unchanged:
        assert fingerprint(before[code].model_dump()) == fingerprint(
            after[code].model_dump()
        ), code
    assert len(MINOR_CODES) == 6 and MINOR_CODES <= unchanged
    for grade in ("JUNIOR", "MIDDLE", "SENIOR"):
        for competency in assessments.COMPETENCIES["BACKEND"]:
            assert Counter(
                q.difficulty
                for q in current
                if q.grade == grade and q.competency == competency
            ) == {"BASIC": 1, "APPLIED": 3, "ADVANCED": 1}
    assert validate_source_bank(current) == []


@pytest.mark.parametrize(
    "old,new", SECOND_REPLACEMENTS, ids=[new for _, new in SECOND_REPLACEMENTS]
)
def test_second_replacement_and_frozen_metadata(b1_bank, old, new):
    before = {q.code: q for q in b1_bank}[old]
    current = {q.code: q for q in load_bank()}
    assert old not in current
    after = current[new]
    assert after.supersedes == old
    assert after.version == (3 if old.endswith("-v2") else 2)
    assert after.version == before.version + 1
    assert (after.grade, after.competency, after.difficulty) == (
        before.grade,
        before.competency,
        before.difficulty,
    )
    assert fingerprint(after.prompt) != fingerprint(before.prompt)
    assert fingerprint(after.options) != fingerprint(before.options)


def test_second_inventory_and_65_unchanged_records(b1_bank):
    current = load_bank()
    before = {q.code: q for q in b1_bank}
    after = {q.code: q for q in current}
    old_codes = {old for old, _ in SECOND_REPLACEMENTS}
    new_codes = {new for _, new in SECOND_REPLACEMENTS}
    unchanged = set(before) - old_codes
    assert len(old_codes) == len(new_codes) == 10
    assert set(before) - set(after) == old_codes
    assert set(after) - set(before) == new_codes
    assert len(unchanged) == 65 and set(before).intersection(after) == unchanged
    assert len(current) == 75
    assert Counter(q.version for q in current) == {1: 38, 2: 35, 3: 2}
    assert Counter(q.grade for q in current) == {
        "JUNIOR": 25,
        "MIDDLE": 25,
        "SENIOR": 25,
    }
    assert Counter(before[old].grade for old in old_codes) == {
        "MIDDLE": 3,
        "SENIOR": 7,
    }
    clean_first_replacements = {new for _, new in REPLACEMENTS} - old_codes
    assert len(clean_first_replacements) == 26
    assert clean_first_replacements <= unchanged
    assert len(SECOND_PASS_MINOR_CODES) == 13
    assert SECOND_PASS_MINOR_CODES <= unchanged
    for code in unchanged:
        assert fingerprint(before[code].model_dump()) == fingerprint(
            after[code].model_dump()
        ), code
    for grade in ("JUNIOR", "MIDDLE", "SENIOR"):
        for competency in assessments.COMPETENCIES["BACKEND"]:
            assert Counter(
                q.difficulty
                for q in current
                if q.grade == grade and q.competency == competency
            ) == {"BASIC": 1, "APPLIED": 3, "ADVANCED": 1}
    assert validate_source_bank(current) == []


def question_snapshot(db):
    return {
        q.code: {
            "id": q.id,
            "active": q.is_active,
            "content": fingerprint(
                {
                    "specialization": q.specialization,
                    "grade": q.grade,
                    "competency": q.competency,
                    "difficulty": q.difficulty,
                    "prompt": q.prompt,
                    "version": q.version,
                    "created_at": q.created_at,
                    "options": sorted((o.id, o.text, o.is_correct) for o in q.options),
                }
            ),
        }
        for q in db.scalars(select(AssessmentQuestion))
    }


def seed_fixed_bank(db_factory, bank, monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(question_bank, "load_bank", lambda: bank)
        with db_factory() as db:
            seed(db)


def assert_current_active_bank(db, expected_bank=None):
    rows = list(
        db.scalars(
            select(AssessmentQuestion).where(AssessmentQuestion.is_active.is_(True))
        )
    )
    assert len(rows) == 75
    if expected_bank is None:
        expected_bank = load_bank()
    assert {q.code for q in rows} == {q.code for q in expected_bank}
    for grade in ("JUNIOR", "MIDDLE", "SENIOR"):
        assert sum(q.grade == grade for q in rows) == 25
        for competency in assessments.COMPETENCIES["BACKEND"]:
            assert Counter(
                q.difficulty
                for q in rows
                if q.grade == grade and q.competency == competency
            ) == {"BASIC": 1, "APPLIED": 3, "ADVANCED": 1}
        assert assessments.bank_available(
            rows_for_grade := [q for q in rows if q.grade == grade], "BACKEND"
        )
        assert len(rows_for_grade) == 25


def test_fresh_seed_and_repeat_are_idempotent(db_factory):
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        before = question_snapshot(db)
        assert len(before) == 75
        assert not {old for old, _ in REPLACEMENTS + SECOND_REPLACEMENTS}.intersection(
            before
        )
        assert len(list(db.scalars(select(AssessmentOption)))) == 300
        assert_current_active_bank(db)
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        assert question_snapshot(db) == before
        assert len(list(db.scalars(select(AssessmentOption)))) == 300


def test_baseline_upgrade_keeps_rows_options_ids_and_v2_history(
    db_factory, baseline_bank, b1_bank, monkeypatch
):
    seed_fixed_bank(db_factory, baseline_bank, monkeypatch)
    with db_factory() as db:
        before = question_snapshot(db)
        assert len(before) == 75 and all(item["active"] for item in before.values())
        options_before = {o.id for o in db.scalars(select(AssessmentOption))}
        assert before["backend-senior-architecture-4-v2"]["active"]
    seed_fixed_bank(db_factory, b1_bank, monkeypatch)
    with db_factory() as db:
        after = question_snapshot(db)
        assert len(after) == 102
        assert_current_active_bank(db, b1_bank)
        assert options_before <= {o.id for o in db.scalars(select(AssessmentOption))}
        assert len(list(db.scalars(select(AssessmentOption)))) == 408
        old_codes = {old for old, _ in REPLACEMENTS}
        for code, snapshot in before.items():
            assert after[code] == {**snapshot, "active": code not in old_codes}, code
        for old, new in REPLACEMENTS:
            assert not after[old]["active"] and after[new]["active"]
            assert after[old]["id"] != after[new]["id"]
        assert not after["backend-senior-architecture-4-v2"]["active"]
        assert after["backend-senior-architecture-4-v3"]["active"]
    seed_fixed_bank(db_factory, b1_bank, monkeypatch)
    with db_factory() as db:
        assert question_snapshot(db) == after


@pytest.mark.parametrize(
    "from_original", [False, True], ids=["b1-to-b2", "pre-p3-to-b1-to-b2"]
)
def test_second_upgrade_preserves_each_immediate_predecessor(
    db_factory, baseline_bank, b1_bank, monkeypatch, from_original
):
    if from_original:
        seed_fixed_bank(db_factory, baseline_bank, monkeypatch)
        with db_factory() as db:
            original = question_snapshot(db)
    seed_fixed_bank(db_factory, b1_bank, monkeypatch)
    with db_factory() as db:
        before = question_snapshot(db)
        assert len(before) == (102 if from_original else 75)
        assert_current_active_bank(db, b1_bank)
        options_before = {o.id for o in db.scalars(select(AssessmentOption))}
        assert before["backend-middle-databases-4-v2"]["active"]
        if from_original:
            first_old = {old for old, _ in REPLACEMENTS}
            for code, snapshot in original.items():
                assert before[code] == {
                    **snapshot,
                    "active": code not in first_old,
                }, code
            assert not before["backend-middle-databases-4-v1"]["active"]
            assert not before["backend-senior-architecture-4-v2"]["active"]
        assert before["backend-senior-architecture-4-v3"]["active"]
        for old, _ in SECOND_REPLACEMENTS:
            assert before[old]["active"], old
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        after = question_snapshot(db)
        assert len(after) == (112 if from_original else 85)
        assert_current_active_bank(db)
        assert set(after) == set(before) | {new for _, new in SECOND_REPLACEMENTS}
        assert options_before <= {o.id for o in db.scalars(select(AssessmentOption))}
        assert len(list(db.scalars(select(AssessmentOption)))) == len(after) * 4
        second_old = {old for old, _ in SECOND_REPLACEMENTS}
        for code, snapshot in before.items():
            assert after[code] == {
                **snapshot,
                "active": snapshot["active"] and code not in second_old,
            }, code
        for old, new in SECOND_REPLACEMENTS:
            assert not after[old]["active"] and after[new]["active"]
            assert after[old]["id"] != after[new]["id"]
        assert not after["backend-middle-databases-4-v2"]["active"]
        assert after["backend-middle-databases-4-v3"]["active"]
        if from_original:
            assert not after["backend-middle-databases-4-v1"]["active"]
            assert not after["backend-senior-architecture-4-v2"]["active"]
            for old, _ in REPLACEMENTS:
                assert not after[old]["active"], old
        assert after["backend-senior-architecture-4-v3"]["active"]
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        assert question_snapshot(db) == after


def test_repeat_preserves_deliberately_inactive_replacement(db_factory):
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        row = db.scalar(
            select(AssessmentQuestion).where(
                AssessmentQuestion.code == REPLACEMENTS[0][1]
            )
        )
        row.is_active = False
        db.commit()
        before = question_snapshot(db)
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        assert question_snapshot(db) == before


@pytest.mark.parametrize(
    "field", ["prompt", "options", "grade", "difficulty", "version"]
)
def test_same_code_content_mutation_still_fails_atomically(
    db_factory, monkeypatch, field
):
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        before = question_snapshot(db)
    questions = load_bank()
    item = questions[0]
    changes = {
        "prompt": "Synthetic changed prompt",
        "options": ["One", "Two", "Three", "Four"],
        "grade": "MIDDLE",
        "difficulty": "ADVANCED",
        "version": item.version + 1,
    }
    questions[0] = item.model_copy(update={field: changes[field]})
    monkeypatch.setattr(question_bank, "load_bank", lambda: questions)
    with (
        db_factory() as db,
        pytest.raises(ValueError, match="Immutable question changed"),
    ):
        seed(db)
    with db_factory() as db:
        assert question_snapshot(db) == before


class HistoricalSelection:
    def __init__(self, replacements):
        self.old_codes = {old for old, _ in replacements}

    def sample(self, population, k):
        return sorted(population, key=lambda q: (q.code not in self.old_codes, q.code))[
            :k
        ]

    def shuffle(self, values):
        values.reverse()


def attempt_snapshot(row):
    return fingerprint(
        [
            {
                "attempt_question_id": item.id,
                "question_id": item.question_id,
                "code": item.question.code,
                "position": item.position,
                "option_order": item.option_order,
                "selected": item.selected_option_id,
                "answered_at": item.answered_at,
            }
            for item in row.questions
        ]
    )


@pytest.mark.parametrize(
    "stage,grade",
    [
        ("first", "JUNIOR"),
        ("first", "MIDDLE"),
        ("first", "SENIOR"),
        ("second", "MIDDLE"),
        ("second", "SENIOR"),
    ],
)
@pytest.mark.parametrize(
    "finished", [False, True], ids=["active-spanning-seed", "historical-finished"]
)
def test_attempt_keeps_historical_membership_order_read_and_scoring(
    client,
    account,
    candidate_data,
    db_factory,
    baseline_bank,
    b1_bank,
    monkeypatch,
    stage,
    grade,
    finished,
):
    user = account()
    assert client.post("/candidate/profile", json=candidate_data).status_code == 201
    initial_bank = baseline_bank if stage == "first" else b1_bank
    replacements = REPLACEMENTS if stage == "first" else SECOND_REPLACEMENTS
    seed_fixed_bank(db_factory, initial_bank, monkeypatch)
    with db_factory() as db:
        db.get(User, user["id"]).email_verified = True
        db.commit()
    monkeypatch.setattr(
        assessments.random, "SystemRandom", lambda: HistoricalSelection(replacements)
    )
    response = client.post("/candidate/assessments", json={"target_grade": grade})
    assert response.status_code == 201
    attempt = response.json()
    path = f"/candidate/assessments/{attempt['id']}"
    with db_factory() as db:
        row = db.get(AssessmentAttempt, attempt["id"])
        old_codes = {item.question.code for item in row.questions}
        assert old_codes.intersection(old for old, _ in replacements)
        if stage == "second":
            assert {
                old for old, _ in replacements if f"-{grade.lower()}-" in old
            } <= old_codes
        if stage == "first" and grade == "SENIOR":
            assert "backend-senior-architecture-4-v2" in old_codes
        if grade == "MIDDLE":
            assert f"backend-middle-databases-4-v{1 if stage == 'first' else 2}" in (
                old_codes
            )
        for item in row.questions:
            item.selected_option_id = next(
                o.id for o in item.question.options if o.is_correct
            )
        db.commit()
    if finished:
        result = client.post(path + "/submit").json()
        assert (
            result["status"] == "PASSED"
            and result["normalized_assessment_score"] == 100
        )
    before_api = client.get(path).json()
    with db_factory() as db:
        before_attempt = attempt_snapshot(db.get(AssessmentAttempt, attempt["id"]))
        before_questions = question_snapshot(db)
    upgrades = [b1_bank, load_bank()] if stage == "first" else [load_bank()]
    for bank in upgrades:
        seed_fixed_bank(db_factory, bank, monkeypatch)
        with db_factory() as db:
            row = db.get(AssessmentAttempt, attempt["id"])
            assert attempt_snapshot(row) == before_attempt
            after_questions = question_snapshot(db)
            for code in old_codes:
                assert after_questions[code]["id"] == before_questions[code]["id"]
                assert (
                    after_questions[code]["content"]
                    == before_questions[code]["content"]
                )
            assert_current_active_bank(db, bank)
        after_api = client.get(path).json()
        assert fingerprint(
            {k: v for k, v in after_api.items() if k != "server_now"}
        ) == fingerprint({k: v for k, v in before_api.items() if k != "server_now"})
    result = client.post(path + "/submit").json()
    assert result["status"] == "PASSED"
    assert result["normalized_assessment_score"] == 100
    assert result["competency_scores"] == {
        "PROGRAMMING": 100,
        "HTTP_API": 100,
        "DATABASES": 100,
        "ARCHITECTURE": 100,
        "TESTING_SECURITY_DEBUGGING": 100,
    }
    assert result["questions"] == []
    assert result["verification"]["verified_grade"] == grade
    if finished:
        assert result["finished_at"] == before_api["finished_at"]
    with db_factory() as db:
        assert (
            attempt_snapshot(db.get(AssessmentAttempt, attempt["id"])) == before_attempt
        )
