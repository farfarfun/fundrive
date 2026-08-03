"""静态检查：所有 HTTP 调用都必须有超时。

一个没有超时的请求会在服务端挂住时永久挂死调用方。逐个调用点靠自觉写
``timeout=`` 是不可靠的（本项目历史上 88 个请求里 81 个漏了），因此：

* 优先用 :func:`fundrive.core.http.new_session`，它在会话层注入默认超时；
* 本测试用 AST 兜底，确保没人新增裸的 ``requests.get(...)`` 或在
  普通 ``requests.Session()`` 上发无超时请求。
"""

import ast
import pathlib

import pytest

SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "fundrive"

# 这些方法名出现在 requests / Session 上时视为发起 HTTP 请求
HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options", "request"}


def _http_calls_without_timeout(path: pathlib.Path):
    """返回 (行号, 源码片段) 列表，覆盖所有缺 timeout 的 HTTP 调用。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    findings = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in HTTP_METHODS:
            continue

        # 只关心接收者看起来像 requests 模块或某个 session 的调用
        receiver = node.func.value
        receiver_src = ast.unparse(receiver)
        if not (
            receiver_src == "requests"
            or "session" in receiver_src.lower()
            or receiver_src.endswith("_client")
        ):
            continue

        kwargs = {kw.arg for kw in node.keywords if kw.arg}
        if "timeout" in kwargs:
            continue
        # **kwargs 透传的情况无法静态判断，放行
        if any(kw.arg is None for kw in node.keywords):
            continue

        findings.append((node.lineno, f"{receiver_src}.{node.func.attr}(...)"))

    return findings


def _iter_source_files():
    return sorted(p for p in SRC.rglob("*.py") if p.name != "example.py")


@pytest.mark.parametrize(
    "path", _iter_source_files(), ids=lambda p: str(p.relative_to(SRC))
)
def test_no_http_call_without_timeout(path):
    """每个 HTTP 调用点要么显式带 timeout，要么走 TimeoutSession。"""
    source = path.read_text(encoding="utf-8")

    # 走 new_session()/TimeoutSession 的文件由会话层保证超时
    if "new_session(" in source or "TimeoutSession" in source:
        return

    findings = _http_calls_without_timeout(path)
    assert not findings, (
        f"{path.relative_to(SRC)} 存在无超时的 HTTP 调用：\n"
        + "\n".join(f"  L{ln}: {src}" for ln, src in findings)
        + "\n请改用 fundrive.core.http.new_session()，或显式传 timeout=。"
    )
