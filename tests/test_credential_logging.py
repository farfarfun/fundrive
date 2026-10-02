"""凭据不得进入日志（SPEC §8.1 / §9.1）。

历史问题：``ZenodoClient`` 把 ``access_token`` 塞进 ``session.params``，于是

* 每个请求的 URL 查询串里都带着明文令牌；
* ``_check_response`` 把 ``response.url`` 原样写进 error 日志，令牌随之落盘。

Zenodo 官方文档本身就把 ``?access_token=`` 标注为 "less secure"，推荐
``Authorization: Bearer``。这里的用例覆盖两条防线：令牌只走请求头，以及
任何写日志的 URL 都要先过 :func:`fundrive.core.utils.sanitize_url`。
"""

from unittest.mock import MagicMock

import pytest
import requests

from fundrive.core.utils import REDACTED, redact_secrets, sanitize_url
from fundrive.drives.zenodo import drive as zenodo_drive

TOKEN = "zenodo-secret-token-42"


class _RecordingLogger:
    """只记录消息的假 logger，用来断言日志内容。"""

    def __init__(self):
        self.messages: list[str] = []

    def _record(self, msg, *args, **kwargs):
        self.messages.append(str(msg))

    info = warning = error = debug = _record

    @property
    def text(self) -> str:
        return "\n".join(self.messages)


@pytest.fixture
def recorded_logger(monkeypatch):
    logger = _RecordingLogger()
    monkeypatch.setattr(zenodo_drive, "logger", logger)
    return logger


# --------------------------------------------------------------------------
# sanitize_url
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url, expected",
    [
        (
            "https://zenodo.org/api/deposit?access_token=abc123",
            f"https://zenodo.org/api/deposit?access_token={REDACTED}",
        ),
        (
            "https://zenodo.org/api/deposit?page=2&ACCESS_TOKEN=abc123&size=10",
            f"https://zenodo.org/api/deposit?page=2&ACCESS_TOKEN={REDACTED}&size=10",
        ),
        (
            "https://example.com/x?token=t&api_key=k&password=p&signature=s",
            f"https://example.com/x?token={REDACTED}&api_key={REDACTED}"
            f"&password={REDACTED}&signature={REDACTED}",
        ),
        # 无查询串 / 无敏感参数时原样返回
        ("https://zenodo.org/api/deposit", "https://zenodo.org/api/deposit"),
        (
            "https://zenodo.org/api/deposit?page=2&size=10",
            "https://zenodo.org/api/deposit?page=2&size=10",
        ),
        ("", ""),
    ],
)
def test_sanitize_url(url, expected):
    assert sanitize_url(url) == expected


def test_sanitize_url_keeps_path_and_host():
    """脱敏不能把定位信息一起抹掉，否则日志就没用了。"""
    out = sanitize_url("https://sandbox.zenodo.org/api/records/999?access_token=abc")
    assert out.startswith("https://sandbox.zenodo.org/api/records/999?")
    assert "abc" not in out


# --------------------------------------------------------------------------
# ZenodoClient
# --------------------------------------------------------------------------


def test_token_goes_to_header_not_query():
    client = zenodo_drive.ZenodoClient(TOKEN)
    assert client.session.headers["Authorization"] == f"Bearer {TOKEN}"
    # session.params 必须为空：一旦有值，requests 会把它拼进每个请求的 URL
    assert not client.session.params


def test_make_request_does_not_put_token_in_params(monkeypatch):
    client = zenodo_drive.ZenodoClient(TOKEN)
    captured = {}

    def fake_request(method, url, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["params"] = kwargs.get("params")
        return MagicMock(spec=requests.Response)

    monkeypatch.setattr(client.session, "request", fake_request)
    client._make_request("GET", "deposit/depositions", params={"page": 2})

    assert captured["url"] == "https://zenodo.org/api/deposit/depositions"
    assert captured["params"] == {"page": 2}
    assert TOKEN not in str(captured["params"])
    assert TOKEN not in captured["url"]


def test_error_log_redacts_token_in_response_url(recorded_logger):
    """即使服务端重定向回来的 URL 带着令牌，日志里也必须打码。"""
    client = zenodo_drive.ZenodoClient(TOKEN)

    response = MagicMock(spec=requests.Response)
    response.status_code = 401
    response.url = f"https://zenodo.org/api/deposit/depositions?access_token={TOKEN}"
    response.json.return_value = {"message": "Unauthorized"}

    assert client._check_response(response, 200, "获取存储库列表") is False

    assert TOKEN not in recorded_logger.text
    assert REDACTED in recorded_logger.text
    # 仍要保留可定位的上下文
    assert "401" in recorded_logger.text
    assert "/api/deposit/depositions" in recorded_logger.text


def test_request_exception_log_redacts_token(monkeypatch, recorded_logger):
    client = zenodo_drive.ZenodoClient(TOKEN)

    def boom(method, url, **kwargs):
        raise requests.ConnectionError(f"failed to reach {url}?access_token={TOKEN}")

    monkeypatch.setattr(client.session, "request", boom)

    with pytest.raises(requests.ConnectionError):
        client._make_request(
            "GET", f"https://zenodo.org/api/records?access_token={TOKEN}"
        )

    assert TOKEN not in recorded_logger.text
    assert "/api/records" in recorded_logger.text


# --------------------------------------------------------------------------
# redact_secrets
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text, leaked",
    [
        ("GET https://zenodo.org/api?access_token=abc123 failed", "abc123"),
        ("HTTPSConnectionPool ... url: /api/x?token=tok-1&page=2", "tok-1"),
        ("payload: password=hunter2", "hunter2"),
        ("url%3Faccess_token%3Dabc123", "abc123"),
    ],
)
def test_redact_secrets(text, leaked):
    out = redact_secrets(text)
    assert leaked not in out
    assert REDACTED in out


def test_redact_secrets_keeps_other_text():
    out = redact_secrets("GET https://zenodo.org/api/records?page=2&size=10 -> 500")
    assert out == "GET https://zenodo.org/api/records?page=2&size=10 -> 500"
