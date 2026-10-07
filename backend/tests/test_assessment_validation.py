import json
from dataclasses import FrozenInstanceError, asdict
from hashlib import sha256
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.assessment_validation import (
    AssessmentValidationCategory as Category,
)
from app.assessment_validation import (
    AssessmentValidationFinding,
    validate_source_bank,
)
from app.models import Difficulty, Grade
from app.question_bank import SeedQuestion, load_bank


@pytest.fixture
def source_bank():
    return load_bank()


def question(code="question", supersedes=None):
    return SeedQuestion(
        code=code,
        version=1,
        supersedes=supersedes,
        grade=Grade.JUNIOR,
        competency="PROGRAMMING",
        difficulty=Difficulty.BASIC,
        prompt="Synthetic prompt",
        options=["Alpha", "Beta", "Gamma", "Delta"],
    )


def categories(questions):
    return {finding.category for finding in validate_source_bank(questions)}


def fingerprint(questions):
    # Compare hashes so an assertion failure cannot print the real source content.
    content = json.dumps([q.model_dump() for q in questions], sort_keys=True)
    return sha256(content.encode()).hexdigest()


def test_real_source_bank_passes(source_bank):
    assert len(source_bank) == 75
    assert validate_source_bank(source_bank) == []


@pytest.mark.parametrize("total", [74, 76])
def test_wrong_total_rejected(source_bank, total):
    questions = source_bank[:74] if total == 74 else [*source_bank, question()]
    assert Category.INVALID_TOTAL in categories(questions)


def test_wrong_grade_count_rejected(source_bank):
    source_bank[0] = source_bank[0].model_copy(update={"grade": Grade.MIDDLE})
    assert len(source_bank) == 75
    findings = validate_source_bank(source_bank)
    assert [
        f.context for f in findings if f.category == Category.INVALID_GRADE_COUNT
    ] == [
        "JUNIOR: expected 25 source records; found 24.",
        "MIDDLE: expected 25 source records; found 26.",
    ]


def test_wrong_bucket_difficulty_mix_rejected(source_bank):
    applied = next(i for i, q in enumerate(source_bank) if q.difficulty == "APPLIED")
    source_bank[applied] = source_bank[applied].model_copy(
        update={"difficulty": Difficulty.BASIC}
    )
    findings = validate_source_bank(source_bank)
    assert Category.INVALID_GRADE_COUNT not in {f.category for f in findings}
    assert [f.context for f in findings] == [
        "JUNIOR/PROGRAMMING/BASIC: expected 1 source record(s); found 2.",
        "JUNIOR/PROGRAMMING/APPLIED: expected 3 source record(s); found 2.",
    ]


@pytest.mark.parametrize("code", ["", " \t\n"])
def test_blank_trimmed_code_rejected(code):
    assert Category.BLANK_CODE in categories([question(code)])


def test_duplicate_code_rejected():
    findings = validate_source_bank([question("same"), question("same")])
    duplicate = [f for f in findings if f.category == Category.DUPLICATE_CODE]
    assert len(duplicate) == 1
    assert duplicate[0].code == "same"


def test_codes_are_exact_and_have_no_new_naming_rule():
    questions = [question("custom"), question(" custom "), question("CUSTOM")]
    assert Category.DUPLICATE_CODE not in categories(questions)
    assert Category.BLANK_CODE not in categories(questions)


@pytest.mark.parametrize("prompt", ["", " \t\n"])
def test_blank_trimmed_prompt_rejected(prompt):
    item = question().model_copy(update={"prompt": prompt})
    assert Category.BLANK_PROMPT in categories([item])


@pytest.mark.parametrize("count", [0, 3, 5])
def test_wrong_option_count_rejected(count):
    item = question().model_copy(
        update={"options": [f"Option {i}" for i in range(count)]}
    )
    assert Category.INVALID_OPTIONS in categories([item])


@pytest.mark.parametrize("blank", ["", " \t\n"])
def test_blank_option_rejected(blank):
    item = question().model_copy(update={"options": ["Alpha", "Beta", "Gamma", blank]})
    assert Category.INVALID_OPTIONS in categories([item])


def test_whitespace_equivalent_option_duplicate_rejected():
    item = question().model_copy(
        update={"options": ["Alpha beta", " Alpha\t beta\n", "Gamma", "Delta"]}
    )
    assert Category.DUPLICATE_OPTION in categories([item])


def test_case_punctuation_and_words_remain_significant():
    item = question().model_copy(
        update={"options": ["Alpha beta", "alpha beta", "Alpha beta!", "Alpha gamma"]}
    )
    assert Category.DUPLICATE_OPTION not in categories([item])
    assert Category.INVALID_OPTIONS not in categories([item])


@pytest.mark.parametrize("value", ["UNKNOWN", None, [], {}])
def test_invalid_competency_rejected(value):
    item = question().model_copy(update={"competency": value})
    assert Category.INVALID_COMPETENCY in categories([item])


@pytest.mark.parametrize("value", ["UNKNOWN", None, [], {}])
def test_invalid_grade_rejected(value):
    item = question().model_copy(update={"grade": value})
    assert Category.INVALID_GRADE in categories([item])


@pytest.mark.parametrize("value", ["UNKNOWN", None, [], {}])
def test_invalid_difficulty_rejected(value):
    item = question().model_copy(update={"difficulty": value})
    assert Category.INVALID_DIFFICULTY in categories([item])


@pytest.mark.parametrize(
    "field,value,expected",
    [
        ("grade", "JUNIOR", Category.INVALID_GRADE),
        ("difficulty", "BASIC", Category.INVALID_DIFFICULTY),
    ],
)
def test_raw_enum_value_strings_rejected(field, value, expected):
    item = question().model_copy(update={field: value})
    assert type(getattr(item, field)) is str
    assert expected in categories([item])


def test_actual_enum_metadata_remains_valid(source_bank):
    index = next(
        i
        for i, item in enumerate(source_bank)
        if item.grade is Grade.JUNIOR and item.difficulty is Difficulty.BASIC
    )
    source_bank[index] = source_bank[index].model_copy(
        update={"grade": Grade.JUNIOR, "difficulty": Difficulty.BASIC}
    )
    assert validate_source_bank(source_bank) == []


@pytest.mark.parametrize("value", [0, -1, None, "1", 1.5, True, [], {}])
def test_invalid_version_rejected(value):
    item = question().model_copy(update={"version": value})
    assert Category.INVALID_VERSION in categories([item])


@pytest.mark.parametrize(
    "field,value",
    [("grade", []), ("competency", []), ("difficulty", []), ("version", 0)],
)
def test_invalid_metadata_not_counted_in_buckets(source_bank, field, value):
    source_bank[0] = source_bank[0].model_copy(update={field: value})
    findings = validate_source_bank(source_bank)
    assert any(
        f.category == Category.INVALID_BUCKET_COUNT
        and f.context
        == "JUNIOR/PROGRAMMING/BASIC: expected 1 source record(s); found 0."
        for f in findings
    )


def test_multiple_invalid_metadata_fields_do_not_crash():
    item = question().model_copy(
        update={"grade": [], "competency": {}, "difficulty": None, "version": "bad"}
    )
    assert {
        Category.INVALID_GRADE,
        Category.INVALID_COMPETENCY,
        Category.INVALID_DIFFICULTY,
        Category.INVALID_VERSION,
    } <= categories([item])


def test_supersedes_self_reference_rejected():
    assert Category.INVALID_SUPERSEDES in categories([question("self", "self")])


def test_two_node_supersedes_cycle_rejected():
    questions = [question("a", "b"), question("b", "a")]
    assert Category.SUPERSEDES_CYCLE in categories(questions)


def test_longer_supersedes_cycle_rejected():
    questions = [question("a", "b"), question("b", "c"), question("c", "a")]
    assert Category.SUPERSEDES_CYCLE in categories(questions)


def test_cycle_reached_from_another_record_and_disjoint_cycles():
    questions = [
        question("entry", "a"),
        question("a", "b"),
        question("b", "a"),
        question("c", "d"),
        question("d", "c"),
    ]
    cycles = [
        f
        for f in validate_source_bank(questions)
        if f.category == Category.SUPERSEDES_CYCLE
    ]
    assert [(f.code, f.context) for f in cycles] == [
        ("a", "Cycle among source codes: a, b."),
        ("c", "Cycle among source codes: c, d."),
    ]


@pytest.mark.parametrize("predecessor_present", [True, False])
def test_duplicate_predecessor_ownership_rejected(predecessor_present):
    questions = [question("first", "previous"), question("second", "previous")]
    if predecessor_present:
        questions.append(question("previous"))
    assert Category.INVALID_SUPERSEDES in categories(questions)


def test_missing_historical_predecessor_allowed():
    findings = categories([question("new-version", "absent-old-version")])
    assert Category.INVALID_SUPERSEDES not in findings
    assert Category.SUPERSEDES_CYCLE not in findings


def test_real_v2_replacements_allow_missing_predecessors(source_bank):
    codes = {q.code for q in source_bank}
    replacements = [q for q in source_bank if q.supersedes is not None]
    assert len(replacements) == 2
    assert all(q.version == 2 and q.supersedes not in codes for q in replacements)
    assert validate_source_bank(source_bank) == []


def test_supersedes_chain_and_version_order_are_not_restricted():
    questions = [question("a", "b"), question("b", "historical")]
    findings = categories(questions)
    assert Category.INVALID_SUPERSEDES not in findings
    assert Category.SUPERSEDES_CYCLE not in findings


@pytest.mark.parametrize("supersedes", ["", " \t\n"])
def test_blank_supersedes_rejected(supersedes):
    assert Category.INVALID_SUPERSEDES in categories([question("new", supersedes)])


def test_duplicate_codes_do_not_create_ambiguous_graph_findings():
    questions = [question("a", "b"), question("a", "a"), question("b", "a")]
    findings = categories(questions)
    assert Category.DUPLICATE_CODE in findings
    assert Category.SUPERSEDES_CYCLE not in findings
    assert Category.INVALID_SUPERSEDES not in findings


@pytest.mark.parametrize("correct_index", [0, 1, 2, 3])
def test_diagnostics_do_not_expose_answers_options_key_or_index(correct_index):
    secret_answer = "SENSITIVE_OPTION_TEXT"
    secret_solution = "SENSITIVE_SOLUTION_EXPLANATION"
    secret_key = "SENSITIVE_ANSWER_KEY"
    secret_index = f"SENSITIVE_CORRECT_OPTION_INDEX_{correct_index}"
    item = question("safe-code").model_copy(
        update={
            "prompt": secret_solution,
            "options": [secret_answer, f" {secret_answer} ", secret_key, " "],
            "grade": secret_index,
            "competency": secret_key,
            "difficulty": secret_solution,
            "version": secret_answer,
            "answer_key": secret_key,
            "correct_option_index": correct_index,
        }
    )
    findings = validate_source_bank([item])
    assert {
        Category.INVALID_OPTIONS,
        Category.DUPLICATE_OPTION,
        Category.INVALID_GRADE,
        Category.INVALID_COMPETENCY,
        Category.INVALID_DIFFICULTY,
        Category.INVALID_VERSION,
    } <= {f.category for f in findings}
    representations = [
        str(findings),
        repr(findings),
        json.dumps([asdict(f) for f in findings]),
        *(str(f) for f in findings),
        *(repr(f) for f in findings),
        *(f.context for f in findings),
    ]
    for representation in representations:
        for forbidden in (
            secret_answer,
            secret_solution,
            secret_key,
            secret_index,
            "answer_key",
            "correct_option_index",
            "option_position",
        ):
            assert forbidden not in representation
    assert all(set(asdict(f)) == {"category", "code", "context"} for f in findings)
    changed_index = item.model_copy(
        update={"correct_option_index": (correct_index + 1) % 4}
    )
    assert validate_source_bank([changed_index]) == findings


def test_finding_is_immutable():
    finding = AssessmentValidationFinding(Category.BLANK_CODE, None, "Code is blank.")
    with pytest.raises(FrozenInstanceError):
        finding.code = "changed"


def test_deterministic_and_nonmutating(source_bank):
    source_bank[0] = source_bank[0].model_copy(
        update={"options": ["Alpha beta", " Alpha\t beta ", "Gamma", "Delta"]}
    )
    source_bank[1] = source_bank[1].model_copy(
        update={"supersedes": source_bank[1].code}
    )
    before = fingerprint(source_bank)
    first = validate_source_bank(source_bank)
    assert first
    assert validate_source_bank(source_bank) == first
    assert fingerprint(source_bank) == before


def test_empty_bank_findings_use_stable_inventory_order():
    findings = validate_source_bank([])
    assert len(findings) == 49
    assert findings[:4] == [
        AssessmentValidationFinding(
            Category.INVALID_TOTAL, None, "Expected 75 source records; found 0."
        ),
        AssessmentValidationFinding(
            Category.INVALID_GRADE_COUNT,
            None,
            "JUNIOR: expected 25 source records; found 0.",
        ),
        AssessmentValidationFinding(
            Category.INVALID_GRADE_COUNT,
            None,
            "MIDDLE: expected 25 source records; found 0.",
        ),
        AssessmentValidationFinding(
            Category.INVALID_GRADE_COUNT,
            None,
            "SENIOR: expected 25 source records; found 0.",
        ),
    ]
    assert findings[4].context == (
        "JUNIOR/PROGRAMMING/BASIC: expected 1 source record(s); found 0."
    )
    assert findings[-1].context == (
        "SENIOR/TESTING_SECURITY_DEBUGGING/ADVANCED: "
        "expected 1 source record(s); found 0."
    )


def test_validator_reads_no_files_or_database(source_bank, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Validator accessed a file or database")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "read_text", forbidden)
        patch.setattr(Session, "execute", forbidden)
        assert validate_source_bank(source_bank) == []
