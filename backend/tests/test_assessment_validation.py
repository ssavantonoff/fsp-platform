import json
from dataclasses import FrozenInstanceError, asdict
from hashlib import sha256
from pathlib import Path
from traceback import format_exception
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app import question_bank
from app.assessment_bank_config import LEGACY_BACKEND_BLUEPRINT
from app.assessment_validation import (
    AssessmentValidationCategory as Category,
)
from app.assessment_validation import (
    AssessmentValidationFinding,
    validate_source_bank,
)
from app.models import Difficulty, Grade, Specialization
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
    assert len(source_bank) == 120
    assert validate_source_bank(source_bank) == []


@pytest.mark.parametrize("total", [119, 121])
def test_wrong_total_rejected(source_bank, total):
    questions = source_bank[:119] if total == 119 else [*source_bank, question()]
    assert Category.INVALID_TOTAL in categories(questions)


def test_wrong_grade_count_rejected(source_bank):
    source_bank[0] = source_bank[0].model_copy(update={"grade": Grade.MIDDLE})
    assert len(source_bank) == 120
    findings = validate_source_bank(source_bank)
    assert [
        f.context for f in findings if f.category == Category.INVALID_GRADE_COUNT
    ] == [
        "JUNIOR: expected 40 source records; found 39.",
        "MIDDLE: expected 40 source records; found 41.",
    ]


def test_wrong_bucket_difficulty_mix_rejected(source_bank):
    applied = next(i for i, q in enumerate(source_bank) if q.difficulty == "APPLIED")
    source_bank[applied] = source_bank[applied].model_copy(
        update={"difficulty": Difficulty.BASIC}
    )
    findings = validate_source_bank(source_bank)
    assert Category.INVALID_GRADE_COUNT not in {f.category for f in findings}
    assert [f.context for f in findings] == [
        "JUNIOR/PROGRAMMING/BASIC: expected 2 source record(s); found 3.",
        "JUNIOR/PROGRAMMING/APPLIED: expected 4 source record(s); found 3.",
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
        == "JUNIOR/PROGRAMMING/BASIC: expected 2 source record(s); found 1."
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


def test_real_versioned_replacements_allow_missing_predecessors(source_bank):
    codes = {q.code for q in source_bank}
    replacements = [q for q in source_bank if q.supersedes is not None]
    assert len(replacements) == 37
    assert sum(q.version == 2 for q in replacements) == 35
    assert sum(q.version == 3 for q in replacements) == 2
    assert all(q.supersedes not in codes for q in replacements)
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
            Category.INVALID_TOTAL, None, "Expected 120 source records; found 0."
        ),
        AssessmentValidationFinding(
            Category.INVALID_GRADE_COUNT,
            None,
            "JUNIOR: expected 40 source records; found 0.",
        ),
        AssessmentValidationFinding(
            Category.INVALID_GRADE_COUNT,
            None,
            "MIDDLE: expected 40 source records; found 0.",
        ),
        AssessmentValidationFinding(
            Category.INVALID_GRADE_COUNT,
            None,
            "SENIOR: expected 40 source records; found 0.",
        ),
    ]
    assert findings[4].context == (
        "JUNIOR/PROGRAMMING/BASIC: expected 2 source record(s); found 0."
    )
    assert findings[-1].context == (
        "SENIOR/TESTING_SECURITY_DEBUGGING/ADVANCED: "
        "expected 2 source record(s); found 0."
    )


def test_validator_reads_no_files_or_database(source_bank, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Validator accessed a file or database")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "read_text", forbidden)
        patch.setattr(Session, "execute", forbidden)
        assert validate_source_bank(source_bank) == []


SOURCE_SECRETS = (
    "PRIVATE_PROMPT_SENTINEL",
    "PRIVATE_OPTION_SENTINEL",
    "PRIVATE_ANSWER_KEY_SENTINEL",
)


@pytest.fixture
def temporary_source(tmp_path, monkeypatch):
    content = tmp_path / "content"
    content.mkdir()
    path = content / "backend_questions.json"
    monkeypatch.setattr(question_bank, "__file__", str(tmp_path / "question_bank.py"))

    def write(value, *, raw=False):
        path.write_text(value if raw else json.dumps(value))
        return path

    return write


@pytest.fixture
def raw_source_bank(source_bank):
    records = [item.model_dump(mode="json") for item in source_bank]
    for item in records:
        item["prompt"] = SOURCE_SECRETS[0]
        item["options"] = [f"{SOURCE_SECRETS[1]} {label}" for label in "ABCD"]
    return records


def assert_safe_loader_error(error):
    representations = [str(error), repr(error), "".join(format_exception(error))]
    for representation in representations:
        for forbidden in (*SOURCE_SECRETS, "answer_key", "correct_option_index"):
            assert forbidden not in representation
    assert error.__cause__ is None
    if error.__context__ is not None:
        # Raw parser context is suppressed by `raise ... from None`.
        assert error.__suppress_context__ is True


def test_loader_real_source_order_and_content_unchanged():
    path = Path(question_bank.__file__).parent / "content/backend_questions.json"
    expected = [
        SeedQuestion.model_validate(item) for item in json.loads(path.read_text())
    ]
    actual = load_bank()
    assert len(actual) == 120
    assert fingerprint(actual) == fingerprint(expected)
    assert validate_source_bank(actual) == []


def test_loader_reads_parses_and_validates_once(
    raw_source_bank, temporary_source, monkeypatch
):
    path = temporary_source(raw_source_bank)
    expected = [SeedQuestion.model_validate(item) for item in raw_source_bank]
    read_calls = []
    original_read = Path.read_bytes

    def read_once(source, *args, **kwargs):
        read_calls.append(source)
        return original_read(source, *args, **kwargs)

    parse_json = Mock(wraps=json.loads)
    original_parse = SeedQuestion.model_validate
    parsed = []

    def parse_record(item):
        result = original_parse(item)
        parsed.append(result)
        return result

    parse_question = Mock(wraps=parse_record)
    validate = Mock(wraps=validate_source_bank)
    monkeypatch.setattr(Path, "read_bytes", read_once)
    monkeypatch.setattr(json, "loads", parse_json)
    monkeypatch.setattr(SeedQuestion, "model_validate", parse_question)
    monkeypatch.setattr(question_bank, "validate_source_bank", validate)

    actual = load_bank()

    assert read_calls == [path]
    assert parse_json.call_count == 1
    assert parse_question.call_count == 120
    validate.assert_called_once_with(
        actual,
        specialization=Specialization.BACKEND,
        blueprint=LEGACY_BACKEND_BLUEPRINT,
    )
    assert validate.call_args.args[0] is actual
    assert all(item is parsed[i] for i, item in enumerate(actual))
    assert fingerprint(actual) == fingerprint(expected)
    codes = {item.code for item in actual}
    replacements = [item for item in actual if item.supersedes is not None]
    assert len(replacements) == 37
    assert sum(item.version == 2 for item in replacements) == 35
    assert sum(item.version == 3 for item in replacements) == 2
    assert all(item.supersedes not in codes for item in replacements)


def test_loader_invalid_json_has_safe_error(temporary_source):
    malformed = json.dumps(question().model_dump(mode="json"))[:-1]
    malformed += SOURCE_SECRETS[0] + SOURCE_SECRETS[1] + SOURCE_SECRETS[2]
    temporary_source(malformed, raw=True)
    with pytest.raises(ValueError) as error:
        load_bank()
    assert str(error.value) == "Invalid assessment source format"
    assert_safe_loader_error(error.value)


@pytest.mark.parametrize(
    "root", [{"prompt": SOURCE_SECRETS[0]}, SOURCE_SECRETS[1], None, 1, True]
)
def test_loader_non_list_root_has_safe_error(root, temporary_source):
    temporary_source(root)
    with pytest.raises(ValueError) as error:
        load_bank()
    assert str(error.value) == "Invalid assessment source format"
    assert_safe_loader_error(error.value)


@pytest.mark.parametrize(
    "field,value",
    [
        ("grade", "INVALID"),
        ("difficulty", "INVALID"),
        ("version", 0),
        ("options", [SOURCE_SECRETS[1]]),
        ("answer_key", SOURCE_SECRETS[2]),
    ],
)
def test_loader_pydantic_failures_have_safe_error(
    field, value, raw_source_bank, temporary_source
):
    raw_source_bank[0][field] = value
    temporary_source(raw_source_bank)
    with pytest.raises(ValueError) as error:
        load_bank()
    assert str(error.value) == "Invalid assessment source format"
    assert_safe_loader_error(error.value)


@pytest.mark.parametrize(
    "scenario,expected",
    [
        ("total", Category.INVALID_TOTAL),
        ("duplicate", Category.DUPLICATE_CODE),
        ("bucket", Category.INVALID_BUCKET_COUNT),
        ("options", Category.DUPLICATE_OPTION),
        ("conflict", Category.INVALID_SUPERSEDES),
        ("cycle", Category.SUPERSEDES_CYCLE),
    ],
)
def test_loader_structural_failures_have_safe_deterministic_error(
    scenario, expected, raw_source_bank, temporary_source
):
    first, second = raw_source_bank[:2]
    if scenario == "total":
        raw_source_bank.pop()
    elif scenario == "duplicate":
        second["code"] = first["code"]
    elif scenario == "bucket":
        first["difficulty"] = "APPLIED" if first["difficulty"] == "BASIC" else "BASIC"
    elif scenario == "options":
        first["options"][1] = f" \t{first['options'][0]}\n"
    elif scenario == "conflict":
        first["supersedes"] = second["supersedes"] = "absent-predecessor"
    elif scenario == "cycle":
        first["supersedes"], second["supersedes"] = second["code"], first["code"]
    temporary_source(raw_source_bank)
    with pytest.raises(ValueError) as error:
        load_bank()
    assert str(error.value).startswith("Invalid assessment source structure: ")
    assert expected.value in str(error.value)
    assert_safe_loader_error(error.value)
    with pytest.raises(ValueError) as repeated:
        load_bank()
    assert str(repeated.value) == str(error.value)
