"""
115网盘驱动，基于 p115client 实现。
"""

import os
import traceback
from typing import Any, List, Optional

from funfile import file_size, file_sha1
from p115client import P115Client
from funget import simple_download
from nltlog import getLogger
from pathlib import Path
from fundrive.core import BaseDrive, DriveFile
from fundrive.core.base import get_filepath

logger = getLogger("fundrive")


def _convert_info_to_file(it: dict) -> DriveFile:
    return DriveFile(
        fid=it["fid"],
        name=it["n"],
        size=it["s"],
        sha=it["sha"],
        time=it["t"],
        pc=it["pc"],
    )


def _convert_info_to_dir(it: dict) -> DriveFile:
    return DriveFile(
        fid=it["cid"],
        name=it["ns"],
        time=it["t"],
        pc=it["pc"],
    )


class Pan115Drive(BaseDrive):
    """115网盘驱动，基于 p115client 实现。"""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._client: Optional[P115Client] = None

    def login(
        self,
        cookies: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        登录115网盘
        """
        if cookies is not None:
            self._client = P115Client(cookies=cookies)
        else:
            self._client = P115Client(
                Path("~/115-cookies.txt").expanduser(), check_for_relogin=True
            )
            self._client.login()
        return True

    def mkdir(
        self,
        fid: str,
        name: str,
        return_if_exist: bool = True,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        self._client.fs_mkdir(name, fid)
        return True

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        try:
            if self.get_file_info(fid):
                return True
            elif self.get_dir_info(fid):
                return True
            else:
                return False
        except Exception:
            return False

    def delete(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        try:
            self._client.fs_delete(fid)
            return True
        except Exception as e:
            logger.error(f"删除文件失败 {fid}: {e}")
            return False

    def get_file_list(self, fid: str, *args: Any, **kwargs: Any) -> List[DriveFile]:
        result: List[DriveFile] = []
        for it in self._client.fs_files(fid)["data"]:
            if it["fc"] == 1:
                result.append(_convert_info_to_file(it))
        return result

    def get_dir_list(self, fid: str, *args: Any, **kwargs: Any) -> List[DriveFile]:
        result: List[DriveFile] = []
        for it in self._client.fs_files(fid)["data"]:
            if it["fc"] == 0:
                result.append(_convert_info_to_dir(it))
        return result

    def get_file_info(self, fid: str, *args: Any, **kwargs: Any) -> Optional[DriveFile]:
        try:
            for it in self._client.fs_file(fid)["data"]:
                if it["fc"] == 1:
                    return _convert_info_to_file(it)
        except Exception:
            pass
        return None

    def get_dir_info(self, fid: str, *args: Any, **kwargs: Any) -> Optional[DriveFile]:
        try:
            for it in self._client.fs_file(fid)["data"]:
                if it["fc"] == 0:
                    return _convert_info_to_dir(it)
        except Exception:
            pass
        return None

    def download_file(
        self,
        fid: str,
        save_dir: Optional[str] = None,
        filename: Optional[str] = None,
        filepath: Optional[str] = None,
        overwrite: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        try:
            file_info = self.get_file_info(fid=fid, *args, **kwargs)
            downer = self._client.download_url_app(file_info["pc"])
            url = downer["data"][fid]["url"]["url"]
            if not filepath:
                save_filename = file_info["name"]
                filepath = get_filepath(save_dir, save_filename)
            simple_download(
                url, filepath=filepath, headers=downer["headers"], overwrite=overwrite
            )
            return True
        except Exception as e:
            logger.error(f"下载文件失败 {fid}: {e}:{traceback.format_exc()}")
            return False

    def upload_file(
        self,
        filepath: str,
        fid: str,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        try:
            self._client.upload_file(
                file=Path(filepath),
                pid=fid,
                partsize=1024,
                filename=os.path.basename(filepath),
                filesize=file_size(filepath),
                filesha1=file_sha1(filepath),
            )
            return True
        except Exception as e:
            logger.error(f"上传文件失败 {filepath}: {e}:{traceback.format_exc()}")
            return False

    def search(
        self,
        keyword: str,
        fid: Optional[str] = None,
        file_type: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> List[DriveFile]:
        return [it for it in self._client.fs_search(keyword)["data"]]

    def move(
        self,
        source_fid: str,
        target_fid: str,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        try:
            self._client.fs_move(source_fid, target_fid)
            return True
        except Exception as e:
            logger.error(f"移动文件失败 {source_fid} -> {target_fid}: {e}")
            return False

    def rename(self, fid: str, new_name: str, *args: Any, **kwargs: Any) -> bool:
        try:
            self._client.fs_rename((fid, new_name))
            return True
        except Exception as e:
            logger.error(f"重命名失败 {fid} -> {new_name}: {e}")
            return False

    def get_quota(self, *args: Any, **kwargs: Any) -> dict:
        data = self._client.user_space_info()["data"]
        total = int(data["all_total"]["size"])
        used = int(data["all_use"]["size"])
        return {"total": total, "used": used, "free": total - used}

    def get_download_url(self, fid: str, *args: Any, **kwargs: Any) -> str:
        """
        获取下载链接
        """
        file_info = self.get_file_info(fid=fid, *args, **kwargs)
        downer = self._client.download_url_app(file_info["pc"])
        return downer["data"][fid]["url"]["url"]
