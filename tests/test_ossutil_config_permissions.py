"""ossutil 驱动写出的凭据文件必须只有本人可读（SPEC §9.1）。

``_create_config_file()`` 会把阿里云 AccessKey ID/Secret 明文写进
``~/.fundrive/ossutil/config``。此前用默认权限创建（受 umask 影响，通常是
``0644``），同机器上的其他用户可以直接读到长期密钥。

``funinstall`` 属于 ``fundrive[ossutil]`` extra，CI 的裸环境不装，所以这里
在 import 驱动前把它替换成桩模块。
"""

import os
import stat
import sys
import types

import pytest


def _install_stubs():
    if "funinstall" not in sys.modules:
        try:
            import funinstall  # noqa: F401
        except ImportError:
            pkg = types.ModuleType("funinstall")
            install = types.ModuleType("funinstall.install")

            class _OSSUtilInstall:  # pragma: no cover - 仅用于满足 import
                pass

            install.OSSUtilInstall = _OSSUtilInstall
            pkg.install = install
            sys.modules["funinstall"] = pkg
            sys.modules["funinstall.install"] = install


_install_stubs()

from fundrive.drives.ossutil.drive import OSSUtilDrive  # noqa: E402


@pytest.fixture
def drive(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))  # Windows
    d = OSSUtilDrive()
    d._access_key = "AK-should-not-be-world-readable"
    d._access_secret = "SK-should-not-be-world-readable"
    d._endpoint = "oss-cn-hangzhou.aliyuncs.com"
    return d


def test_config_file_is_owner_only(drive, tmp_path):
    assert drive._create_config_file() is True

    config = tmp_path / ".fundrive" / "ossutil" / "config"
    assert config.exists()
    assert "AK-should-not-be-world-readable" in config.read_text(encoding="utf-8")

    mode = stat.S_IMODE(os.stat(config).st_mode)
    assert mode == 0o600, f"凭据文件权限是 {oct(mode)}，组/其他用户可读"

    dir_mode = stat.S_IMODE(os.stat(config.parent).st_mode)
    assert dir_mode == 0o700, f"凭据目录权限是 {oct(dir_mode)}"


def test_config_file_rewrite_keeps_permissions(drive, tmp_path):
    """已存在的宽权限文件也要被收紧，而不是沿用旧权限。"""
    config_dir = tmp_path / ".fundrive" / "ossutil"
    config_dir.mkdir(parents=True)
    config = config_dir / "config"
    config.write_text("stale", encoding="utf-8")
    os.chmod(config, 0o644)

    assert drive._create_config_file() is True
    assert stat.S_IMODE(os.stat(config).st_mode) == 0o600
    assert "stale" not in config.read_text(encoding="utf-8")
