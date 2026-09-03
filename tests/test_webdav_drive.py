"""WebDAV 驱动的 mock 契约测试。

``WebDavDrive`` 只依赖标准库 + ``requests``，不需要真实服务器就能测：这里
用 ``unittest.mock`` 打桩 ``requests.Session.request``，覆盖登录参数校验、
文件是否存在的状态码语义、目录列表解析和下载路径校验等公开 API 的正常路径
与边界条件（对应 SPEC.md §12.3 "发布到 PyPI 的包必须有 tests/"）。
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from fundrive.core.exceptions import InvalidParameterError
from fundrive.drives.webdav.drive import WebDavDrive

PROPFIND_RESPONSE = """<?xml version="1.0"?>
<d:multistatus xmlns:d="DAV:">
  <d:response>
    <d:href>/dav/docs/</d:href>
    <d:propstat>
      <d:prop>
        <d:displayname>docs</d:displayname>
        <d:resourcetype><d:collection/></d:resourcetype>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
  <d:response>
    <d:href>/dav/docs/sub/</d:href>
    <d:propstat>
      <d:prop>
        <d:displayname>sub</d:displayname>
        <d:resourcetype><d:collection/></d:resourcetype>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
  <d:response>
    <d:href>/dav/docs/a.txt</d:href>
    <d:propstat>
      <d:prop>
        <d:displayname>a.txt</d:displayname>
        <d:getcontentlength>5</d:getcontentlength>
        <d:resourcetype/>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
</d:multistatus>
"""


def _response(status_code=200, text=""):
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.text = text
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(response=resp)
    else:
        resp.raise_for_status.side_effect = None
    return resp


@pytest.fixture
def drive():
    return WebDavDrive()


def test_login_requires_all_credentials(drive):
    # password=None 时 login() 会回退读取本地 funsecret 配置；测试环境不应
    # 依赖开发机上是否恰好配置了 fundrive/webdav 密钥，因此显式打桩为空。
    with patch(
        "fundrive.drives.webdav.drive.read_secret", return_value=None
    ):
        with pytest.raises(InvalidParameterError):
            drive.login(
                server_url="https://dav.example.com", username="u", password=None
            )


def test_login_success_probes_root(drive):
    with patch.object(
        requests.Session, "request", return_value=_response(207)
    ) as mocked:
        assert (
            drive.login(
                server_url="https://dav.example.com/dav",
                username="u",
                password="p",
            )
            is True
        )
    assert mocked.call_args.kwargs["method"] == "PROPFIND"


def test_exist_returns_false_on_404(drive):
    drive.server_url = "https://dav.example.com/dav"
    drive.username, drive.password = "u", "p"
    drive._session = requests.Session()
    with patch.object(requests.Session, "request", return_value=_response(404)):
        assert drive.exist("/docs/missing.txt") is False


def test_exist_raises_on_server_error(drive):
    drive.server_url = "https://dav.example.com/dav"
    drive.username, drive.password = "u", "p"
    drive._session = requests.Session()
    with patch.object(requests.Session, "request", return_value=_response(500)):
        with pytest.raises(requests.HTTPError):
            drive.exist("/docs/a.txt")


def test_get_file_list_and_get_dir_list_parse_propfind(drive):
    drive.server_url = "https://dav.example.com/dav"
    drive.username, drive.password = "u", "p"
    drive._session = requests.Session()
    with patch.object(
        requests.Session, "request", return_value=_response(207, PROPFIND_RESPONSE)
    ):
        files = drive.get_file_list("/docs")
        dirs = drive.get_dir_list("/docs")

    assert {f.name for f in files} == {"a.txt"}
    assert files[0].size == 5
    # 目标目录自身 (docs) 也出现在 Depth=1 响应里，必须被过滤掉，只留子目录
    assert {d.name for d in dirs} == {"sub"}


def test_download_file_rejects_empty_local_path(drive):
    with pytest.raises(ValueError):
        drive.download_file("")


def test_upload_file_requires_existing_local_file(drive, tmp_path):
    missing = tmp_path / "nope.txt"
    with pytest.raises(FileNotFoundError):
        drive.upload_file(str(missing), "/docs")


def test_request_requires_login_first(drive):
    with pytest.raises(RuntimeError, match="please login first"):
        drive._request("PROPFIND", "/")
