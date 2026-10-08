import json
import random
from collections import Counter
from datetime import timedelta
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy import select
from test_assessment_bank_remediation import (
    B1_HASH,
    BASELINE_HASH,
    DIVERSITY_CODES,
    attempt_snapshot,
    fingerprint,
    frozen_bank,
    question_snapshot,
    seed_fixed_bank,
)
from test_assessments import BASE, answer_counts, expire, finish, start
from test_assessments import ready as ready

from app.models import (
    AssessmentAttempt,
    AssessmentQuestion,
    CandidateProfile,
    Grade,
    User,
)
from app.question_bank import SeedQuestion, load_bank
from app.seed import seed
from app.services import assessments

PRE_P5_HASH = "11fba035b866475b588f62a142bc97f47e7fe94898afdbba3ecd263b5b7fae56"


@pytest.fixture
def pre_p5_bank():
    return frozen_bank("assessment-bank-pre-p5.json", PRE_P5_HASH)


@pytest.fixture
def clock(monkeypatch):
    now = [assessments.utcnow()]
    monkeypatch.setattr(assessments, "utcnow", lambda: now[0])
    return now


def families(db_factory, attempt):
    ids = {q["question_id"] for q in attempt["questions"]}
    with db_factory() as db:
        return {
            assessments.question_family(q.code)
            for q in db.scalars(
                select(AssessmentQuestion).where(AssessmentQuestion.id.in_(ids))
            )
        }


def assert_blueprint(db_factory, attempt):
    ids = {q["question_id"] for q in attempt["questions"]}
    assert len(ids) == len(attempt["questions"]) == 20
    with db_factory() as db:
        selected = list(
            db.scalars(select(AssessmentQuestion).where(AssessmentQuestion.id.in_(ids)))
        )
        for competency in assessments.COMPETENCIES["BACKEND"]:
            assert Counter(
                q.difficulty for q in selected if q.competency == competency
            ) == {"BASIC": 1, "APPLIED": 2, "ADVANCED": 1}


def setup_unseeded(client, account, candidate_data, db_factory):
    user = account()
    profile = client.post("/candidate/profile", json=candidate_data)
    assert profile.status_code == 201
    with db_factory() as db:
        db.get(User, user["id"]).email_verified = True
        db.commit()
    return profile.json()


class FirstChoice:
    def sample(self, population, count):
        return list(population[:count])

    def shuffle(self, values):
        values.reverse()


class RotateOptions(FirstChoice):
    def shuffle(self, values):
        if len(values) == 4:
            values[:] = values[1:] + values[:1]
        else:
            values.reverse()


class IncludeLegacy(FirstChoice):
    def sample(self, population, count):
        ordered = sorted(
            population, key=lambda q: q.code != "backend-middle-databases-4-v1"
        )
        return ordered[:count]


def test_exact_120_inventory_preserves_75_frozen_records(pre_p5_bank):
    current = load_bank()
    before = {q.code: q for q in pre_p5_bank}
    after = {q.code: q for q in current}
    assert len(after) == 120
    assert set(after) - set(before) == DIVERSITY_CODES
    assert len(DIVERSITY_CODES) == 45
    for code, original in before.items():
        assert fingerprint(original.model_dump()) == fingerprint(
            after[code].model_dump()
        ), code
    for code in DIVERSITY_CODES:
        assert after[code].version == 1
        assert after[code].supersedes is None
    for grade in Grade:
        assert sum(q.grade == grade for q in current) == 40
        for competency in assessments.COMPETENCIES["BACKEND"]:
            assert Counter(
                q.difficulty
                for q in current
                if q.grade == grade and q.competency == competency
            ) == {"BASIC": 2, "APPLIED": 4, "ADVANCED": 2}
    predecessors = [q for q in current if q.supersedes]
    assert len(predecessors) == 37
    for q in predecessors:
        assert assessments.question_family(q.code) == assessments.question_family(
            q.supersedes
        ), q.code
    assert assessments.question_family("custom-code") == "custom-code"
    assert assessments.question_family("custom-vword") == "custom-vword"


@pytest.mark.parametrize("grade", list(Grade))
@pytest.mark.parametrize("seed_value", [0, 1, 19])
def test_first_two_attempts_are_disjoint_in_all_buckets(
    client, ready, db_factory, clock, monkeypatch, grade, seed_value
):
    monkeypatch.setattr(
        assessments.random, "SystemRandom", lambda: random.Random(seed_value)
    )
    first = start(client, grade)
    assert_blueprint(db_factory, first)
    assert client.get(f"{BASE}/{first['id']}").json()["questions"] == first["questions"]
    assert finish(client, first)["status"] == "FAILED"
    clock[0] += timedelta(days=8)
    second = start(client, grade)
    assert_blueprint(db_factory, second)
    first_families, second_families = (
        families(db_factory, first),
        families(db_factory, second),
    )
    assert len(first_families) == len(second_families) == 20
    assert first_families.isdisjoint(second_families)
    assert len(first_families | second_families) == 40


@pytest.mark.parametrize("grade", list(Grade))
def test_eight_retakes_keep_each_bucket_exposure_balanced(
    client, ready, db_factory, clock, grade
):
    pool = [q for q in load_bank() if q.grade == grade]
    exposure = Counter()
    for _ in range(8):
        attempt = start(client, grade)
        assert_blueprint(db_factory, attempt)
        exposure.update(families(db_factory, attempt))
        assert finish(client, attempt)["status"] == "FAILED"
        clock[0] += timedelta(days=8)
        for competency in assessments.COMPETENCIES["BACKEND"]:
            for difficulty in assessments.BLUEPRINT:
                counts = [
                    exposure[assessments.question_family(q.code)]
                    for q in pool
                    if q.competency == competency and q.difficulty == difficulty
                ]
                assert max(counts) - min(counts) <= 1
    assert set(exposure.values()) == {4}
    with db_factory() as db:
        profile = db.get(CandidateProfile, ready["id"])
        assert assessments.historical_exposure(db, profile, grade) == exposure


@pytest.mark.parametrize(
    "levels,expected",
    [([0, 0, 1, 1], [0, 0]), ([0, 1, 1, 4], [0, 1]), ([2, 2, 2, 3], [2, 2])],
)
def test_applied_selection_expands_only_when_lowest_pool_is_insufficient(
    levels, expected
):
    questions = [AssessmentQuestion(code=f"synthetic-{i}-v1") for i in range(4)]
    exposure = Counter(
        {
            assessments.question_family(q.code): level
            for q, level in zip(questions, levels, strict=True)
        }
    )
    selected = assessments.least_exposed_questions(
        questions, 2, exposure, FirstChoice()
    )
    assert len({q.code for q in selected}) == 2
    assert [exposure[assessments.question_family(q.code)] for q in selected] == expected


def test_runtime_uses_system_random_without_seed(client, ready, monkeypatch):
    secure = Mock(wraps=random.SystemRandom)
    monkeypatch.setattr(assessments.random, "SystemRandom", secure)
    start(client)
    secure.assert_called_once_with()


def test_candidates_sample_independently_and_option_shuffle_is_persisted(
    client, ready, account, candidate_data, db_factory, monkeypatch
):
    monkeypatch.setattr(assessments.random, "SystemRandom", FirstChoice)
    first = start(client)
    assert client.get(f"{BASE}/{first['id']}").json()["questions"] == first["questions"]
    finish(client, first)
    other_user = account(email="other-candidate@example.com")
    response = client.post("/candidate/profile", json=candidate_data)
    assert response.status_code == 201
    with db_factory() as db:
        db.get(User, other_user["id"]).email_verified = True
        other = db.get(CandidateProfile, response.json()["id"])
        assert assessments.historical_exposure(db, other, Grade.MIDDLE) == {}
        db.commit()
    monkeypatch.setattr(assessments.random, "SystemRandom", RotateOptions)
    second = start(client)
    assert families(db_factory, second) == families(db_factory, first)
    first_options = {
        q["question_id"]: [o["id"] for o in q["options"]] for q in first["questions"]
    }
    second_options = {
        q["question_id"]: [o["id"] for o in q["options"]] for q in second["questions"]
    }
    assert all(first_options[qid] != second_options[qid] for qid in first_options)
    assert (
        client.get(f"{BASE}/{second['id']}").json()["questions"] == second["questions"]
    )


@pytest.mark.parametrize("outcome", ["passed", "failed", "timeout"])
def test_predecessor_exposure_inherits_through_v1_v2_v3_without_history_edits(
    client, account, candidate_data, db_factory, monkeypatch, clock, outcome
):
    profile_data = setup_unseeded(client, account, candidate_data, db_factory)
    baseline = frozen_bank("assessment-bank-pre-p3.json", BASELINE_HASH)
    b1 = frozen_bank("assessment-bank-p3-b1.json", B1_HASH)
    seed_fixed_bank(db_factory, baseline, monkeypatch)
    monkeypatch.setattr(assessments.random, "SystemRandom", IncludeLegacy)
    first = start(client)
    lineage = "backend-middle-databases-4"
    assert lineage in families(db_factory, first)
    if outcome == "passed":
        answer_counts(db_factory, first)
    if outcome == "timeout":
        expire(db_factory, first, clock[0])
        result = client.get(f"{BASE}/{first['id']}").json()
        assert result["completion_reason"] == "TIMEOUT"
    else:
        result = finish(client, first)
    assert result["status"] == ("PASSED" if outcome == "passed" else "FAILED")
    with db_factory() as db:
        original_membership = attempt_snapshot(db.get(AssessmentAttempt, first["id"]))
        original_content = question_snapshot(db)[lineage + "-v1"]["content"]
        profile = db.get(CandidateProfile, profile_data["id"])
        assert (
            sum(assessments.historical_exposure(db, profile, Grade.MIDDLE).values())
            == 20
        )
        assert assessments.historical_exposure(db, profile, Grade.JUNIOR) == {}
        profile.specialization = "FRONTEND"
        assert assessments.historical_exposure(db, profile, Grade.MIDDLE) == {}
        db.rollback()
    seed_fixed_bank(db_factory, b1, monkeypatch)
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        rows = question_snapshot(db)
        assert rows[lineage + "-v1"]["content"] == original_content
        assert not rows[lineage + "-v1"]["active"]
        assert not rows[lineage + "-v2"]["active"]
        assert rows[lineage + "-v3"]["active"]
        assert (
            attempt_snapshot(db.get(AssessmentAttempt, first["id"]))
            == original_membership
        )
        profile = db.get(CandidateProfile, profile_data["id"])
        assert assessments.historical_exposure(db, profile, Grade.MIDDLE)[lineage] == 1
    clock[0] += timedelta(days=91 if outcome == "passed" else 8)
    second = start(client)
    assert lineage not in families(db_factory, second)
    assert families(db_factory, first).isdisjoint(families(db_factory, second))


@pytest.mark.parametrize("finished", [False, True], ids=["in-progress", "finished"])
def test_75_to_120_seed_preserves_every_existing_row_and_attempt(
    client, account, candidate_data, db_factory, pre_p5_bank, monkeypatch, finished
):
    setup_unseeded(client, account, candidate_data, db_factory)
    seed_fixed_bank(db_factory, pre_p5_bank, monkeypatch)
    attempt = start(client)
    if finished:
        finish(client, attempt)
    before_read = client.get(f"{BASE}/{attempt['id']}").json()["questions"]
    with db_factory() as db:
        before_questions = question_snapshot(db)
        before_attempt = attempt_snapshot(db.get(AssessmentAttempt, attempt["id"]))
    with db_factory() as db:
        seed(db)
    with db_factory() as db:
        after = question_snapshot(db)
        assert len(before_questions) == 75 and len(after) == 120
        assert set(after) - set(before_questions) == DIVERSITY_CODES
        for code in before_questions:
            assert after[code] == before_questions[code], code
        assert (
            attempt_snapshot(db.get(AssessmentAttempt, attempt["id"])) == before_attempt
        )
    assert client.get(f"{BASE}/{attempt['id']}").json()["questions"] == before_read
    if not finished:
        question = attempt["questions"][0]
        saved = client.put(
            f"{BASE}/{attempt['id']}/answers/{question['attempt_question_id']}",
            json={"selected_option_id": question["options"][0]["id"]},
        )
        assert saved.status_code == 200
        assert finish(client, attempt)["status"] == "FAILED"
    with db_factory() as db:
        seed(db)
        assert question_snapshot(db) == after


def test_expected_independent_cross_candidate_overlap_is_ten_of_twenty():
    forms = [
        set(b + a + d)
        for b in combinations(range(2), 1)
        for a in combinations(range(2, 6), 2)
        for d in combinations(range(6, 8), 1)
    ]
    assert len(forms) == 24
    per_competency = Fraction(
        sum(len(a & b) for a in forms for b in forms), len(forms) ** 2
    )
    assert per_competency == 2
    assert per_competency * 5 == 10
    assert Fraction(10, 20) == Fraction(1, 2)


def test_pre_p5_fixture_is_exact_base_source_bytes():
    content = (
        Path(__file__).parent / "fixtures" / "assessment-bank-pre-p5.json"
    ).read_bytes()
    assert sha256(content).hexdigest() == PRE_P5_HASH
    assert len(json.loads(content)) == 75
    assert all(SeedQuestion.model_validate(q) for q in json.loads(content))
