from concurrent.futures import ThreadPoolExecutor
from threading import Event
from time import monotonic

import pytest
from sqlalchemy import select, text

from app.errors import ApiError
from app.models import EmployerNeed, NeedStatus, User
from app.need_schemas import NeedWrite
from app.services import employer_needs

BASE = "/employer/needs"
ROUTES = [
    ("GET", ""),
    ("POST", ""),
    ("GET", "/missing"),
    ("PUT", "/missing"),
    ("POST", "/missing/activate"),
    ("POST", "/missing/close"),
]


def test_employer_creates_own_draft(client, employer_account, need_data, db_factory):
    _, profile = employer_account()
    response = client.post(BASE, json=need_data)
    assert response.status_code == 201, response.text
    result = response.json()
    assert result["employer_id"] == profile["id"]
    assert result["status"] == "DRAFT"
    assert {s["id"] for s in result["must_have_skills"]} == set(
        need_data["must_have_skill_ids"]
    )
    assert {s["id"] for s in result["nice_to_have_skills"]} == set(
        need_data["nice_to_have_skill_ids"]
    )
    assert [s["name"] for s in result["must_have_skills"]] == ["Django", "Python"]
    with db_factory() as db:
        need = db.scalar(select(EmployerNeed).where(EmployerNeed.id == result["id"]))
        assert need.employer_id == profile["id"]
        assert need.status == NeedStatus.DRAFT
        assert len(need.skill_requirements) == 3
    assert client.get(f"{BASE}/{result['id']}").json() == result


@pytest.mark.parametrize("method,path", ROUTES)
@pytest.mark.parametrize("role,status", [(None, 401), ("CANDIDATE", 403)])
def test_need_routes_require_employer(
    client, account, need_data, method, path, role, status
):
    if role:
        account(role=role)
    response = client.request(
        method,
        BASE + path,
        json=need_data
        if method in {"PUT", "POST"} and not path.endswith(("activate", "close"))
        else None,
    )
    assert response.status_code == status, response.text


def create_need(client, employer_account, need_data):
    employer_account()
    response = client.post(BASE, json=need_data)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def persisted(db_factory, need_id):
    with db_factory() as db:
        need = db.get(EmployerNeed, need_id)
        return (
            tuple(
                getattr(need, column.name) for column in EmployerNeed.__table__.columns
            ),
            sorted((link.skill_id, link.kind) for link in need.skill_requirements),
        )


@pytest.mark.parametrize(
    "method,suffix",
    [("GET", ""), ("PUT", ""), ("POST", "/activate"), ("POST", "/close")],
)
@pytest.mark.parametrize("foreign", [True, False])
def test_need_routes_hide_foreign_and_missing_ids(
    client, employer_account, need_data, method, suffix, foreign
):
    foreign_id = create_need(client, employer_account, need_data)
    employer_account("other@example.com")
    own = client.post(BASE, json=need_data).json()["id"]
    target = foreign_id if foreign else "missing"
    response = client.request(
        method, f"{BASE}/{target}{suffix}", json=need_data if method == "PUT" else None
    )
    assert response.status_code == 404, response.text
    assert response.json()["error"]["code"] == "need_not_found"
    page = client.get(BASE).json()
    assert [item["id"] for item in page["items"]] == [own]
    assert page["total"] == 1


@pytest.mark.parametrize(
    "method,suffix",
    [
        ("POST", ""),
        ("PUT", "/{id}"),
        ("POST", "/{id}/activate"),
        ("POST", "/{id}/close"),
    ],
)
@pytest.mark.parametrize("origin", [None, "https://untrusted.example"])
def test_need_mutations_require_trusted_origin(
    client, employer_account, need_data, db_factory, method, suffix, origin
):
    need_id = create_need(client, employer_account, need_data)
    before = persisted(db_factory, need_id)
    headers = {} if origin is None else {"Origin": origin}
    client.headers.pop("Origin")
    response = client.request(
        method,
        BASE + suffix.format(id=need_id),
        json=need_data if method == "PUT" or not suffix else None,
        headers=headers,
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "untrusted_origin"
    assert persisted(db_factory, need_id) == before
    with db_factory() as db:
        assert len(list(db.scalars(select(EmployerNeed)))) == 1


@pytest.mark.parametrize("method,path", ROUTES)
def test_need_requires_employer_profile(
    client, account, need_data, db_factory, method, path
):
    account(role="EMPLOYER")
    response = client.request(
        method,
        BASE + path,
        json=need_data
        if method in {"PUT", "POST"} and not path.endswith(("activate", "close"))
        else None,
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "profile_not_found"
    with db_factory() as db:
        assert list(db.scalars(select(EmployerNeed))) == []


INVALID = [
    ("empty_title", {"position_title": ""}),
    ("blank_title", {"position_title": "   "}),
    ("long_title", {"position_title": "x" * 201}),
    ("empty_description", {"description": ""}),
    ("blank_description", {"description": " \n "}),
    ("salary_order", {"salary_from": "300000"}),
    ("negative_from", {"salary_from": "-0.01"}),
    ("negative_to", {"salary_to": "-0.01"}),
    ("salary_nan", {"salary_from": "NaN"}),
    ("salary_infinity", {"salary_to": "Infinity"}),
    ("salary_digits", {"salary_to": "10000000000.00"}),
    ("salary_places", {"salary_to": "200000.001"}),
    ("target_nan", {"target_experience_years": "NaN"}),
    ("target_infinity", {"target_experience_years": "Infinity"}),
    ("target_negative", {"target_experience_years": -0.1}),
    ("duplicate_must", {}),
    ("duplicate_nice", {}),
    ("overlap", {}),
    ("zero_must", {"must_have_skill_ids": []}),
]


def invalid_data(need_data, name, changes):
    result = {**need_data, **changes}
    first = need_data["must_have_skill_ids"][0]
    if name == "duplicate_must":
        result["must_have_skill_ids"] = [first, first]
    elif name == "duplicate_nice":
        result["nice_to_have_skill_ids"] = [need_data["nice_to_have_skill_ids"][0]] * 2
    elif name == "overlap":
        result["nice_to_have_skill_ids"] = [first]
    return result


@pytest.mark.parametrize("name,changes", INVALID, ids=[case[0] for case in INVALID])
def test_need_input_validation(
    client, employer_account, need_data, db_factory, name, changes
):
    employer_account()
    response = client.post(BASE, json=invalid_data(need_data, name, changes))
    assert response.status_code == 422, response.text
    assert response.json()["error"]["code"] == "validation_error"
    with db_factory() as db:
        assert list(db.scalars(select(EmployerNeed))) == []


@pytest.mark.parametrize(
    "field",
    [
        "employer_id",
        "owner",
        "status",
        "score",
        "eligibility",
        "grade_fit",
        "verified_grade",
        "normalized_assessment_score",
        "assessment_verified_at",
    ],
)
def test_need_rejects_mass_assignment(
    client, employer_account, need_data, db_factory, field
):
    employer_account()
    response = client.post(BASE, json={**need_data, field: "untrusted"})
    assert response.status_code == 422
    with db_factory() as db:
        assert list(db.scalars(select(EmployerNeed))) == []


@pytest.mark.parametrize("active", [False, True])
def test_unknown_need_skill_rejected(
    client, employer_account, need_data, db_factory, active
):
    need_id = create_need(client, employer_account, need_data)
    if active:
        assert client.post(f"{BASE}/{need_id}/activate").status_code == 200
    before = persisted(db_factory, need_id)
    invalid = {
        **need_data,
        "position_title": "Changed",
        "must_have_skill_ids": ["unknown"],
        "nice_to_have_skill_ids": [],
    }
    response = client.put(f"{BASE}/{need_id}", json=invalid)
    assert response.status_code == 422, response.text
    assert response.json()["error"] == {
        "code": "unknown_skill",
        "message": "Выбран неизвестный навык.",
        "fields": [],
    }
    assert persisted(db_factory, need_id) == before
    assert client.post(BASE, json=invalid).status_code == 422
    with db_factory() as db:
        assert len(list(db.scalars(select(EmployerNeed)))) == 1


def test_need_lifecycle_and_editing(client, employer_account, need_data):
    need_id = create_need(client, employer_account, need_data)
    path = f"{BASE}/{need_id}"
    assert client.post(path + "/close").status_code == 409
    updated = {**need_data, "position_title": "Draft edited"}
    response = client.put(path, json=updated)
    assert response.status_code == 200
    assert response.json()["position_title"] == "Draft edited"
    response = client.post(path + "/activate")
    assert response.status_code == 200
    assert response.json()["status"] == "ACTIVE"
    assert (
        client.post(path + "/activate").json()["error"]["code"] == "need_state_conflict"
    )
    response = client.put(
        path,
        json={
            **updated,
            "position_title": "Active edited",
            "target_experience_years": 0,
        },
    )
    assert response.status_code == 200
    assert response.json()["position_title"] == "Active edited"
    assert response.json()["target_experience_years"] == 0
    response = client.post(path + "/close")
    assert response.status_code == 200
    assert response.json()["status"] == "CLOSED"
    for transition in ("activate", "close"):
        response = client.post(path + "/" + transition)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "need_state_conflict"


def test_need_skill_kind_reassignment(client, employer_account, need_data, db_factory):
    need_id = create_need(client, employer_account, need_data)
    before = persisted(db_factory, need_id)
    first, second = need_data["must_have_skill_ids"]
    response = client.put(
        f"{BASE}/{need_id}",
        json={
            **need_data,
            "must_have_skill_ids": [second],
            "nice_to_have_skill_ids": [first],
        },
    )
    assert response.status_code == 200, response.text
    assert [s["id"] for s in response.json()["must_have_skills"]] == [second]
    assert [s["id"] for s in response.json()["nice_to_have_skills"]] == [first]
    after = persisted(db_factory, need_id)
    assert dict(after[1]) == {first: "NICE_TO_HAVE", second: "MUST_HAVE"}
    # The skills-only update must advance the parent timestamp.
    columns = list(EmployerNeed.__table__.columns.keys())
    assert (
        after[0][columns.index("updated_at")] > before[0][columns.index("updated_at")]
    )


def test_closed_need_update_is_immutable(
    client, employer_account, need_data, db_factory
):
    need_id = create_need(client, employer_account, need_data)
    path = f"{BASE}/{need_id}"
    assert client.post(path + "/activate").status_code == 200
    assert client.post(path + "/close").status_code == 200
    before = persisted(db_factory, need_id)
    response = client.put(
        path,
        json={
            **need_data,
            "position_title": "Changed",
            "must_have_skill_ids": need_data["nice_to_have_skill_ids"],
            "nice_to_have_skill_ids": [],
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "need_state_conflict"
    assert persisted(db_factory, need_id) == before


@pytest.mark.parametrize("name,changes", INVALID, ids=[case[0] for case in INVALID])
def test_invalid_active_update_is_atomic(
    client, employer_account, need_data, db_factory, name, changes
):
    need_id = create_need(client, employer_account, need_data)
    path = f"{BASE}/{need_id}"
    assert client.post(path + "/activate").status_code == 200
    before = persisted(db_factory, need_id)
    attempted = {
        **need_data,
        "position_title": "Changed",
        "description": "Changed description",
        "must_have_skill_ids": need_data["nice_to_have_skill_ids"],
        "nice_to_have_skill_ids": [],
    }
    # Keep the duplicate/overlap test inputs independent from the scalar edits.
    invalid = invalid_data(need_data, name, changes)
    invalid_fields = set(changes)
    if name in {"duplicate_must", "duplicate_nice", "overlap"}:
        invalid_fields.update({"must_have_skill_ids", "nice_to_have_skill_ids"})
    attempted.update({key: invalid[key] for key in invalid_fields})
    response = client.put(path, json=attempted)
    assert response.status_code == 422, response.text
    assert persisted(db_factory, need_id) == before


@pytest.mark.parametrize("failure", ["flush", "commit"])
def test_active_update_persistence_failure_rolls_back(
    client, employer_account, need_data, db_factory, monkeypatch, failure
):
    from sqlalchemy.exc import IntegrityError

    need_id = create_need(client, employer_account, need_data)
    path = f"{BASE}/{need_id}"
    assert client.post(path + "/activate").status_code == 200
    before = persisted(db_factory, need_id)
    session_class = db_factory.class_
    original = getattr(session_class, failure)
    fired = False

    def fail_after_flush(session, *args, **kwargs):
        nonlocal fired
        # A service may explicitly flush before commit/DTO construction. Locate
        # the intended write by its values, so a clean identity map still injects
        # the same post-flush failure and exercises rollback.
        if not fired and any(
            isinstance(item, EmployerNeed)
            and item.id == need_id
            and item.position_title == "Changed"
            for item in session.identity_map.values()
        ):
            fired = True
            if failure == "flush":
                original(session, *args, **kwargs)
            else:
                session.flush()
            raise IntegrityError(
                "injected persistence failure", {}, Exception("constraint")
            )
        return original(session, *args, **kwargs)

    monkeypatch.setattr(session_class, failure, fail_after_flush)
    response = client.put(
        path,
        json={
            **need_data,
            "position_title": "Changed",
            "must_have_skill_ids": need_data["nice_to_have_skill_ids"],
            "nice_to_have_skill_ids": [],
        },
    )
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "need_conflict"
    assert fired
    assert persisted(db_factory, need_id) == before


def test_need_list_pagination(client, employer_account, need_data, db_factory):
    from datetime import UTC, datetime, timedelta

    create_need(client, employer_account, need_data)
    for index in range(22):
        assert (
            client.post(
                BASE, json={**need_data, "position_title": f"Need {index}"}
            ).status_code
            == 201
        )
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    with db_factory() as db:
        needs = list(db.scalars(select(EmployerNeed).order_by(EmployerNeed.id)))
        for need in needs:
            need.created_at = timestamp
        needs[-1].created_at = timestamp + timedelta(days=1)
        expected = [needs[-1].id] + [need.id for need in needs[:-1]]
        db.commit()
    response = client.get(BASE)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    page = response.json()
    assert set(page) == {"items", "total", "limit", "offset"}
    assert (page["total"], page["limit"], page["offset"]) == (23, 20, 0)
    assert [item["id"] for item in page["items"]] == expected[:20]
    page = client.get(BASE, params={"limit": 100, "offset": 2}).json()
    assert (page["total"], page["limit"], page["offset"]) == (23, 100, 2)
    assert [item["id"] for item in page["items"]] == expected[2:]
    assert client.get(BASE, params={"offset": 100}).json()["items"] == []
    for params in (
        {"limit": 0},
        {"limit": -1},
        {"limit": 101},
        {"limit": "bad"},
        {"offset": -1},
    ):
        assert client.get(BASE, params=params).status_code == 422


def test_close_racing_update_preserves_closed_state(
    database, db_factory, client, employer_account, need_data, monkeypatch
):
    if database.dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and pg_blocking_pids")
    user, _ = employer_account()
    response = client.post(BASE, json=need_data)
    assert response.status_code == 201, response.text
    need_id = response.json()["id"]
    assert client.post(f"{BASE}/{need_id}/activate").status_code == 200
    original = persisted(db_factory, need_id)
    preloaded, close_locked, update_attempted, release_close = (
        Event(),
        Event(),
        Event(),
        Event(),
    )
    timeout = 15
    pids = {}
    original_get_need = employer_needs.get_need

    def finish(future, stage):
        try:
            return future.result(timeout)
        except TimeoutError:
            pytest.fail(f"Timed out after {timeout}s waiting for {stage}")

    def controlled_get_need(db, owner, target, *, for_update=False):
        need = original_get_need(db, owner, target, for_update=for_update)
        if db.info.get("closer") and for_update:
            close_locked.set()
            assert release_close.wait(timeout), "Controller did not release close lock"
        return need

    monkeypatch.setattr(employer_needs, "get_need", controlled_get_need)

    def update():
        with database.connect() as connection, db_factory(bind=connection) as db:
            connection.detach()
            db.execute(text("SET LOCAL lock_timeout = '10s'"))
            db.execute(text("SET LOCAL statement_timeout = '12s'"))
            pids["update"] = db.scalar(text("SELECT pg_backend_pid()"))
            owner = db.get(User, user["id"])
            # Retain this strong reference across the blocking lock acquisition.
            cached = db.get(EmployerNeed, need_id)
            assert cached.status == NeedStatus.ACTIVE
            preloaded.set()
            assert close_locked.wait(timeout), "Close worker did not acquire row lock"
            update_attempted.set()
            with pytest.raises(ApiError) as error:
                employer_needs.update_need(
                    db,
                    owner,
                    need_id,
                    NeedWrite(
                        **{
                            **need_data,
                            "position_title": "Must not reopen or change CLOSED",
                            "description": "Rejected concurrent description",
                            "required_grade": "JUNIOR",
                            "target_experience_years": 99,
                            "must_have_skill_ids": need_data["nice_to_have_skill_ids"],
                            "nice_to_have_skill_ids": need_data["must_have_skill_ids"],
                        }
                    ),
                )
            assert (error.value.status, error.value.code) == (
                409,
                "need_state_conflict",
            )
            assert db.get(EmployerNeed, need_id) is cached
            assert cached.status == NeedStatus.CLOSED
            assert cached.position_title == need_data["position_title"]
            return pids["update"]

    def close():
        with database.connect() as connection, db_factory(bind=connection) as db:
            connection.detach()
            db.execute(text("SET LOCAL lock_timeout = '10s'"))
            db.execute(text("SET LOCAL statement_timeout = '12s'"))
            pids["close"] = db.scalar(text("SELECT pg_backend_pid()"))
            db.info["closer"] = True
            owner = db.get(User, user["id"])
            assert preloaded.wait(timeout), "Update worker did not preload ACTIVE"
            need = employer_needs.close_need(db, owner, need_id)
            assert need.status == NeedStatus.CLOSED
            return pids["close"]

    with ThreadPoolExecutor(max_workers=2) as workers:
        updating = workers.submit(update)
        closing = workers.submit(close)
        try:
            assert close_locked.wait(timeout), "Close did not get real row lock first"
            assert update_attempted.wait(timeout), "Update did not attempt its row lock"
            with database.connect() as connection, db_factory(bind=connection) as db:
                connection.detach()
                db.execute(text("SET LOCAL statement_timeout = '12s'"))
                observer_pid = db.scalar(text("SELECT pg_backend_pid()"))
                deadline = monotonic() + 5
                blockers = []
                while monotonic() < deadline:
                    blockers = db.scalar(
                        text("SELECT pg_blocking_pids(:pid)"), {"pid": pids["update"]}
                    )
                    if pids["close"] in blockers:
                        break
                assert pids["close"] in blockers, (
                    f"Update PID {pids['update']} never blocked on close PID "
                    f"{pids['close']}; last blockers={blockers}"
                )
            assert len({pids["update"], pids["close"], observer_pid}) == 3
            assert not updating.done() and not closing.done()
            release_close.set()
            assert finish(closing, "winning close commit") == pids["close"]
            assert finish(updating, "blocked update CLOSED rejection") == pids["update"]
        finally:
            release_close.set()
            # Also unblock an updater if close failed before its checkpoint.
            close_locked.set()
            preloaded.set()
    after = persisted(db_factory, need_id)
    columns = list(EmployerNeed.__table__.columns.keys())
    assert after[0][columns.index("status")] == NeedStatus.CLOSED
    assert after[1] == original[1]
    assert {
        key: value
        for key, value in zip(columns, after[0], strict=True)
        if key not in {"status", "updated_at"}
    } == {
        key: value
        for key, value in zip(columns, original[0], strict=True)
        if key not in {"status", "updated_at"}
    }
