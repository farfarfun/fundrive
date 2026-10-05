"""调用点契约回归测试。

``tests/test_drive_contract.py`` 只比对**方法定义**的形参名，抓不到**调用点**用错
参数名的情况。本轮审计就在调用点上抓到三个必崩/静默失效的缺陷：

* ``drives/tsinghua/drive.py`` 的模块级 ``download()`` 用 ``filedir=`` 调
  ``download_file`` / ``download_dir``，而两者的形参叫 ``save_dir``：文件会落到当前
  目录，目录下载因为 ``save_dir`` 是必填位置参数直接 ``TypeError``。
* ``drives/lanzou/snapshot.py`` 的 ``download()`` 用 ``dir_path=`` / ``url=`` 调
  ``LanZouDrive.download_file``，两个名字都不存在，必填的 ``fid`` 也没传。
* ``BaseDrive.__init__`` 把多余关键字参数转发给 ``object.__init__``，于是
  ``get_drive("dropbox", access_token="x")`` 必抛 ``TypeError``。

这些都不需要网络即可用静态/轻量方式守住。
"""

import ast
import pathlib

import pytest

from fundrive.core import BaseDrive
from fundrive.drives import get_drive

SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "fundrive"

# 下载类方法的本地保存目录统一叫 save_dir；历史上被写成 filedir 过。
_FORBIDDEN_KW = "filedir"
_DOWNLOAD_FUNCS = {"download_file", "download_dir"}


def _iter_python_files():
    for path in sorted(SRC.rglob("*.py")):
        yield path


def _calls_with_forbidden_kw(path: pathlib.Path):
    """返回该文件里用 ``filedir=`` 调用下载方法的 (函数名, 行号) 列表。"""
    hits = []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = getattr(func, "attr", None) or getattr(func, "id", None)
        if name not in _DOWNLOAD_FUNCS:
            continue
        if any(kw.arg == _FORBIDDEN_KW for kw in node.keywords):
            hits.append((name, node.lineno))
    return hits


def test_no_download_call_uses_filedir_kwarg():
    """src/ 下不允许再用 ``filedir=`` 调用 download_file / download_dir。"""
    offenders = {}
    for path in _iter_python_files():
        hits = _calls_with_forbidden_kw(path)
        if hits:
            offenders[str(path.relative_to(SRC))] = hits
    assert offenders == {}, f"下载调用点仍在用 filedir=（应为 save_dir=）：{offenders}"


def test_tsinghua_download_passes_save_dir():
    """清华云盘的向后兼容函数 ``download()`` 必须把 dir_path 作为 save_dir 传下去。"""
    source = (SRC / "drives" / "tsinghua" / "drive.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    func = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "download"
    )
    calls = [
        n
        for n in ast.walk(func)
        if isinstance(n, ast.Call) and getattr(n.func, "attr", None) in _DOWNLOAD_FUNCS
    ]
    assert len(calls) == 2, "download() 应当分别处理文件和目录两条分支"
    for call in calls:
        kwargs = {kw.arg for kw in call.keywords}
        assert "save_dir" in kwargs
        assert _FORBIDDEN_KW not in kwargs


def test_lanzou_snapshot_download_uses_real_parameter_names():
    """快照下载必须用 LanZouDrive.download_file 真实存在的参数名。"""
    drive_src = (SRC / "drives" / "lanzou" / "drive.py").read_text(encoding="utf-8")
    drive_tree = ast.parse(drive_src)
    cls = next(
        n
        for n in drive_tree.body
        if isinstance(n, ast.ClassDef) and n.name == "LanZouDrive"
    )
    method = next(
        n
        for n in cls.body
        if isinstance(n, ast.FunctionDef) and n.name == "download_file"
    )
    args = method.args
    accepted = {a.arg for a in args.args} | {a.arg for a in args.kwonlyargs}

    snap_src = (SRC / "drives" / "lanzou" / "snapshot.py").read_text(encoding="utf-8")
    snap_tree = ast.parse(snap_src)
    call = next(
        n
        for n in ast.walk(snap_tree)
        if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "download_file"
    )
    used = {kw.arg for kw in call.keywords}
    assert used <= accepted, f"快照用了不存在的参数：{sorted(used - accepted)}"
    # fid 是必填位置参数，必须显式给出（即便是 None）
    assert "fid" in used


def test_lanzou_move_file_returns_bool():
    """``move_file`` 必须返回比较结果，否则 ``move()`` 声明 -> bool 却恒返回 None。"""
    src = (SRC / "drives" / "lanzou" / "drive.py").read_text(encoding="utf-8")
    cls = next(
        n
        for n in ast.parse(src).body
        if isinstance(n, ast.ClassDef) and n.name == "LanZouDrive"
    )
    method = next(
        n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "move_file"
    )
    returns = [n for n in ast.walk(method) if isinstance(n, ast.Return)]
    assert returns and all(r.value is not None for r in returns)


def test_mkdir_never_returns_bool_literal():
    """``mkdir`` 按契约返回新目录的ID（str），返回 True/False 会被调用方当成ID。

    蓝奏云和115都踩过这个坑：``upload_dir`` 把 ``mkdir`` 的返回值当 fid 继续用，
    返回 ``True`` 会让后续上传全落到错误位置且不报错。
    """
    offenders = {}
    for path in _iter_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
            for method in cls.body:
                if not isinstance(method, ast.FunctionDef) or method.name != "mkdir":
                    continue
                bad = [
                    r.lineno
                    for r in ast.walk(method)
                    if isinstance(r, ast.Return)
                    and isinstance(r.value, ast.Constant)
                    and isinstance(r.value.value, bool)
                ]
                if bad:
                    offenders[f"{path.relative_to(SRC)}::{cls.name}"] = bad
    assert offenders == {}, f"mkdir 返回了布尔字面量（应返回目录ID）：{offenders}"


def test_no_named_kwarg_before_star_args():
    """``f(fid=x, *args)`` 这种写法只要 args 非空就必 TypeError。

    ``*args`` 会先去填第一个位置形参，和同名的关键字实参撞车，报
    ``got multiple values for argument``。``**kwargs`` 不受影响，所以只检查
    **具名**关键字与 ``*args`` 同时出现的调用。

    反过来 ``f(*fids, password=...)``（``*`` 写在具名关键字**之前**）是正常写法，
    不在检查范围内，按源码位置区分。
    """
    offenders = {}
    for path in _iter_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        hits = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            starred = [a for a in node.args if isinstance(a, ast.Starred)]
            named = [kw for kw in node.keywords if kw.arg is not None]
            if not starred or not named:
                continue
            star_pos = min((s.lineno, s.col_offset) for s in starred)
            kw_pos = min((k.value.lineno, k.value.col_offset) for k in named)
            if kw_pos < star_pos:
                name = getattr(node.func, "attr", None) or getattr(
                    node.func, "id", None
                )
                hits.append((name, node.lineno))
        # oss2.Bucket 的位置形参很多，这里只盯内部自有调用
        hits = [h for h in hits if h[0] not in {"Bucket"}]
        if hits:
            offenders[str(path.relative_to(SRC))] = hits
    assert offenders == {}, f"具名关键字与 *args 混用，args 非空必崩：{offenders}"


@pytest.mark.parametrize("kwargs", [{}, {"access_token": "x"}, {"a": 1, "b": 2}])
def test_base_drive_accepts_and_drops_extra_kwargs(kwargs):
    """BaseDrive 必须吞掉子类没消费的参数，不能转发给 object.__init__。"""
    drive = BaseDrive(**kwargs)
    assert drive.is_logged_in is False


def test_get_drive_with_extra_kwargs():
    """``get_drive`` 文档承诺把关键字参数透传给构造函数，不能因此崩。"""
    drive = get_drive("local", some_unused_option=True)
    assert drive is not None
