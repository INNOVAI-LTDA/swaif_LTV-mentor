from app.storage.metric_repository import MetricRepository


def test_metric_repository_lists_by_pillar_and_rejects_duplicate_code(tmp_path) -> None:
    repo = MetricRepository(tmp_path / "metrics.json")
    created = repo.create(
        protocol_id="prt_1",
        pillar_id="plr_1",
        name="Comparecimento",
        code="comparecimento",
        direction="higher_better",
        unit="%",
    )

    listed = repo.list_by_pillar("plr_1")

    assert created["id"] == "met_1"
    assert len(listed) == 1
    assert listed[0]["pillar_id"] == "plr_1"

    try:
        repo.create(
            protocol_id="prt_1",
            pillar_id="plr_1",
            name="Presenca",
            code="comparecimento",
            direction="higher_better",
        )
    except ValueError as exc:
        assert str(exc) == "metric code already exists in pillar"
    else:
        raise AssertionError("ValueError was expected")
