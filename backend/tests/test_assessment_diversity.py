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


# Failed P5 source freeze a0e5d399: opaque content hashes, no marking keys.
P5_FIRST_FREEZE_HASHES = {
    "backend-junior-architecture-6-v1": "946b64237af9f86d1b8cfce78a2d868e78eb0869b41b406c4ae9962edb2b499d",
    "backend-junior-architecture-7-v1": "fee84cc56c0b90075b171acf89f5ad42f522a78752aeecd6063314997f79355f",
    "backend-junior-architecture-8-v1": "5a3c0f7be744b7edff968a23271813084db7207e5d82d030b60759a4929ecc06",
    "backend-junior-databases-6-v1": "cc99ec02ec9793816b0a5df19dff3691ee2959d98f63b7315ea68ca1dde47e99",
    "backend-junior-databases-7-v1": "43efb5e3866f701ad87dae8115f7f472fd592f078455e40b3fa33cfb54bb58ea",
    "backend-junior-databases-8-v1": "e3b4881768c00ce8a0c68f42146a90f130989d03a5297d01dc21d9be93997ce0",
    "backend-junior-http_api-6-v1": "36f83c389624d5664ba749b76acb4a93a2cf8ccb0d3ff4e3077114a35c7984a0",
    "backend-junior-http_api-7-v1": "01a660e637b846aa8c0f82725534288651ae5b59bd6df9ea6f5731e93a748862",
    "backend-junior-http_api-8-v1": "e724525aee29c76fead06244fe0e6d3726e8bf27cc356ee9f22fe97d6e3a6262",
    "backend-junior-programming-6-v1": "c882bc980546a911dffacda5e201dc146c8b1a4d5640eee6e1a37270f2e1bb57",
    "backend-junior-programming-7-v1": "1235d2f7309e42ff80918e4fe6a21bab4e86ff4bc227e14babb7eaab8984d2d5",
    "backend-junior-programming-8-v1": "f3f92fd01e9120f48a5c4b0e7e6fd1de141581ae9ce82952aed96e57408908d6",
    "backend-junior-testing_security_debugging-6-v1": "a863e1a4375efea0402a2afd45f3fe671148b8ac4f4f67449117ce2f6be32ff5",
    "backend-junior-testing_security_debugging-7-v1": "6d218e2d4bef7472eaec4c472faa1a9502d13d4f34ec39649bff05df3ca6d668",
    "backend-junior-testing_security_debugging-8-v1": "3693b0c01a95396af629351973942dff56278c0d8f141bc0ddd238a6074d378e",
    "backend-middle-architecture-6-v1": "06fbad188d9d1bcbc7ef82f8cb79b60fc759311ceb30169151062f0f8ebdacac",
    "backend-middle-architecture-7-v1": "46e072e3d8577839f14bc9ebeabe607395c1eb338f7346bf9b2494c551baebc5",
    "backend-middle-architecture-8-v1": "2caa70172a163a0fad08a0e27d4ed379dd2f42129236f158a00cf6af4fc11afc",
    "backend-middle-databases-6-v1": "3f1b36ad3770e20e15a46213231f3726356bb8225e41c39c95a3889522a45c11",
    "backend-middle-databases-7-v1": "462ed9484ecb49b0a46eb5007843a5292d0666364f1128de903a68a1c69474c7",
    "backend-middle-databases-8-v1": "f220f9f8a725e122e4cc2b1c51890897addb9302d30ad38f3f6a0d31c4bec6b9",
    "backend-middle-http_api-6-v1": "d2b178b0eb075e28b9d12e42cad5d97c42b25fa34a5592071c5143aec155d235",
    "backend-middle-http_api-7-v1": "5f50503ff17928c6494e2ac0226dfb7e466ab9c4edd44016e818d09e0450cf47",
    "backend-middle-http_api-8-v1": "276878cd7d5f2882e477c21afd7dabcc7f6e9b4bfd53fc011df473d4af619907",
    "backend-middle-programming-6-v1": "d60e43d0251886703a4ff1793a551d501e4f180e1b61487bc28600af46787131",
    "backend-middle-programming-7-v1": "e1845a457269f45806541e4942871196199a5a609ab46f095944da8b4c252549",
    "backend-middle-programming-8-v1": "7fdcc11660fc7c0431d135d1d5ec551d1bcc19aaa3937801f87c6b5b5ea24f1f",
    "backend-middle-testing_security_debugging-6-v1": "86b65913752d04154e0a8f1a5e5544be557f44a7509ca297ac3340e6efd615a1",
    "backend-middle-testing_security_debugging-7-v1": "cb95650d32d6ab2aee373b3fea6d1463af05e8a59433fc889f23d4ad160d0231",
    "backend-middle-testing_security_debugging-8-v1": "1200ac07e505e67755ed141d7a5680a50031bd311e0a69f091409b20fba43b91",
    "backend-senior-architecture-6-v1": "ab56bc53c267d87edf8f09372147ce3794fd61c34903a9d445ea6edba1a39bae",
    "backend-senior-architecture-7-v1": "d466143e971b30e8b0681be29d4371a152e2708594fa23d16869ca709941e545",
    "backend-senior-architecture-8-v1": "38e9fa7c8923be12a498dbcc7df8d135b35bcc0832f7373b38d428e30dc9b3ca",
    "backend-senior-databases-6-v1": "9ef0f6ce12977a9f763d4250b72b0358ab724827beeb7e62e4c9646b474b8eef",
    "backend-senior-databases-7-v1": "99619108af6ebf9a7d5bc227881551c3c6cdd7298bc50e0705a9d617df6df69d",
    "backend-senior-databases-8-v1": "14aa70a0156d824b78ea6c92e1cf88f883c0de4d699ce6440ddf70b96036bffa",
    "backend-senior-http_api-6-v1": "4f2a8cbdab7f6270267ca7b69dfc463fb6371403e766e78e938420c8475bddcd",
    "backend-senior-http_api-7-v1": "e3169e7a0896d8c3a18b67a8607454d097b8ae23634bcff0e09b5ab9a744dca1",
    "backend-senior-http_api-8-v1": "b5adb6a2f9544bf4ecd3ea9731fc51e9f6164c6e595305e067eeeb005c5ab01b",
    "backend-senior-programming-6-v1": "146d76bd15a9dda57a891c11030dc3195b66914c015df06b2afeedc824991d66",
    "backend-senior-programming-7-v1": "d1791d8fb8f45cd4236e4dc0f85ecbb5a7e187f446a6f882a3e90599481b8b28",
    "backend-senior-programming-8-v1": "b7e52f2483eb51adcbe02661b1d3943bcd46cee111b80b29fe1c183029c87640",
    "backend-senior-testing_security_debugging-6-v1": "392c25b7cb32887b718fd6c9fc712545d6b7215416594f7c0e87ae95005a5c8d",
    "backend-senior-testing_security_debugging-7-v1": "9feec4364b3649d604d5c564553d79a4153c179693ec4e65a4d72efd3bf8caed",
    "backend-senior-testing_security_debugging-8-v1": "7b93eedb83e895a068c6acf6f20611c46d4e5b045d3f6811de3efe0e6750fa5c",
}
P5_B_REMEDIATED_CODES = {
    "backend-junior-testing_security_debugging-8-v1",
    "backend-middle-architecture-8-v1",
    "backend-middle-databases-8-v1",
    "backend-middle-programming-7-v1",
    "backend-middle-programming-8-v1",
    "backend-senior-architecture-8-v1",
    "backend-senior-testing_security_debugging-8-v1",
}


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


def test_p5_b_edits_exactly_seven_unpublished_v1_records():
    current = {q.code: q for q in load_bank() if q.code in DIVERSITY_CODES}
    assert set(current) == set(P5_FIRST_FREEZE_HASHES)
    changed = {
        code
        for code, q in current.items()
        if fingerprint(q.model_dump()) != P5_FIRST_FREEZE_HASHES[code]
    }
    assert changed == P5_B_REMEDIATED_CODES
    assert len(current) == 45 and len(changed) == 7
    for code, q in current.items():
        slot = int(code.rsplit("-", 2)[1])
        assert (
            code == f"backend-{q.grade.value.lower()}-{q.competency.lower()}-{slot}-v1"
        )
        assert q.difficulty.value == {6: "BASIC", 7: "APPLIED", 8: "ADVANCED"}[slot]
        assert q.version == 1 and q.supersedes is None
