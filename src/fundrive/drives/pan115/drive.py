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
    """
    115网盘驱动，基于 p115client 实现

    ``fid`` 用 115 自己的 ID 体系：目录用 ``cid``，文件用 ``fid``，根目录是
    ``"0"``。几乎所有接口都要求先 :meth:`login`。
    """

    def __init__(self, *args: Any, **kwargs: Any):
        """
        初始化115网盘驱动

        这里只准备字段，真正建立会话在 :meth:`login` 中完成。

        Args:
            *args: 透传给 ``BaseDrive`` 的可变位置参数
            **kwargs: 透传给 ``BaseDrive`` 的可变关键字参数
        """
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

        不传 ``cookies`` 时读取 ``~/115-cookies.txt``，并以 ``qandroid`` 客户端
        走一次扫码/续期登录。

        Args:
            cookies (str, optional): 115 的 cookie 字符串
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            bool: 登录成功返回 ``True``
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
        """
        在指定目录下创建子目录

        Args:
            fid (str): 父目录的 cid
            name (str): 新目录名
            return_if_exist (bool): 保留参数；115 服务端对同名目录直接返回已有
                目录的 cid，本驱动不额外判重
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            str: 新目录的 cid；创建失败返回空字符串

        Note:
            按 ``BaseDrive`` 契约这里必须返回**目录ID**。历史实现 ``return True``，
            调用方（如 ``upload_dir`` / ``copy_data``）会把 ``True`` 当成 cid 继续
            往下传，导致后续上传全部落到错误位置。
        """
        client = self._require_client()
        response = client.fs_mkdir(name, fid) or {}
        cid = response.get("cid") or (response.get("data") or {}).get("cid")
        if not cid:
            logger.error(f"115创建目录失败 parent_fid={fid} name={name}: {response}")
            return ""
        return str(cid)

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
        """
        判断文件或目录是否存在

        Args:
            fid (str): 文件或目录ID
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            bool: 存在返回 ``True``

        Raises:
            AuthenticationError: 尚未登录
            FunDriveError: 查询过程中出现网络/SDK 等非"资源不存在"的错误
        """
        return bool(self._query_entries(fid))

    def delete(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        删除文件或目录

        Args:
            fid (str): 待删除的文件或目录ID
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            bool: 删除成功返回 ``True``，失败记录日志并返回 ``False``
        """
        try:
            self._require_client().fs_delete(fid)
            return True
        except Exception as e:
            logger.error(f"删除文件失败 {fid}: {e}")
            return False

    def get_all_list(self, fid: str, *args: Any, **kwargs: Any) -> list[DriveFile]:
        """
        获取目录下的全部条目（文件 + 子目录）

        为避免触发 115 的频率限制，每次调用前固定 sleep 1 秒。

        Args:
            fid (str): 目录的 cid
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            list[DriveFile]: 条目列表，用 ``isfile`` / ``isdir`` 区分类型
        """
        time.sleep(1)
        result: list[DriveFile] = []
        response = self._require_client().fs_files(fid)
        dirname = "/".join([i["name"] for i in response["path"][1:]])
        for it in response["data"]:
            if it["fc"] == 0:
                result.append(_convert_info_to_dir(it, dirname=dirname))
            else:
                result.append(_convert_info_to_file(it, dirname=dirname))
        return result

    def get_file_list(self, fid: str, *args: Any, **kwargs: Any) -> list[DriveFile]:
        """
        获取目录下的文件列表

        Args:
            fid (str): 目录的 cid
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            list[DriveFile]: 文件列表
        """
        return [i for i in self.get_all_list(fid, *args, **kwargs) if i["isfile"]]

    def get_dir_list(self, fid: str, *args: Any, **kwargs: Any) -> list[DriveFile]:
        """
        获取目录下的子目录列表

        Args:
            fid (str): 目录的 cid
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            list[DriveFile]: 子目录列表
        """
        return [i for i in self.get_all_list(fid, *args, **kwargs) if not i["isfile"]]

    def get_file_info(self, fid: str, *args: Any, **kwargs: Any) -> DriveFile | None:
        """
        获取文件详情

        Args:
            fid (str): 文件ID
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            DriveFile | None: 文件信息；不存在或该ID是目录时返回 ``None``
        """
        for it in self._query_entries(fid):
            if it["fc"] == 1:
                return _convert_info_to_file(it)
        return None

    def get_dir_info(self, fid: str, *args: Any, **kwargs: Any) -> DriveFile | None:
        """
        获取目录详情

        Args:
            fid (str): 目录的 cid
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            DriveFile | None: 目录信息；不存在或该ID是文件时返回 ``None``
        """
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
        """
        下载单个文件

        Args:
            fid (str): 文件ID
            save_dir (str, optional): 保存目录
            filename (str, optional): 保存文件名，默认用网盘上的文件名
            filepath (str, optional): 完整保存路径，给了就忽略 save_dir/filename
            overwrite (bool): 目标已存在时是否覆盖
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            bool: 下载成功返回 ``True``，失败记录日志并返回 ``False``
        """
        try:
            # 注意不能写成 get_file_info(fid=fid, *args)：*args 会去填第一个位置
            # 形参（也是 fid），直接 TypeError: got multiple values for 'fid'。
            file_info = self.get_file_info(fid, **kwargs)
            if not file_info:
                logger.error(f"文件不存在或不是文件 {fid}")
                return False
            downer = self._require_client().download_url_app(file_info["pc"])
            url = downer["data"][fid]["url"]["url"]
            if not filepath:
                save_filename = filename or file_info["name"]
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
        """
        上传单个文件

        Args:
            filepath (str): 本地文件路径
            fid (str): 目标目录的 cid
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            bool: 上传成功返回 ``True``，失败记录日志并返回 ``False``
        """
        try:
            self._require_client().upload_file(
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
        """
        按关键字搜索文件

        Args:
            keyword (str): 搜索关键字
            fid (str, optional): 保留参数，当前实现是全盘搜索，不限定目录
            file_type (str, optional): 保留参数，当前实现不按类型过滤
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            list[DriveFile]: 命中条目

        Note:
            这里返回的是 115 接口的原始条目字典，字段名与 ``DriveFile`` 并不一致，
            调用方暂时不能按 ``DriveFile`` 的字段去取值。
        """
        return [it for it in self._require_client().fs_search(keyword)["data"]]

    def move(
        self,
        source_fid: str,
        target_fid: str,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        移动文件或目录

        Args:
            source_fid (str): 源文件或目录ID
            target_fid (str): 目标目录的 cid
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            bool: 移动成功返回 ``True``，失败记录日志并返回 ``False``
        """
        try:
            self._require_client().fs_move(source_fid, target_fid)
            return True
        except Exception as e:
            logger.error(f"移动文件失败 {source_fid} -> {target_fid}: {e}")
            return False

    def rename(self, fid: str, new_name: str, *args: Any, **kwargs: Any) -> bool:
        """
        重命名文件或目录

        Args:
            fid (str): 文件或目录ID
            new_name (str): 新名称
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            bool: 重命名成功返回 ``True``，失败记录日志并返回 ``False``
        """
        try:
            self._require_client().fs_rename((fid, new_name))
            return True
        except Exception as e:
            logger.error(f"重命名失败 {fid} -> {new_name}: {e}")
            return False

    def get_quota(self, *args: Any, **kwargs: Any) -> dict:
        """
        获取网盘空间使用情况

        Args:
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            dict: 含 ``total`` / ``used`` / ``free`` 三个键，单位字节
        """
        data = self._require_client().user_space_info()["data"]
        total = int(data["all_total"]["size"])
        used = int(data["all_use"]["size"])
        return {"total": total, "used": used, "free": total - used}

    def get_download_url(self, fid: str, *args: Any, **kwargs: Any) -> str:
        """
        获取文件的下载直链

        Args:
            fid (str): 文件ID
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            str: 下载链接（有时效，且通常需要配合 115 的请求头使用）

        Raises:
            FunDriveError: 文件不存在
        """
        # 同 download_file：不能写成 get_file_info(fid=fid, *args)
        file_info = self.get_file_info(fid, **kwargs)
        if not file_info:
            raise FunDriveError(
                f"文件不存在 fid={fid}",
                error_code="PAN115_FILE_NOT_FOUND",
                details={"fid": fid},
            )
        downer = self._require_client().download_url_app(file_info["pc"])
        return downer["data"][fid]["url"]["url"]
