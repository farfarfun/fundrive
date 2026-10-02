"""
115网盘驱动，基于 p115client 实现。
"""

import os
import time
import traceback
from typing import Any

from funfile import file_size, file_sha1
from p115client import P115Client
from funget import simple_download
from farlog import getLogger
from pathlib import Path
from fundrive.core import BaseDrive, DriveFile
from fundrive.core.base import get_filepath
from fundrive.core.exceptions import AuthenticationError, FunDriveError

logger = getLogger("fundrive")


def _convert_info_to_file(
    it: dict, dirname: str | None = None, *args, **kwargs
) -> DriveFile:
    return DriveFile(
        fid=it["fid"],
        name=it["n"],
        size=it["s"],
        sha=it["sha"],
        time=it["t"],
        pc=it["pc"],
        isfile=True,
        isdir=False,
        dirname=dirname,
    )


def _convert_info_to_dir(
    it: dict, dirname: str | None = None, *args, **kwargs
) -> DriveFile:
    return DriveFile(
        fid=it["cid"],
        name=it["ns"],
        time=it["t"],
        pc=it["pc"],
        isfile=False,
        isdir=True,
        dirname=dirname,
    )


class Pan115Drive(BaseDrive):
    """115网盘驱动，基于 p115client 实现。"""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._client: P115Client | None = None

    def login(
        self,
        cookies: str | None = None,
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
                Path("~/115-cookies.txt").expanduser(),
                app="qandroid",
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

    def _require_client(self) -> P115Client:
        """返回已登录的客户端，未登录时抛出认证异常。"""
        if self._client is None:
            raise AuthenticationError("请先调用 Pan115Drive.login() 登录 115 网盘")
        return self._client

    def _query_entries(self, fid: str) -> list[dict]:
        """查询 fid 对应的原始条目列表。

        只有 115 明确回答"资源不存在"时才返回空列表；网络、认证、SDK 等其他
        错误会带着 fid 上下文抛出 :class:`FunDriveError`，不再被伪装成
        "文件不存在"（SPEC §8.2）。
        """
        client = self._require_client()
        time.sleep(1)
        try:
            response = client.fs_file(fid)
        except FileNotFoundError:
            # p115client 的 P115FileNotFoundError 继承内置 FileNotFoundError，
            # 这是 SDK 明确表示"资源不存在"的唯一信号。
            return []
        except Exception as e:
            raise FunDriveError(
                f"查询 115 条目失败 fid={fid}: {type(e).__name__}: {e}",
                error_code="PAN115_QUERY_FAILED",
                details={"fid": fid},
            ) from e
        return list(response.get("data") or [])

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        return bool(self._query_entries(fid))

    def delete(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        try:
            self._client.fs_delete(fid)
            return True
        except Exception as e:
            logger.error(f"删除文件失败 {fid}: {e}")
            return False

    def get_all_list(self, fid: str, *args: Any, **kwargs: Any) -> list[DriveFile]:
        time.sleep(1)
        result: list[DriveFile] = []
        response = self._client.fs_files(fid)
        dirname = "/".join([i["name"] for i in response["path"][1:]])
        for it in response["data"]:
            if it["fc"] == 0:
                result.append(_convert_info_to_dir(it, dirname=dirname))
            else:
                result.append(_convert_info_to_file(it, dirname=dirname))
        return result

    def get_file_list(self, fid: str, *args: Any, **kwargs: Any) -> list[DriveFile]:
        return [i for i in self.get_all_list(fid, *args, **kwargs) if i["isfile"]]

    def get_dir_list(self, fid: str, *args: Any, **kwargs: Any) -> list[DriveFile]:
        return [i for i in self.get_all_list(fid, *args, **kwargs) if not i["isfile"]]

    def get_file_info(self, fid: str, *args: Any, **kwargs: Any) -> DriveFile | None:
        for it in self._query_entries(fid):
            if it["fc"] == 1:
                return _convert_info_to_file(it)
        return None

    def get_dir_info(self, fid: str, *args: Any, **kwargs: Any) -> DriveFile | None:
        for it in self._query_entries(fid):
            if it["fc"] == 0:
                return _convert_info_to_dir(it)
        return None

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
        fid: str | None = None,
        file_type: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> list[DriveFile]:
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
