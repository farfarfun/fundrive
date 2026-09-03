"""本地文件系统驱动

把本地目录当作"网盘"来操作，主要用途：
* 作为 :func:`fundrive.core.copy_data` 的一端，在本地和远端之间搬数据；
* 作为其它驱动的参照实现——它没有任何第三方依赖，因此也是驱动契约的
  活文档和测试基准。

``fid`` 就是本地路径。``mkdir`` 返回新目录的路径（即它的 fid），与
:class:`~fundrive.core.BaseDrive` 的契约一致。
"""

import os
import shutil
from typing import Any
from collections.abc import Callable

from farlog import getLogger

from fundrive.core import BaseDrive, DriveFile
from fundrive.core.base import get_filepath

logger = getLogger("fundrive")


def _to_drive_file(path: str) -> DriveFile:
    """把本地路径转成 DriveFile。fid 用绝对路径，name 用文件名。"""
    abspath = os.path.abspath(path)
    try:
        stat = os.stat(abspath)
        size: int | None = stat.st_size if os.path.isfile(abspath) else None
        mtime: str | None = str(int(stat.st_mtime))
    except OSError:
        size, mtime = None, None
    return DriveFile(
        fid=abspath,
        name=os.path.basename(abspath.rstrip(os.sep)) or abspath,
        size=size,
        time=mtime,
        ext={"path": abspath, "is_dir": os.path.isdir(abspath)},
    )


class OSDrive(BaseDrive):
    """本地文件系统驱动。

    Args:
        root_path: 可选的根目录。给定后所有相对 fid 都相对它解析，
            且拒绝逃逸出该目录的路径（防目录穿越）。不给则以进程 cwd 为基准，
            不做任何限制。
    """

    def __init__(
        self, root_path: str | None = None, *args: Any, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.root_path = os.path.abspath(root_path) if root_path else None
        self._root_fid = self.root_path or os.path.abspath(os.curdir)

    # ------------------------------------------------------------------ 内部
    def _resolve(self, fid: str) -> str:
        """把 fid 解析成绝对路径；配置了 root_path 时禁止逃逸。

        本方法必须能接受自己吐出去的 fid（``mkdir`` / ``get_file_list`` 返回的
        都是绝对路径），否则 ``upload_dir`` 这类把 fid 回传的基类实现会把
        路径拼两遍。因此：

        * ``/`` / ``.`` / ``root`` —— 视为根目录；
        * 绝对路径 —— 原样采用（随后做边界检查），**不**当成相对根的路径，
          否则 ``/etc/passwd`` 会被静默改写成 ``<root>/etc/passwd``；
        * 相对路径 —— 相对 root_path 解析。
        """
        if fid is None or fid == "":
            raise ValueError("fid must not be empty")
        if self.root_path is None:
            return os.path.abspath(fid)

        if fid in ("/", ".", "root"):
            return self.root_path

        candidate = (
            os.path.abspath(fid)
            if os.path.isabs(fid)
            else os.path.abspath(os.path.join(self.root_path, fid))
        )
        if candidate != self.root_path and not candidate.startswith(
            self.root_path + os.sep
        ):
            raise ValueError(f"路径越出 root_path: {fid}")
        return candidate

    # ------------------------------------------------------------------ 核心
    def login(self, *args: Any, **kwargs: Any) -> bool:
        """本地文件系统无需认证，仅校验根目录可用。"""
        root = self.root_path or os.path.abspath(os.curdir)
        if self.root_path is not None:
            os.makedirs(root, exist_ok=True)
        if not os.path.isdir(root):
            logger.error(f"根目录不存在或不是目录: {root}")
            return False
        self._is_logged_in = True
        logger.info(f"本地文件系统就绪: {root}")
        return True

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        try:
            return os.path.exists(self._resolve(fid))
        except ValueError:
            return False

    def mkdir(
        self,
        fid: str,
        name: str,
        return_if_exist: bool = True,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """在 fid 下创建名为 name 的子目录，返回新目录的 fid（绝对路径）。"""
        parent = self._resolve(fid)
        target = os.path.join(parent, name)
        if os.path.isdir(target):
            if return_if_exist:
                return target
            logger.warning(f"目录已存在: {target}")
            return target
        os.makedirs(target, exist_ok=True)
        logger.info(f"创建目录: {target}")
        return target

    def delete(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        path = self._resolve(fid)
        if not os.path.exists(path):
            logger.warning(f"删除目标不存在: {path}")
            return False
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        logger.info(f"已删除: {path}")
        return True

    def get_file_list(self, fid: str, *args: Any, **kwargs: Any) -> list[DriveFile]:
        path = self._resolve(fid)
        if not os.path.isdir(path):
            return []
        return [
            _to_drive_file(os.path.join(path, entry))
            for entry in sorted(os.listdir(path))
            if os.path.isfile(os.path.join(path, entry))
        ]

    def get_dir_list(self, fid: str, *args: Any, **kwargs: Any) -> list[DriveFile]:
        path = self._resolve(fid)
        if not os.path.isdir(path):
            return []
        return [
            _to_drive_file(os.path.join(path, entry))
            for entry in sorted(os.listdir(path))
            if os.path.isdir(os.path.join(path, entry))
        ]

    def get_file_info(self, fid: str, *args: Any, **kwargs: Any) -> DriveFile | None:
        path = self._resolve(fid)
        if not os.path.isfile(path):
            return None
        return _to_drive_file(path)

    def get_dir_info(self, fid: str, *args: Any, **kwargs: Any) -> DriveFile | None:
        path = self._resolve(fid)
        if not os.path.isdir(path):
            return None
        return _to_drive_file(path)

    # ------------------------------------------------------------ 上传 / 下载
    def upload_file(
        self,
        filepath: str,
        fid: str,
        *args: Any,
        overwrite: bool = False,
        **kwargs: Any,
    ) -> bool:
        """把本地文件 filepath 复制进目录 fid。

        与 BaseDrive 契约一致：``fid`` 是**目标目录**，不是目标文件。

        Note:
            ``filepath`` 是"网盘之外"的本地路径，因此按进程 cwd 解析，
            **不**经过 ``root_path``；``fid`` 才是网盘内的 id，会经过
            ``root_path`` 解析与越界检查。下载方向同理（``fid`` 是网盘内的
            源，``save_dir``/``filepath`` 是网盘外的目标）。
        """
        if not os.path.isfile(filepath):
            logger.error(f"源文件不存在: {filepath}")
            return False

        target_dir = self._resolve(fid)
        os.makedirs(target_dir, exist_ok=True)
        target = os.path.join(
            target_dir, kwargs.get("filename") or os.path.basename(filepath)
        )

        if os.path.exists(target) and not overwrite:
            logger.warning(f"目标已存在且未开启 overwrite: {target}")
            return False
        if os.path.abspath(filepath) == os.path.abspath(target):
            logger.warning(f"源和目标是同一个文件，跳过: {target}")
            return True

        shutil.copy2(filepath, target)
        logger.info(f"上传完成: {filepath} -> {target}")
        return True

    def download_file(
        self,
        fid: str,
        save_dir: str | None = None,
        filename: str | None = None,
        filepath: str | None = None,
        overwrite: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        source = self._resolve(fid)
        if not os.path.isfile(source):
            logger.error(f"源文件不存在: {source}")
            return False

        if not filepath and not save_dir:
            # 未指定任何目标时落到当前目录，而不是像历史实现那样
            # 让 os.makedirs("") 抛 FileNotFoundError
            save_dir = os.path.abspath(os.curdir)
        local_path = get_filepath(
            filedir=save_dir,
            filename=filename or os.path.basename(source),
            filepath=filepath,
        )

        if os.path.exists(local_path) and not overwrite:
            logger.warning(f"目标已存在且未开启 overwrite: {local_path}")
            return False
        if source == local_path:
            logger.warning(f"源和目标是同一个文件，跳过: {local_path}")
            return True

        parent = os.path.dirname(local_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        shutil.copy2(source, local_path)
        logger.info(f"下载完成: {source} -> {local_path}")
        return True

    def download_dir(
        self,
        fid: str,
        save_dir: str,
        recursion: bool = True,
        overwrite: bool = False,
        ignore_filter: Callable[[str], bool] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """本地目录复制。直接用 shutil 递归，避免逐文件走网络语义的基类实现。"""
        source = self._resolve(fid)
        if not os.path.isdir(source):
            logger.error(f"源目录不存在: {source}")
            return False
        os.makedirs(save_dir, exist_ok=True)

        for entry in sorted(os.listdir(source)):
            src = os.path.join(source, entry)
            if ignore_filter and ignore_filter(entry):
                continue
            dst = os.path.join(save_dir, entry)
            if os.path.isfile(src):
                if os.path.exists(dst) and not overwrite:
                    continue
                shutil.copy2(src, dst)
            elif os.path.isdir(src) and recursion:
                self.download_dir(
                    fid=src,
                    save_dir=dst,
                    recursion=recursion,
                    overwrite=overwrite,
                    ignore_filter=ignore_filter,
                )
        return True

    # ------------------------------------------------------------------ 高级
    def move(self, source_fid: str, target_fid: str, *args: Any, **kwargs: Any) -> bool:
        source = self._resolve(source_fid)
        target_dir = self._resolve(target_fid)
        if not os.path.exists(source):
            logger.error(f"源不存在: {source}")
            return False
        os.makedirs(target_dir, exist_ok=True)
        shutil.move(source, os.path.join(target_dir, os.path.basename(source)))
        return True

    def copy(self, source_fid: str, target_fid: str, *args: Any, **kwargs: Any) -> bool:
        source = self._resolve(source_fid)
        target_dir = self._resolve(target_fid)
        if not os.path.exists(source):
            logger.error(f"源不存在: {source}")
            return False
        os.makedirs(target_dir, exist_ok=True)
        target = os.path.join(target_dir, os.path.basename(source))
        if os.path.isdir(source):
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            shutil.copy2(source, target)
        return True

    def rename(self, fid: str, new_name: str, *args: Any, **kwargs: Any) -> bool:
        source = self._resolve(fid)
        if not os.path.exists(source):
            logger.error(f"源不存在: {source}")
            return False
        target = os.path.join(os.path.dirname(source.rstrip(os.sep)), new_name)
        os.rename(source, target)
        logger.info(f"重命名: {source} -> {target}")
        return True

    def search(
        self,
        keyword: str,
        fid: str | None = None,
        file_type: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> list[DriveFile]:
        root = self._resolve(fid) if fid else self._root_fid
        matched: list[DriveFile] = []
        for dirpath, dirnames, filenames in os.walk(root):
            names = (
                filenames if file_type == "file" else list(dirnames) + list(filenames)
            )
            for name in names:
                if keyword.lower() in name.lower():
                    matched.append(_to_drive_file(os.path.join(dirpath, name)))
        return matched

    def get_quota(self, *args: Any, **kwargs: Any) -> dict:
        usage = shutil.disk_usage(self._root_fid)
        return {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "path": self._root_fid,
        }

    def get_download_url(self, fid: str, *args: Any, **kwargs: Any) -> str:
        """本地文件没有网络下载链接，返回 file:// URI。"""
        from pathlib import Path

        return Path(self._resolve(fid)).as_uri()


class LocalDrive(OSDrive):
    """:class:`OSDrive` 的别名，保留以兼容 ``get_drive("local")``。"""
