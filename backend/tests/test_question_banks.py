import json
from collections import Counter
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from traceback import format_exception

import pytest
from sqlalchemy import select
from test_assessment_bank_remediation import attempt_snapshot, question_snapshot

from app import question_bank
from app.assessment_bank_config import (
    COMPETENCIES,
    EXPANDED_BLUEPRINT,
    LEGACY_BACKEND_BLUEPRINT,
    SourceBlueprint,
)
from app.assessment_validation import (
    AssessmentValidationCategory as Category,
)
from app.assessment_validation import validate_source_bank, validate_source_banks
from app.models import AssessmentAttempt, AssessmentQuestion, Difficulty, Grade
from app.models import Specialization as Spec
from app.question_bank import BankSource, SeedQuestion, load_bank, load_banks
from app.seed import seed
from app.services import assessments

BASE = "/candidate/assessments"
BACKEND_HASH = "76cda12d6358f14da84cce0ac584035ab189ae7a2f43e18d1e3cfed41276023c"


def synthetic_bank(specialization):
    return [
        SeedQuestion(
            code=f"test-{specialization.lower()}-{grade.lower()}-{competency}-{i}-v1",
            version=1,
            grade=grade,
            competency=competency,
            difficulty=difficulty,
            prompt="Synthetic infrastructure fixture, not reviewed content.",
            options=[
                "Synthetic Alpha",
                "Synthetic Beta",
                "Synthetic Gamma",
                "Synthetic Delta",
            ],
        )
        for grade in Grade
        for competency in COMPETENCIES[specialization]
        for difficulty, count in EXPANDED_BLUEPRINT.mix.items()
        for i in range(
            {Difficulty.BASIC: 0, Difficulty.APPLIED: 2, Difficulty.ADVANCED: 8}[
                difficulty
            ],
            {Difficulty.BASIC: 0, Difficulty.APPLIED: 2, Difficulty.ADVANCED: 8}[
                difficulty
            ]
            + count,
        )
    ]


@pytest.fixture
def source_registry(tmp_path, monkeypatch):
    content = tmp_path / "content"
    content.mkdir()
    monkeypatch.setattr(question_bank, "__file__", str(tmp_path / "question_bank.py"))

    def install(banks, *, published=None, blueprints=None):
        sources = []
        for specialization, questions in banks.items():
            filename = f"{specialization.lower()}_questions.json"
            raw = json.dumps([q.model_dump(mode="json") for q in questions]).encode()
            (content / filename).write_bytes(raw)
            approved = published is None or specialization in published
            sources.append(
                BankSource(
                    specialization,
                    filename,
                    (blueprints or {}).get(specialization, EXPANDED_BLUEPRINT),
                    sha256(raw).hexdigest() if approved else None,
                    "TEST_FIXTURE_ONLY: not a professional content approval"
                    if approved
                    else None,
                )
            )
        monkeypatch.setattr(question_bank, "BANK_SOURCES", tuple(sources))
        return tuple(sources)

    return install


@pytest.fixture
def original_backend():
    raw = (
        Path(__file__).parents[1] / "app/content/backend_questions.json"
    ).read_bytes()
    assert sha256(raw).hexdigest() == BACKEND_HASH
    return [SeedQuestion.model_validate(q) for q in json.loads(raw)]


def setup_candidate(client, account, app, candidate_data, specialization):
    user = account()
    token = app.state.mailer.tokens[user["email"]]
    assert client.post("/auth/verify-email", json={"token": token}).status_code == 204
    response = client.post(
        "/candidate/profile",
        json={
            **candidate_data,
            "specialization": specialization,
            "declared_grade": "SENIOR",
        },
    )
    assert response.status_code == 201
    return response.json()


def start(client, grade):
    response = client.post(BASE, json={"target_grade": grade})
    assert response.status_code == 201
    return response.json()


def submit(client, attempt):
    response = client.post(f"{BASE}/{attempt['id']}/submit")
    assert response.status_code == 200
    return response.json()


def save_correct_answers(client, db_factory, attempt):
    with db_factory() as db:
        row = db.get(AssessmentAttempt, attempt["id"])
        answers = [
            (
                item.id,
                next(o.id for o in item.question.options if o.is_correct),
            )
            for item in row.questions
        ]
    for question_id, option_id in answers:
        response = client.put(
            f"{BASE}/{attempt['id']}/answers/{question_id}",
            json={"selected_option_id": option_id},
        )
        assert response.status_code == 200


def assert_private_fields_absent(value):
    if isinstance(value, dict):
        assert not {
            "is_correct",
            "answer_key",
            "correct_option_index",
            "correct_option_id",
            "solution",
            "explanation",
        }.intersection(value)
        for child in value.values():
            assert_private_fields_absent(child)
    elif isinstance(value, list):
        for child in value:
            assert_private_fields_absent(child)


def test_production_source_and_publication_unchanged(original_backend):
    assert len(original_backend) == 120
    assert list(load_banks()) == [Spec.BACKEND]
    assert Counter(q.grade for q in original_backend) == dict.fromkeys(Grade, 40)
    sources = question_bank.bank_sources()
    assert sources[Spec.BACKEND].blueprint == LEGACY_BACKEND_BLUEPRINT
    assert sources[Spec.BACKEND].reviewed_sha256 == BACKEND_HASH
    assert not sources[Spec.FRONTEND].published
    assert not sources[Spec.DATA_ML].published
    assert validate_source_bank(original_backend) == []


def test_complete_three_bank_inventory(source_registry):
    banks = {spec: synthetic_bank(spec) for spec in Spec}
    source_registry(banks)
    loaded = load_banks()
    assert sum(map(len, loaded.values())) == 450
    assert len({q.code for bank in loaded.values() for q in bank}) == 450
    assert validate_source_banks(loaded) == []
    for spec, bank in loaded.items():
        assert len(bank) == 150
        assert Counter(q.grade for q in bank) == dict.fromkeys(Grade, 50)
        for grade in Grade:
            for competency in COMPETENCIES[spec]:
                assert (
                    Counter(
                        q.difficulty
                        for q in bank
                        if q.grade == grade and q.competency == competency
                    )
                    == EXPANDED_BLUEPRINT.mix
                )


@pytest.mark.parametrize("specialization", list(Spec))
@pytest.mark.parametrize(
    "scenario", ["missing", "extra", "grade", "mix", "competency", "options"]
)
def test_expanded_structure_rejects_bad_bank(specialization, scenario, source_registry):
    bank = synthetic_bank(specialization)
    field, value, expected = {
        "grade": ("grade", Grade.MIDDLE, Category.INVALID_GRADE_COUNT),
        "mix": ("difficulty", Difficulty.APPLIED, Category.INVALID_BUCKET_COUNT),
        "competency": ("competency", "UNSUPPORTED", Category.INVALID_COMPETENCY),
        "options": (
            "options",
            ["same", " same ", "three", "four"],
            Category.DUPLICATE_OPTION,
        ),
        "missing": (None, None, Category.INVALID_TOTAL),
        "extra": (None, None, Category.INVALID_TOTAL),
    }[scenario]
    if field:
        bank[0] = bank[0].model_copy(update={field: value})
    elif scenario == "extra":
        bank.append(bank[0].model_copy(update={"code": "extra-v1"}))
    else:
        bank.pop()
    source_registry({specialization: bank})
    with pytest.raises(ValueError) as error:
        load_banks()
    assert expected.value in str(error.value)
    assert "Synthetic Alpha" not in str(error.value)


def test_competencies_are_specialization_specific():
    bank = synthetic_bank(Spec.FRONTEND)
    bank[0] = bank[0].model_copy(update={"competency": "PROGRAMMING"})
    findings = validate_source_bank(
        bank, specialization=Spec.FRONTEND, blueprint=EXPANDED_BLUEPRINT
    )
    assert Category.INVALID_COMPETENCY in {f.category for f in findings}


@pytest.mark.parametrize("specialization", [Spec.FRONTEND, Spec.DATA_ML])
def test_new_specialization_default_is_expanded(specialization):
    assert (
        validate_source_bank(
            synthetic_bank(specialization), specialization=specialization
        )
        == []
    )


@pytest.mark.parametrize(
    "specialization,blueprint",
    [
        (Spec.FRONTEND, LEGACY_BACKEND_BLUEPRINT),
        (Spec.DATA_ML, LEGACY_BACKEND_BLUEPRINT),
        (Spec.BACKEND, SourceBlueprint(1, 8, 1)),
    ],
)
def test_registry_cannot_override_frozen_distribution(
    source_registry, monkeypatch, specialization, blueprint
):
    sources = source_registry({specialization: synthetic_bank(specialization)})
    monkeypatch.setattr(
        question_bank, "BANK_SOURCES", (replace(sources[0], blueprint=blueprint),)
    )
    with pytest.raises(ValueError, match="Invalid assessment bank registry"):
        load_banks()


@pytest.mark.parametrize(
    "scenario", ["duplicate", "foreign_predecessor", "shared_predecessor"]
)
def test_global_identity_and_lineage_rejected(source_registry, scenario):
    banks = {spec: synthetic_bank(spec) for spec in Spec}
    backend = banks[Spec.BACKEND][0]
    frontend = banks[Spec.FRONTEND][0]
    if scenario == "duplicate":
        banks[Spec.FRONTEND][0] = frontend.model_copy(update={"code": backend.code})
        expected = Category.DUPLICATE_CODE
    elif scenario == "foreign_predecessor":
        banks[Spec.FRONTEND][0] = frontend.model_copy(
            update={"supersedes": backend.code}
        )
        expected = Category.INVALID_SUPERSEDES
    else:
        banks[Spec.BACKEND][0] = backend.model_copy(
            update={"supersedes": "historical-code"}
        )
        banks[Spec.FRONTEND][0] = frontend.model_copy(
            update={"supersedes": "historical-code"}
        )
        expected = Category.INVALID_SUPERSEDES
    source_registry(banks)
    with pytest.raises(ValueError, match=expected.value):
        load_banks()


@pytest.mark.parametrize("version", [True, "1", 1.0])
def test_parser_requires_strict_version(version):
    record = synthetic_bank(Spec.FRONTEND)[0].model_dump(mode="json")
    record["version"] = version
    with pytest.raises(ValueError):
        SeedQuestion.model_validate(record)


@pytest.mark.parametrize(
    "scenario", ["no_review", "changed_hash", "missing_file", "bad_utf8"]
)
def test_publication_requires_reviewed_exact_valid_source(
    source_registry, tmp_path, scenario
):
    bank = synthetic_bank(Spec.FRONTEND)
    sources = source_registry({Spec.FRONTEND: bank})
    path = tmp_path / "content" / sources[0].filename
    if scenario == "no_review":
        question_bank.BANK_SOURCES = (replace(sources[0], review_reference=None),)
        assert load_banks() == {}
        assert len(load_bank(Spec.FRONTEND)) == 150  # preflight is not publication
        return
    if scenario == "changed_hash":
        raw = json.loads(path.read_bytes())
        raw[0]["prompt"] = "PRIVATE_CHANGED_CONTENT"
        path.write_text(json.dumps(raw))
    elif scenario == "missing_file":
        path.unlink()
    else:
        path.write_bytes(b"\xff PRIVATE_CHANGED_CONTENT")
    with pytest.raises(ValueError) as error:
        load_banks()
    assert "PRIVATE_CHANGED_CONTENT" not in "".join(format_exception(error.value))


def test_registry_rejects_ambiguous_specialization(source_registry, monkeypatch):
    sources = source_registry({Spec.BACKEND: synthetic_bank(Spec.BACKEND)})
    monkeypatch.setattr(question_bank, "BANK_SOURCES", (*sources, sources[0]))
    with pytest.raises(ValueError, match="Invalid assessment bank registry"):
        load_banks()


@pytest.mark.parametrize("specialization", list(Spec))
def test_draft_source_and_persisted_draft_never_available(
    source_registry,
    client,
    account,
    app,
    candidate_data,
    db_factory,
    specialization,
):
    bank = synthetic_bank(specialization)
    source_registry({specialization: bank}, published=[])
    profile = setup_candidate(client, account, app, candidate_data, specialization)
    with db_factory() as db:
        seed(db)
        assert list(db.scalars(select(AssessmentQuestion))) == []
    # Simulate old/manual DB rows: even a technically complete bank has no approval.
    question_bank.BANK_SOURCES = tuple(
        replace(s, reviewed_sha256=None) for s in question_bank.BANK_SOURCES
    )
    with db_factory() as db:
        for item in bank:
            question_bank._seed_question(db, {}, specialization, item)
        db.commit()
    available = client.get(BASE + "/availability").json()
    assert available["verification"]["id"] == profile["id"]
    assert all(g["reason"] == "UNAVAILABLE" for g in available["grades"])
    response = client.post(BASE, json={"target_grade": "JUNIOR"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "assessment_unavailable"


@pytest.mark.parametrize("specialization", list(Spec))
def test_partial_or_changed_persisted_bank_blocks_new_start(
    source_registry,
    client,
    account,
    app,
    candidate_data,
    db_factory,
    specialization,
):
    source_registry({specialization: synthetic_bank(specialization)})
    setup_candidate(client, account, app, candidate_data, specialization)
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        question = db.scalar(
            select(AssessmentQuestion).where(AssessmentQuestion.grade == Grade.SENIOR)
        )
        question.is_active = False
        db.commit()
    # A full Junior grade still cannot expose an incomplete specialization bank.
    assert client.post(BASE, json={"target_grade": "JUNIOR"}).status_code == 409
    with db_factory() as db:
        question = db.scalar(
            select(AssessmentQuestion).where(AssessmentQuestion.is_active.is_(False))
        )
        question.is_active = True
        question.options[0].is_correct = False
        db.commit()
    assert client.post(BASE, json={"target_grade": "JUNIOR"}).status_code == 409


@pytest.mark.parametrize("specialization", list(Spec))
@pytest.mark.parametrize("grade", list(Grade))
def test_all_nine_attempt_lifecycles(
    source_registry,
    client,
    account,
    app,
    candidate_data,
    db_factory,
    monkeypatch,
    specialization,
    grade,
):
    source_registry({spec: synthetic_bank(spec) for spec in Spec})
    with db_factory() as db:
        seed(db)
    setup_candidate(client, account, app, candidate_data, specialization)
    now = [datetime(2030, 1, 1, tzinfo=UTC)]
    monkeypatch.setattr(assessments, "utcnow", lambda: now[0])
    first = start(client, grade)
    assert first["specialization"] == specialization
    assert len(first["questions"]) == 20
    assert len({q["question_id"] for q in first["questions"]}) == 20
    assert datetime.fromisoformat(first["expires_at"]) - datetime.fromisoformat(
        first["started_at"]
    ) == timedelta(minutes=30)
    for competency in COMPETENCIES[specialization]:
        assert (
            Counter(
                q["difficulty"]
                for q in first["questions"]
                if q["competency"] == competency
            )
            == assessments.BLUEPRINT
        )
    assert_private_fields_absent(first)
    save_correct_answers(client, db_factory, first)
    saved = client.get(f"{BASE}/{first['id']}").json()
    assert all(q["selected_option_id"] for q in saved["questions"])
    assert [[o["id"] for o in q["options"]] for q in saved["questions"]] == [
        [o["id"] for o in q["options"]] for q in first["questions"]
    ]
    passed = submit(client, first)
    assert passed["status"] == "PASSED"
    assert passed["normalized_assessment_score"] == 100
    assert passed["competency_scores"] == dict.fromkeys(
        COMPETENCIES[specialization], 100
    )
    assert passed["verification"]["verified_grade"] == grade
    assert passed["verification"]["declared_grade"] == "SENIOR"
    assert passed["questions"] == []
    assert submit(client, first)["finished_at"] == passed["finished_at"]
    assert_private_fields_absent(passed)
    assert (
        client.post(BASE, json={"target_grade": grade}).json()["error"]["code"]
        == "assessment_cooldown"
    )
    with db_factory() as db:
        old_questions = question_snapshot(db)
        old_attempt = attempt_snapshot(db.get(AssessmentAttempt, first["id"]))
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        assert question_snapshot(db) == old_questions
        assert attempt_snapshot(db.get(AssessmentAttempt, first["id"])) == old_attempt
    now[0] += timedelta(days=91)
    second = start(client, grade)
    assert {q["question_id"] for q in first["questions"]}.isdisjoint(
        q["question_id"] for q in second["questions"]
    )
    failed = submit(client, second)
    assert failed["status"] == "FAILED" and failed["normalized_assessment_score"] == 0
    assert failed["verification"] == passed["verification"]
    assert datetime.fromisoformat(failed["available_at"]) - now[0] == timedelta(days=7)
    now[0] += timedelta(days=8)
    third = start(client, grade)
    prior_applied = {
        q["question_id"]
        for attempt in (first, second)
        for q in attempt["questions"]
        if q["difficulty"] == "APPLIED"
    }
    assert prior_applied.isdisjoint(
        q["question_id"] for q in third["questions"] if q["difficulty"] == "APPLIED"
    )
    now[0] += timedelta(minutes=31)
    timeout = client.get(f"{BASE}/{third['id']}").json()
    assert timeout["completion_reason"] == "TIMEOUT" and timeout["status"] == "FAILED"
    assert timeout["finished_at"] == third["expires_at"]
    assert timeout["verification"] == passed["verification"]
    history = client.get(BASE + "/history").json()
    assert len(history) == 3
    assert_private_fields_absent(history)


@pytest.mark.parametrize("finished", [False, True])
def test_backend_120_to_150_preserves_questions_attempts_and_verification(
    source_registry,
    original_backend,
    client,
    account,
    app,
    candidate_data,
    db_factory,
    finished,
):
    source_registry(
        {Spec.BACKEND: original_backend},
        blueprints={Spec.BACKEND: LEGACY_BACKEND_BLUEPRINT},
    )
    with db_factory() as db:
        seed(db)
    setup_candidate(client, account, app, candidate_data, Spec.BACKEND)
    passed = start(client, Grade.JUNIOR)
    save_correct_answers(client, db_factory, passed)
    verification = submit(client, passed)["verification"]
    active = start(client, Grade.MIDDLE)
    if finished:
        submit(client, active)
    before = client.get(f"{BASE}/{active['id']}").json()
    with db_factory() as db:
        questions_before = question_snapshot(db)
        attempt_before = attempt_snapshot(db.get(AssessmentAttempt, active["id"]))
    additions = [
        q.model_copy(update={"code": "expansion-" + q.code})
        for q in synthetic_bank(Spec.BACKEND)
        if q.difficulty == Difficulty.APPLIED and q.code.rsplit("-", 2)[1] in ("6", "7")
    ]
    assert len(additions) == 30
    source_registry({Spec.BACKEND: [*original_backend, *additions]})
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        questions_after = question_snapshot(db)
        assert len(questions_after) == 150
        assert {
            code: questions_after[code] for code in questions_before
        } == questions_before
        assert (
            attempt_snapshot(db.get(AssessmentAttempt, active["id"])) == attempt_before
        )
        assert question_bank.bank_is_published(db, Spec.BACKEND)
    after = client.get(f"{BASE}/{active['id']}").json()
    assert {k: v for k, v in after.items() if k != "server_now"} == {
        k: v for k, v in before.items() if k != "server_now"
    }
    assert after["verification"] == verification
    assert submit(client, active)["verification"] == verification
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        assert question_snapshot(db) == questions_after


def test_removing_publication_keeps_active_and_finished_history(
    source_registry,
    client,
    account,
    app,
    candidate_data,
    db_factory,
    monkeypatch,
):
    sources = source_registry({Spec.FRONTEND: synthetic_bank(Spec.FRONTEND)})
    with db_factory() as db:
        seed(db)
    setup_candidate(client, account, app, candidate_data, Spec.FRONTEND)
    active = start(client, Grade.JUNIOR)
    monkeypatch.setattr(
        question_bank,
        "BANK_SOURCES",
        tuple(replace(s, reviewed_sha256=None, review_reference=None) for s in sources),
    )
    save_correct_answers(client, db_factory, active)
    passed = submit(client, active)
    assert (
        passed["status"] == "PASSED"
        and passed["verification"]["verified_grade"] == "JUNIOR"
    )
    assert (
        client.get(f"{BASE}/{active['id']}").json()["normalized_assessment_score"]
        == 100
    )
    assert len(client.get(BASE + "/history").json()) == 1
    assert client.post(BASE, json={"target_grade": "MIDDLE"}).status_code == 409


def test_invalid_later_bank_cannot_partially_seed(source_registry, db_factory):
    banks = {spec: synthetic_bank(spec) for spec in Spec}
    banks[Spec.DATA_ML].pop()
    source_registry(banks)
    with db_factory() as db, pytest.raises(ValueError):
        seed(db)
    with db_factory() as db:
        assert list(db.scalars(select(AssessmentQuestion))) == []


def test_cross_bank_historical_predecessor_cannot_deactivate(
    source_registry,
    db_factory,
):
    backend = synthetic_bank(Spec.BACKEND)
    source_registry({Spec.BACKEND: backend})
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        before = question_snapshot(db)
    frontend = synthetic_bank(Spec.FRONTEND)
    frontend[0] = frontend[0].model_copy(update={"supersedes": backend[0].code})
    source_registry({Spec.FRONTEND: frontend})
    with db_factory() as db, pytest.raises(ValueError, match="predecessor"):
        seed(db)
    with db_factory() as db:
        assert question_snapshot(db) == before
