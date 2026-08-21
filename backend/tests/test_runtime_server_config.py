from pathlib import Path


def test_gula_uvicorn_worker_has_conservative_defaults() -> None:
    from gula_uvicorn_worker import GulaUvicornWorker

    assert GulaUvicornWorker.CONFIG_KWARGS["limit_concurrency"] == 400
    assert GulaUvicornWorker.CONFIG_KWARGS["timeout_keep_alive"] == 5
    assert GulaUvicornWorker.CONFIG_KWARGS["timeout_graceful_shutdown"] == 30
    assert GulaUvicornWorker.CONFIG_KWARGS["limit_max_requests"] == 10000


def test_start_script_exposes_memory_safe_runtime_knobs() -> None:
    script = Path(__file__).parents[1] / "start_railway.sh"
    content = script.read_text()

    for setting in (
        "WEB_CONCURRENCY",
        "GUNICORN_TIMEOUT",
        "GUNICORN_GRACEFUL_TIMEOUT",
        "GUNICORN_KEEPALIVE",
        "GUNICORN_MAX_REQUESTS",
        "GUNICORN_MAX_REQUESTS_JITTER",
        "GUNICORN_BACKLOG",
    ):
        assert f"{setting}_VALUE" in content

    assert "gula_uvicorn_worker.GulaUvicornWorker" in content
    assert "--max-requests-jitter" in content
