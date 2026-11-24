import pytest
from sqlalchemy import event


@pytest.mark.parametrize("task_count", [3, 6])
def test_list_tasks_query_count(client, db_session, task_count):
    # 할 일 개수와 무관하게 GET /tasks의 SELECT가 2개(할 일 1회 + 태그 1회)인지 확인합니다.
    tag_sets = [["개인"], ["긴급"], ["개인", "긴급"]]
    for i in range(task_count):
        res = client.post(
            "/tasks", json={"title": f"할 일 {i}", "tags": tag_sets[i % len(tag_sets)]}
        )
        assert res.status_code == 201

    statements = []

    def count_select(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    engine = db_session.get_bind()
    event.listen(engine, "before_cursor_execute", count_select)
    try:
        res = client.get("/tasks")
    finally:
        event.remove(engine, "before_cursor_execute", count_select)

    assert res.status_code == 200
    assert len(res.json()) == task_count
    assert len(statements) == 2


def test_create_and_list(client):
    res = client.post("/tasks", json={"title": "테스트 할 일", "tags": ["개인", "긴급"]})
    assert res.status_code == 201
    body = res.json()
    assert body["title"] == "테스트 할 일"
    assert {t["name"] for t in body["tags"]} == {"개인", "긴급"}

    res = client.get("/tasks")
    assert res.status_code == 200
    tasks = res.json()
    assert len(tasks) == 1
    assert tasks[0]["tags"]
