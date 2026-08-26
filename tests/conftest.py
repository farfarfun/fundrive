"""pytest 公共配置。

``farlog`` 在被 import 时会在**当前工作目录**创建 ``logs/``（见
``docs/AUDIT-2026-07.md``）。为了不让测试在仓库里到处拉屎，也为了让测试能在
只读目录下跑，这里把整个会话的 cwd 切到临时目录。
"""

import os
import pathlib
import sys
import tempfile

import pytest

# 让测试直接跑源码树，不依赖是否 pip install 过
SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(scope="session", autouse=True)
def _isolated_cwd():
    """整个测试会话在临时目录里运行，避免污染仓库。"""
    original = os.getcwd()
    with tempfile.TemporaryDirectory(prefix="fundrive-tests-") as tmp:
        os.chdir(tmp)
        try:
            yield tmp
        finally:
            os.chdir(original)


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    """把 cwd 切到一个干净的 tmp_path，用于需要相对路径的用例。"""
    monkeypatch.chdir(tmp_path)
    return tmp_path
