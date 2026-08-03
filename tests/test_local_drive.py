"""本地驱动的功能测试。

``LocalDrive``/``OSDrive`` 没有任何第三方依赖，所以它是唯一能在 CI 里真正
跑起来的驱动，也因此充当 ``BaseDrive`` 契约的活基准：这里覆盖的行为，其它
驱动理应表现一致。

这些用例对应的历史问题（见 ``docs/AUDIT-2026-07.md``）：
* ``login()`` 抛 NotImplementedError；
* ``mkdir("/", name, return_if_exist=True)`` 因为签名是
  ``mkdir(path, exist_ok=True)``，把 ``name`` 绑到了 ``exist_ok``，
  结果 ``os.makedirs("/", exist_ok="name")`` 静默 no-op 却返回 True；
* ``get_file_list`` 返回 ``[{"path": ...}]`` 而非 ``DriveFile``，导致
  ``BaseDrive.download_dir`` 直接 ``AttributeError``；
* ``upload_file`` 把 ``fid`` 当文件路径，而基类传的是目录。
"""

import os

import pytest

from fundrive import get_drive
from fundrive.core import DriveFile


@pytest.fixture
def tree(workdir):
    """构造 src/{a.txt, sub/b.txt} 结构，cwd 已切到 tmp。"""
    (workdir / "src" / "sub").mkdir(parents=True)
    (workdir / "src" / "a.txt").write_text("hello")
    (workdir / "src" / "sub" / "b.txt").write_text("deep")
    return workdir


@pytest.fixture
def drive(tree):
    d = get_drive("local")
    assert d.login() is True
    return d


def test_login_succeeds_and_sets_state(drive):
    assert drive.is_logged_in is True
    assert drive.root_fid


def test_mkdir_returns_new_dir_fid_and_actually_creates_it(drive, tree):
    fid = drive.mkdir(".", "newdir", return_if_exist=True)
    assert os.path.isdir(fid), f"mkdir 返回了 {fid!r} 但目录并不存在"
    assert os.path.basename(fid) == "newdir"


def test_mkdir_return_if_exist_is_idempotent(drive):
    first = drive.mkdir(".", "dup")
    second = drive.mkdir(".", "dup", return_if_exist=True)
    assert first == second


def test_get_file_list_returns_drive_files(drive):
    files = drive.get_file_list("src")
    assert files, "src 下应当有文件"
    for f in files:
        assert isinstance(f, DriveFile), f"应返回 DriveFile，实为 {type(f).__name__}"
        assert f.fid and f.name  # BaseDrive.download_dir 依赖这两个属性
    assert {f.name for f in files} == {"a.txt"}


def test_get_dir_list_returns_drive_files(drive):
    dirs = drive.get_dir_list("src")
    assert {d.name for d in dirs} == {"sub"}
    assert all(isinstance(d, DriveFile) for d in dirs)


def test_download_dir_copies_tree_recursively(drive, tree):
    assert drive.download_dir("src", "out") is True
    assert (tree / "out" / "a.txt").read_text() == "hello"
    assert (tree / "out" / "sub" / "b.txt").read_text() == "deep"


def test_download_dir_respects_recursion_false(drive, tree):
    assert drive.download_dir("src", "flat", recursion=False) is True
    assert (tree / "flat" / "a.txt").is_file()
    assert not (tree / "flat" / "sub").exists()


def test_download_dir_honours_ignore_filter(drive, tree):
    drive.download_dir("src", "filtered", ignore_filter=lambda n: n == "a.txt")
    assert not (tree / "filtered" / "a.txt").exists()
    assert (tree / "filtered" / "sub" / "b.txt").is_file()


def test_upload_file_treats_fid_as_directory(drive, tree):
    """基类 upload_dir 传的 fid 是目录，不是目标文件路径。"""
    target_dir = drive.mkdir(".", "dest")
    assert drive.upload_file("src/a.txt", target_dir) is True
    assert (tree / "dest" / "a.txt").read_text() == "hello"


def test_upload_dir_roundtrips_through_returned_fids(drive, tree):
    """mkdir 返回的 fid 必须能再传回驱动，否则路径会被拼两遍。"""
    dest = drive.mkdir(".", "uploaded")
    assert drive.upload_dir("src", dest) is True
    assert (tree / "uploaded" / "a.txt").is_file()
    assert (tree / "uploaded" / "sub" / "b.txt").is_file()


def test_download_file_to_current_dir_without_save_dir(drive, tree):
    """不给 save_dir 时应落到当前目录，而不是 os.makedirs("") 崩掉。"""
    assert drive.download_file("src/a.txt") is True
    assert (tree / "a.txt").read_text() == "hello"


def test_download_file_respects_overwrite(drive, tree):
    assert drive.download_file("src/a.txt", filepath="copy.txt") is True
    assert drive.download_file("src/a.txt", filepath="copy.txt") is False
    assert drive.download_file("src/a.txt", filepath="copy.txt", overwrite=True) is True


def test_file_info_returns_none_when_missing(drive):
    assert drive.get_file_info("src/a.txt").name == "a.txt"
    assert drive.get_file_info("src/nope.txt") is None
    assert drive.get_dir_info("src").name == "src"
    assert drive.get_dir_info("src/a.txt") is None  # 文件不是目录


def test_delete_file_and_dir(drive, tree):
    assert drive.delete("src/a.txt") is True
    assert not (tree / "src" / "a.txt").exists()
    assert drive.delete("src") is True
    assert not (tree / "src").exists()
    assert drive.delete("src") is False  # 已不存在


def test_rename_move_copy(drive, tree):
    dest = drive.mkdir(".", "box")
    assert drive.copy("src/a.txt", dest) is True
    assert (tree / "box" / "a.txt").is_file()
    assert drive.rename(os.path.join(dest, "a.txt"), "renamed.txt") is True
    assert (tree / "box" / "renamed.txt").is_file()
    other = drive.mkdir(".", "box2")
    assert drive.move(os.path.join(dest, "renamed.txt"), other) is True
    assert (tree / "box2" / "renamed.txt").is_file()
    assert not (tree / "box" / "renamed.txt").exists()


def test_search_finds_by_substring(drive):
    names = {f.name for f in drive.search("b.txt")}
    assert "b.txt" in names


def test_get_quota_reports_disk_usage(drive):
    quota = drive.get_quota()
    assert {"total", "used", "free"} <= set(quota)
    assert quota["total"] > 0


def test_get_download_url_is_file_uri(drive):
    assert drive.get_download_url("src/a.txt").startswith("file://")


def test_exist(drive):
    assert drive.exist("src/a.txt") is True
    assert drive.exist("src/nope") is False


class TestRootPathSandbox:
    """给定 root_path 时必须拒绝逃逸出去的路径。"""

    @pytest.fixture
    def sandboxed(self, tree):
        d = get_drive("local", root_path=str(tree / "src"))
        assert d.login() is True
        return d

    def test_relative_paths_resolve_inside_root(self, sandboxed):
        assert {f.name for f in sandboxed.get_file_list("/")} == {"a.txt"}

    def test_absolute_path_outside_root_is_rejected(self, sandboxed):
        assert sandboxed.exist("/etc/passwd") is False
        with pytest.raises(ValueError, match="越出 root_path"):
            sandboxed._resolve("/etc/passwd")

    def test_dotdot_traversal_is_rejected(self, sandboxed):
        with pytest.raises(ValueError, match="越出 root_path"):
            sandboxed._resolve("../../../etc/passwd")

    def test_returned_fids_are_accepted_back(self, sandboxed, tree):
        """驱动吐出的绝对 fid 必须能再传回去，且不被当成相对根的路径。"""
        sub = sandboxed.mkdir("/", "roundtrip")
        assert sandboxed.exist(sub) is True
        # upload_file 的第一个参数是**本地**路径（网盘之外），因此按 cwd 解析，
        # 不经过 root_path；第二个参数才是网盘内的 fid。
        assert sandboxed.upload_file(str(tree / "src" / "a.txt"), sub) is True
        assert [f.name for f in sandboxed.get_file_list(sub)] == ["a.txt"]
