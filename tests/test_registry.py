"""驱动注册表测试。

这些测试存在的原因：历史上 ``drives/__init__.py`` 把 5 个驱动的类名拼错了
（``OssDrive`` / ``WebDAVDrive`` / ``LanzouDrive`` / ``AliPanDrive`` /
``AliPanOpenDrive``），而所有 import 都包在 ``except ImportError: X = None``
里，于是**拼写错误和"依赖没装"产生完全相同的现象**——驱动静默消失，
``get_drive("oss")`` 报"不支持的驱动类型"。没有任何报错，持续了很多个版本。

:func:`test_spec_class_name_exists` 是防止复发的关键：它用 AST 静态比对，
**不需要装任何可选依赖**，所以在 CI 的裸环境里也能抓到类名拼错。
"""

import ast
import pathlib

import pytest

from fundrive.drives import DRIVE_SPECS, get_drive

DRIVES_DIR = pathlib.Path(__file__).resolve().parents[1] / "src" / "fundrive" / "drives"


def _names_bound_by(init_py: pathlib.Path):
    """收集某个包 ``__init__.py`` 绑定的所有名字（import + 赋值）。"""
    names = set()
    for node in ast.walk(ast.parse(init_py.read_text(encoding="utf-8"))):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return names


@pytest.mark.parametrize("key", sorted(DRIVE_SPECS))
def test_spec_class_name_exists(key):
    """注册表里的类名必须真的被对应子包导出（纯静态，不需要装依赖）。"""
    spec = DRIVE_SPECS[key]
    init_py = DRIVES_DIR / spec.module.lstrip(".") / "__init__.py"
    assert init_py.is_file(), f"{key}: 找不到 {init_py}"

    exported = _names_bound_by(init_py)
    assert spec.cls in exported, (
        f"注册表 key {key!r} 声明的类 {spec.cls!r} 并未被 "
        f"{spec.module}/__init__.py 导出。该模块导出的驱动类为: "
        f"{sorted(n for n in exported if n.endswith('Drive'))}。"
        f"这类拼写错误会被 ImportError 掩盖成'依赖未安装'，必须靠本测试拦住。"
    )


def test_no_duplicate_class_module_pairs_with_different_extras():
    """同一个驱动类在不同 key 下的 extra 必须一致，否则安装提示会互相矛盾。"""
    by_target = {}
    for key, spec in DRIVE_SPECS.items():
        by_target.setdefault((spec.module, spec.cls), []).append((key, spec.extra))
    for target, entries in by_target.items():
        extras = {extra for _, extra in entries}
        assert len(extras) == 1, f"{target} 在不同 key 下 extra 不一致: {entries}"


def test_declared_extras_exist_in_pyproject():
    """注册表引用的每个 pip extra 都必须在 pyproject.toml 里真实存在。"""
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
        pytest.skip("需要 tomllib")

    pyproject = pathlib.Path(__file__).resolve().parents[1] / "pyproject.toml"
    declared = set(
        tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"][
            "optional-dependencies"
        ]
    )
    referenced = {spec.extra for spec in DRIVE_SPECS.values() if spec.extra}
    missing = referenced - declared
    assert not missing, f"注册表引用了 pyproject 中不存在的 extra: {sorted(missing)}"


def test_get_drive_rejects_unknown_type():
    with pytest.raises(ValueError, match="不支持的驱动类型"):
        get_drive("definitely-not-a-drive")


def test_get_drive_is_case_insensitive():
    """key 大小写不敏感（get_drive 内部会 lower()）。"""
    assert "LOCAL".lower() in DRIVE_SPECS
    assert type(get_drive("LOCAL")).__name__ == "LocalDrive"


def test_missing_dependency_gives_actionable_hint():
    """依赖缺失时必须给出可执行的 pip 命令，而不是'不支持的驱动类型'。"""
    from fundrive.drives import list_missing_drives

    for key, hint in list_missing_drives().items():
        assert hint.startswith("fundrive"), f"{key} 的安装提示不合理: {hint}"
        with pytest.raises(ImportError) as excinfo:
            get_drive(key)
        assert "pip install" in str(excinfo.value)


def test_import_fundrive_does_not_pull_optional_sdks():
    """``import fundrive`` 必须是廉价的：不能把 22 个驱动的 SDK 全拖进来。"""
    import subprocess
    import sys

    code = (
        "import sys; import fundrive; "
        "heavy = {'oss2','boto3','botocore','dropbox','aligo','p115client',"
        "'webdav4','googleapiclient'}; "
        "print(sorted(m for m in sys.modules if m.split('.')[0] in heavy))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": str(DRIVES_DIR.parents[1])},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "[]", (
        f"import fundrive 意外导入了可选 SDK: {result.stdout.strip()}"
    )
