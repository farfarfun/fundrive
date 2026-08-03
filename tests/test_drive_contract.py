"""驱动契约一致性测试（纯静态，不需要安装任何可选依赖）。

``BaseDrive`` 不是 ABC，``@abstractmethod`` 因此完全失效，加上过去没有测试，
22 个驱动的方法签名各自漂移了很久：``save_dir`` 被改名成 ``filedir``、
``mkdir`` 丢掉 ``return_if_exist``、``get_quota`` 不收 ``*args`` ……这些都会让
通过基类接口调用的代码（``core/copy.py``、``BaseDrive.download_dir``）直接
抛 ``TypeError``。

本测试用 AST 比对每个驱动与 ``BaseDrive`` 的形参名，因此**新增的漂移会立刻
失败**。已知但尚未修的历史债记在 :data:`KNOWN_DIVERGENCES` 里，它是一份会
逐步缩短的清单，而不是一个被永久忽略的开关。
"""

import ast
import pathlib

import pytest

SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "fundrive"

# 已知的历史遗留漂移：{"<包名>.<类名>": {"<方法名>", ...}}
# 每一项都应当有明确的修复计划；清单只应变短，不应变长。
KNOWN_DIVERGENCES: dict[str, set[str]] = {}


def _public_methods(path: pathlib.Path, clsname=None):
    """提取类的公开方法签名信息。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result = {}
    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef):
            continue
        if clsname is not None:
            if cls.name != clsname:
                continue
        elif not any(getattr(b, "id", "") == "BaseDrive" for b in cls.bases):
            continue
        methods = {}
        for node in cls.body:
            if not isinstance(node, ast.FunctionDef) or node.name.startswith("_"):
                continue
            args = node.args
            methods[node.name] = {
                # 去掉 self
                "pos": [a.arg for a in args.posonlyargs + args.args][1:],
                "kwonly": [a.arg for a in args.kwonlyargs],
                "vararg": args.vararg is not None,
                "kwarg": args.kwarg is not None,
                "line": node.lineno,
            }
        result[cls.name] = methods
    return result


BASE = _public_methods(SRC / "core" / "base.py", clsname="BaseDrive")["BaseDrive"]
DRIVER_FILES = sorted(SRC.glob("drives/*/drive*.py"))


def _check(cls_key, name, sig):
    """返回该方法相对基类的偏差描述列表。"""
    base = BASE[name]
    problems = []

    for index, base_param in enumerate(base["pos"]):
        if index >= len(sig["pos"]):
            if base_param not in sig["kwonly"]:
                problems.append(f"缺少形参 {base_param!r}")
        elif (
            sig["pos"][index] != base_param
            and base_param not in sig["pos"]
            and base_param not in sig["kwonly"]
        ):
            problems.append(
                f"第 {index + 1} 个形参应为 {base_param!r}，实为 {sig['pos'][index]!r}"
            )

    if base["kwarg"] and not sig["kwarg"]:
        problems.append("缺少 **kwargs")
    if base["vararg"] and not sig["vararg"] and not sig["kwarg"]:
        problems.append("缺少 *args")
    return problems


@pytest.mark.parametrize("path", DRIVER_FILES, ids=lambda p: p.parent.name)
def test_driver_signatures_match_base(path):
    """驱动重写 BaseDrive 方法时，形参名和可变参数必须兼容。"""
    failures = []
    for cls_name, methods in _public_methods(path).items():
        cls_key = f"{path.parent.name}.{cls_name}"
        allowed = KNOWN_DIVERGENCES.get(cls_key, set())
        for name, sig in methods.items():
            if name not in BASE or name in allowed:
                continue
            for problem in _check(cls_key, name, sig):
                failures.append(f"  {cls_key}.{name} (L{sig['line']}): {problem}")

    assert not failures, (
        f"{path.relative_to(SRC)} 的签名与 BaseDrive 不兼容：\n"
        + "\n".join(failures)
        + "\n通过基类接口调用这些方法会抛 TypeError。"
    )


def test_known_divergences_are_still_real():
    """KNOWN_DIVERGENCES 里的条目如果已经修好，就应该从清单里删掉。"""
    stale = []
    for path in DRIVER_FILES:
        for cls_name, methods in _public_methods(path).items():
            cls_key = f"{path.parent.name}.{cls_name}"
            for name in KNOWN_DIVERGENCES.get(cls_key, set()):
                sig = methods.get(name)
                if sig and not _check(cls_key, name, sig):
                    stale.append(f"{cls_key}.{name}")
    assert not stale, (
        f"以下条目已经符合契约，请从 KNOWN_DIVERGENCES 中移除: {sorted(stale)}"
    )


@pytest.mark.parametrize("path", DRIVER_FILES, ids=lambda p: p.parent.name)
def test_driver_does_not_invent_parallel_method_names(path):
    """不要用 copy_object/move_object 这类别名代替契约里的 copy/move。

    ``S3Drive`` 曾经只提供 ``copy_object``/``move_object``，于是基类的
    ``copy``/``move`` 一直抛 NotImplementedError，而调用方看到有个长得很像的
    方法却不知道两者语义还不一样（一个把 target 当完整 key，一个当目录）。
    """
    aliases = {
        "copy_object": "copy",
        "move_object": "move",
        "create_share_link": "share",
        "move_file": "move",
    }
    for cls_name, methods in _public_methods(path).items():
        for alias, canonical in aliases.items():
            if alias in methods and canonical not in methods:
                pytest.fail(
                    f"{path.parent.name}.{cls_name} 定义了 {alias}() 但没有实现契约里的 "
                    f"{canonical}()，调用方通过 BaseDrive.{canonical}() 只会拿到 "
                    f"NotImplementedError。"
                )
