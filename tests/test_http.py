from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from lean.server import Handler, Server


@pytest.fixture
def server():
    value = Server(("127.0.0.1", 0), Handler)
    value.token = "synthetic-test-token-at-least24"
    thread = threading.Thread(target=value.serve_forever, daemon=True)
    thread.start()
    yield value
    value.shutdown()
    value.server_close()
    thread.join()


def test_real_http_lab_and_validation(server):
    base = f"http://127.0.0.1:{server.server_port}"

    def request(path, data=None, headers=None):
        req = urllib.request.Request(base + path, data=data, headers=headers or {})
        return urllib.request.urlopen(req, timeout=3)

    with pytest.raises(urllib.error.HTTPError) as error:
        request("/api/report")
    assert error.value.code == 401
    headers = {"Authorization": "Bearer " + server.token}
    with request(
        "/api/lab", json.dumps({"policy": "balanced", "task": "empty-mean"}).encode(), headers
    ) as response:
        result = json.load(response)
    assert result["cache_hits"] == 1 and result["invocations"] == 1
    assert result["first"]["after_tokens"] < result["first"]["before_tokens"]
    assert not result["inference_run"]
    for raw, expected in [
        (b"[]", 400),
        (b"x" * 65537, 413),
        (b'{"policy":"unknown","task":"x"}', 400),
    ]:
        with pytest.raises(urllib.error.HTTPError) as error:
            request("/api/lab", raw, headers)
        assert error.value.code == expected
    with pytest.raises(urllib.error.HTTPError) as error:
        request("/api/lab", b"{}", {**headers, "Origin": "https://other.invalid"})
    assert error.value.code == 403
    with request("/api/report", headers=headers) as response:
        assert json.load(response)["model"].startswith("HuggingFaceTB/")
