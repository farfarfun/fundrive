"""``login()`` 不得把失败报告成成功（SPEC §8.2）。

历史问题：天池 / OpenXLab / 清华云盘三个驱动的 ``login()`` 在

* 探测接口返回非 200（401、403、500……），或
* 探测请求直接抛异常（网络不通、DNS 失败、超时）

两种情况下都打一条 warning 然后 ``return True``，于是"认证失败"被报告成
"登录成功"，后续每个操作都带着无效凭据去撞墙，调用方拿不到任何可判断的信号。

这些用例全部用桩替换 HTTP 层，不访问网络，也不需要任何可选依赖。
"""

from unittest.mock import MagicMock

import pytest
import requests

from fundrive.drives.openxlab import drive as openxlab_drive
from fundrive.drives.tianchi import drive as tianchi_drive
from fundrive.drives.tsinghua import drive as tsinghua_drive


def _response(status_code: int):
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    return resp


@pytest.fixture(autouse=True)
def _no_secret_lookup(monkeypatch):
    """禁止测试读取本机 funsecret 配置，保证用例可复现。"""
    for mod in (tianchi_drive, openxlab_drive, tsinghua_drive):
        monkeypatch.setattr(mod, "read_secret", lambda *a, **k: None)


# --------------------------------------------------------------------------
# 天池
# --------------------------------------------------------------------------


def _tianchi(monkeypatch, result):
    drive = tianchi_drive.TianChiDrive(
        tc_cookie="tc", csrf_cookie="csrf", csrf_token="token"
    )

    def fake_get(url, **kwargs):
        assert kwargs.get("timeout"), "探测请求必须带超时"
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(tianchi_drive.requests, "get", fake_get)
    return drive


def test_tianchi_login_ok(monkeypatch):
    assert _tianchi(monkeypatch, _response(200)).login() is True


@pytest.mark.parametrize("status", [302, 401, 403, 404, 500])
def test_tianchi_login_rejects_non_200(monkeypatch, status):
    assert _tianchi(monkeypatch, _response(status)).login() is False


@pytest.mark.parametrize(
    "exc",
    [
        requests.ConnectionError("dns failure"),
        requests.Timeout("timed out"),
    ],
)
def test_tianchi_login_rejects_probe_failure(monkeypatch, exc):
    assert _tianchi(monkeypatch, exc).login() is False


def test_tianchi_login_does_not_write_none_cookies(monkeypatch):
    """未配置的凭据不能以 None 写进 cookies/headers（requests 会报错）。"""
    drive = tianchi_drive.TianChiDrive()
    monkeypatch.setattr(tianchi_drive.requests, "get", lambda url, **kw: _response(401))
    assert drive.login() is False
    assert None not in drive.cookies.values()
    assert None not in drive.headers.values()


# --------------------------------------------------------------------------
# OpenXLab
# --------------------------------------------------------------------------


def _openxlab(monkeypatch, result):
    drive = openxlab_drive.OpenXLabDrive(opendatalab_session="sess", ssouid="uid")

    def fake_get(url, **kwargs):
        assert kwargs.get("timeout"), "探测请求必须带超时"
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(openxlab_drive.requests, "get", fake_get)
    return drive


def test_openxlab_login_ok(monkeypatch):
    assert _openxlab(monkeypatch, _response(200)).login() is True


@pytest.mark.parametrize("status", [302, 401, 403, 404, 500])
def test_openxlab_login_rejects_non_200(monkeypatch, status):
    assert _openxlab(monkeypatch, _response(status)).login() is False


@pytest.mark.parametrize(
    "exc",
    [
        requests.ConnectionError("dns failure"),
        requests.Timeout("timed out"),
    ],
)
def test_openxlab_login_rejects_probe_failure(monkeypatch, exc):
    assert _openxlab(monkeypatch, exc).login() is False


# --------------------------------------------------------------------------
# 清华云盘
# --------------------------------------------------------------------------


def _tsinghua(monkeypatch, result, share_key="share-key"):
    drive = tsinghua_drive.TSingHuaDrive(share_key=share_key)

    def fake_get(url, **kwargs):
        assert kwargs.get("timeout"), "探测请求必须带超时"
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(drive.session, "get", fake_get)
    return drive


def test_tsinghua_login_ok(monkeypatch):
    assert _tsinghua(monkeypatch, _response(200)).login() is True


@pytest.mark.parametrize("status", [401, 403, 404, 500])
def test_tsinghua_login_rejects_non_200(monkeypatch, status):
    assert _tsinghua(monkeypatch, _response(status)).login() is False


def test_tsinghua_login_rejects_probe_failure(monkeypatch):
    assert _tsinghua(monkeypatch, requests.Timeout("timed out")).login() is False


def test_tsinghua_login_requires_share_key(monkeypatch):
    """没有 share_key 的清华云盘驱动什么都做不了，不能返回登录成功。"""
    drive = tsinghua_drive.TSingHuaDrive()

    def must_not_be_called(*args, **kwargs):  # pragma: no cover - 防御性断言
        raise AssertionError("没有 share_key 时不应该发请求")

    monkeypatch.setattr(drive.session, "get", must_not_be_called)
    assert drive.login() is False
