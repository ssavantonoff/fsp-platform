"""P8-B0-003: API DTOs must describe a complete committed version."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError

from app.models import CandidateProfile, EmployerNeed
from app.schemas import CandidateOut
from app.services import employer_needs
from tests.conftest import ORIGIN


def setup_entity(
    kind, client, account, employer_account, candidate_data, need_data, skill_ids
):
    if kind == "candidate":
        account()
        path = "/candidate/profile"
        scalar = "first_name"
        payload = {**candidate_data, "skill_ids": skill_ids[:1]}
    else:
        employer_account()
        path = "/employer/needs"
        scalar = "position_title"
        payload = {
            **need_data,
            "must_have_skill_ids": skill_ids[:1],
            "nice_to_have_skill_ids": [],
        }
    response = client.post(path, json={**payload, scalar: "version-A"})
    assert response.status_code == 201, response.text
    if kind == "need":
        path += "/" + response.json()["id"]
        assert client.post(path + "/activate").status_code == 200
    replacement = {**payload, scalar: "version-B"}
    replacement["skill_ids" if kind == "candidate" else "must_have_skill_ids"] = (
        skill_ids[1:2]
    )
    return path, scalar, payload, replacement


def version(kind, scalar, response):
    assert response.status_code == 200, response.text
    body = response.json()
    return body[scalar], [
        skill["id"]
        for skill in body["skills" if kind == "candidate" else "must_have_skills"]
    ]


@pytest.mark.parametrize("kind", ["candidate", "need"])
@pytest.mark.parametrize("expire_on_commit", [False, True])
def test_concurrent_put_response_is_a_real_committed_version(
    database,
    db_factory,
    client,
    app,
    account,
    employer_account,
    candidate_data,
    need_data,
    skill_ids,
    monkeypatch,
    kind,
    expire_on_commit,
):
    if database.dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL independent committed transactions")
    db_factory.configure(expire_on_commit=expire_on_commit)
    path, scalar, payload, replacement = setup_entity(
        kind, client, account, employer_account, candidate_data, need_data, skill_ids
    )
    model = CandidateProfile if kind == "candidate" else EmployerNeed
    captured, release, dto_built = Event(), Event(), Event()
    first_session = None
    pids = {}

    def before_flush(db, context, instances):
        nonlocal first_session
        if first_session is None and any(
            isinstance(row, model) and getattr(row, scalar) == "version-A"
            for row in db.dirty
        ):
            first_session = db
            pids["reader"] = (
                db.connection().connection.driver_connection.info.backend_pid
            )

    # The fixed path materializes DTO before commit. The legacy path instead
    # reaches a scalar refresh after commit; both checkpoints let B commit while
    # A's response is unfinished, without relying on a removed refresh call.
    original_candidate_out = CandidateOut.model_validate
    original_need_out = employer_needs.need_out

    def candidate_out(cls, entity, *args, **kwargs):
        value = original_candidate_out(entity, *args, **kwargs)
        if isinstance(entity, CandidateProfile) and entity.first_name == "version-A":
            dto_built.set()
        return value

    def need_out(entity):
        value = original_need_out(entity)
        if isinstance(entity, EmployerNeed) and entity.position_title == "version-A":
            dto_built.set()
        return value

    monkeypatch.setattr(CandidateOut, "model_validate", classmethod(candidate_out))
    monkeypatch.setattr(employer_needs, "need_out", need_out)

    def after_commit(db):
        if db is first_session:
            db.info["write_committed"] = True
            if dto_built.is_set():
                captured.set()
                assert release.wait(20), "Committed response DTO not released"

    original_refresh = db_factory.class_.refresh

    def refresh(db, entity, *args, **kwargs):
        if (
            db is first_session
            and isinstance(entity, model)
            and db.info.get("write_committed")
        ):
            db.info["target_response_refresh"] = True
        try:
            return original_refresh(db, entity, *args, **kwargs)
        finally:
            db.info.pop("target_response_refresh", None)

    monkeypatch.setattr(db_factory.class_, "refresh", refresh)

    def after_query(connection, cursor, statement, parameters, context, executemany):
        if (
            first_session is not None
            and first_session.info.get("target_response_refresh")
            and connection is first_session.connection()
            and "from " + model.__tablename__ in statement.lower()
            and " join " not in statement.lower()
        ):
            captured.set()
            assert release.wait(20), "Scalar response refresh not released"
        if (
            statement.lower().startswith("update " + model.__tablename__)
            and not captured.is_set()
        ):
            return
        if (
            statement.lower().startswith("update " + model.__tablename__)
            and captured.is_set()
        ):
            pids["writer"] = connection.connection.driver_connection.info.backend_pid

    event.listen(db_factory.class_, "before_flush", before_flush)
    event.listen(db_factory.class_, "after_commit", after_commit)
    event.listen(database, "after_cursor_execute", after_query)
    try:
        with TestClient(app, headers={"Origin": ORIGIN}) as peer:
            peer.cookies.update(client.cookies)
            with ThreadPoolExecutor(1) as pool:
                first = pool.submit(
                    peer.put, path, json={**payload, scalar: "version-A"}
                )
                try:
                    assert captured.wait(20), "No response reconstruction checkpoint"
                    second = client.put(path, json=replacement)
                    assert version(kind, scalar, second) == (
                        "version-B",
                        skill_ids[1:2],
                    )
                    assert not first.done(), (
                        "B must commit before A's response finishes"
                    )
                finally:
                    release.set()
                response = first.result(20)
        returned = version(kind, scalar, response)
        assert returned in [
            ("version-A", skill_ids[:1]),
            ("version-B", skill_ids[1:2]),
        ], returned
        assert pids["reader"] != pids["writer"]
        assert version(kind, scalar, client.get(path)) == ("version-B", skill_ids[1:2])
        print(
            {
                "kind": kind,
                "expire_on_commit": expire_on_commit,
                "pids": pids,
                "A_response": returned,
            }
        )
    finally:
        release.set()
        event.remove(db_factory.class_, "before_flush", before_flush)
        event.remove(db_factory.class_, "after_commit", after_commit)
        event.remove(database, "after_cursor_execute", after_query)


@pytest.mark.parametrize("kind", ["candidate", "need", "need_list"])
def test_get_response_uses_one_scalar_and_relation_snapshot(
    database,
    client,
    app,
    account,
    employer_account,
    candidate_data,
    need_data,
    skill_ids,
    kind,
):
    if database.dialect.name != "postgresql":
        pytest.skip("Requires PostgreSQL independent committed transactions")
    entity_kind = "need" if kind == "need_list" else kind
    path, scalar, _, replacement = setup_entity(
        entity_kind,
        client,
        account,
        employer_account,
        candidate_data,
        need_data,
        skill_ids,
    )
    table = "candidate_profiles" if kind == "candidate" else "employer_needs"
    captured, release = Event(), Event()
    paused = False

    def checkpoint(connection, cursor, statement, parameters, context, executemany):
        nonlocal paused
        sql = statement.lower()
        if not paused and "from " + table in sql and table + "." + scalar in sql:
            paused = True
            captured.set()
            assert release.wait(20)

    event.listen(database, "after_cursor_execute", checkpoint)
    try:
        with TestClient(app, headers={"Origin": ORIGIN}) as peer:
            peer.cookies.update(client.cookies)
            with ThreadPoolExecutor(1) as pool:
                first = pool.submit(
                    peer.get, "/employer/needs" if kind == "need_list" else path
                )
                try:
                    assert captured.wait(20)
                    assert client.put(path, json=replacement).status_code == 200
                    assert not first.done()
                finally:
                    release.set()
                response = first.result(20)
        assert response.status_code == 200, response.text
        body = response.json()["items"][0] if kind == "need_list" else response.json()
        skills = body["skills" if kind == "candidate" else "must_have_skills"]
        returned = (body[scalar], [skill["id"] for skill in skills])
        assert returned in [
            ("version-A", skill_ids[:1]),
            ("version-B", skill_ids[1:2]),
        ], returned
        assert version(entity_kind, scalar, client.get(path)) == (
            "version-B",
            skill_ids[1:2],
        )
    finally:
        release.set()
        event.remove(database, "after_cursor_execute", checkpoint)


@pytest.mark.parametrize("kind", ["candidate", "need"])
def test_commit_failure_never_returns_successful_prepared_dto(
    db_factory,
    client,
    app,
    account,
    employer_account,
    candidate_data,
    need_data,
    skill_ids,
    monkeypatch,
    kind,
):
    path, scalar, _, replacement = setup_entity(
        kind, client, account, employer_account, candidate_data, need_data, skill_ids
    )
    before = client.get(path).json()
    model = CandidateProfile if kind == "candidate" else EmployerNeed
    original_commit = db_factory.class_.commit
    flushed = []

    def fail(db):
        if any(
            isinstance(row, model) and getattr(row, scalar) == "failed-version"
            for row in db.identity_map.values()
        ):
            db.flush()
            flushed.append(True)
            raise IntegrityError(
                "injected commit failure", {}, Exception("synthetic failure")
            )
        return original_commit(db)

    monkeypatch.setattr(db_factory.class_, "commit", fail)
    with TestClient(
        app, headers={"Origin": ORIGIN}, raise_server_exceptions=False
    ) as owner:
        owner.cookies.update(client.cookies)
        response = owner.put(path, json={**replacement, scalar: "failed-version"})
    assert flushed == [True]
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == (
        "profile_conflict" if kind == "candidate" else "need_conflict"
    )
    assert client.get(path).json() == before
