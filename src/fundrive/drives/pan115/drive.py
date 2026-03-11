"""
115网盘驱动，基于 p115client 实现。
"""
import os
from typing import Any, List, Optional

from p115client import P115Client, check_response
from p115client.tool.download import batch_get_url
from funget import download
from funsecret import read_secret
from nltlog import getLogger

from fundrive.core import BaseDrive, DriveFile
from fundrive.core.base import get_filepath

logger = getLogger("fundrive")


def _item_to_drive_file(item: dict) -> DriveFile:
    """将 115 API 返回的条目（dict）转为 DriveFile。"""
    fid = str(item.get("cid") or item.get("id") or item.get("fid", ""))
    name = str(item.get("n") or item.get("name") or "")
    size = item.get("s")
    if size is None:
        size = item.get("size")
    if size is not None:
        size = int(size)
    ico = item.get("ico") or item.get("t") or ""
    is_dir = ico == "folder" or ico == "folder.png" or item.get("is_dir", False)
    if isinstance(is_dir, str):
        is_dir = is_dir in ("1", "true", "True")
    return DriveFile(
        fid=fid,
        name=name,
        size=size,
        ext={
            "parent_id": str(item.get("pid") or item.get("parent_id") or ""),
            "modified_time": str(item.get("te") or item.get("modified_time") or ""),
            "sha1": item.get("sha1"),
            "pickcode": item.get("pc") or item.get("pickcode"),
            "is_dir": is_dir,
        },
    )


def _is_dir(item: dict) -> bool:
    ico = item.get("ico") or item.get("t") or ""
    is_dir = ico == "folder" or ico == "folder.png" or item.get("is_dir", False)
    if isinstance(is_dir, str):
        is_dir = is_dir in ("1", "true", "True")
    return bool(is_dir)


class Pan115Drive(BaseDrive):
    """115网盘驱动，基于 p115client 实现。"""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._client: Optional[P115Client] = None

    def login(
        self,
        uid: Optional[str] = None,
        cid: Optional[str] = None,
        seid: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        登录115网盘

        凭据来自浏览器Cookie中的 UID、CID、SEID 三个值。
        可通过参数传入，也可通过 funsecret 配置:
            funsecret set fundrive pan115 uid "your_uid"
            funsecret set fundrive pan115 cid "your_cid"
            funsecret set fundrive pan115 seid "your_seid"
        """
        uid = uid or read_secret("fundrive", "pan115", "uid")
        cid_val = cid or read_secret("fundrive", "pan115", "cid")
        seid_val = seid or read_secret("fundrive", "pan115", "seid")
        cookies_str = f"UID={uid}; CID={cid_val}; SEID={seid_val}"
        self._client = P115Client(cookies_str)
        self._is_logged_in = True
        self._root_fid = "0"
        return True

    def _list_raw(self, fid: str) -> List[dict]:
        resp = check_response(
            self._client.request(
                "https://webapi.115.com/files",
                method="GET",
                payload={"cid": fid, "show_dir": 1},
            )
        )
        data = resp.get("data") or resp.get("list") or []
        return data if isinstance(data, list) else []

    def mkdir(
        self,
        fid: str,
        name: str,
        return_if_exist: bool = True,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        if return_if_exist:
            dir_map = {f.name: f.fid for f in self.get_dir_list(fid=fid)}
            if name in dir_map:
                logger.info(f"目录 {name} 已存在, fid={dir_map[name]}")
                return dir_map[name]
        resp = check_response(
            self._client.request(
                "https://webapi.115.com/files/add",
                method="POST",
                payload={"pid": fid, "cname": name},
            )
        )
        return str(resp.get("cid") or resp.get("id") or (resp.get("data") or {}).get("cid") or "")

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        try:
            self._list_raw(fid)
            return True
        except Exception:
            return False

    def delete(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        try:
            check_response(
                self._client.request(
                    "https://webapi.115.com/files/delete",
                    method="POST",
                    payload={"fid": fid},
                )
            )
            return True
        except Exception as e:
            logger.error(f"删除文件失败 {fid}: {e}")
            return False

    def get_file_list(self, fid: str, *args: Any, **kwargs: Any) -> List[DriveFile]:
        return [_item_to_drive_file(it) for it in self._list_raw(fid) if not _is_dir(it)]

    def get_dir_list(self, fid: str, *args: Any, **kwargs: Any) -> List[DriveFile]:
        return [_item_to_drive_file(it) for it in self._list_raw(fid) if _is_dir(it)]

    def get_file_info(self, fid: str, *args: Any, **kwargs: Any) -> Optional[DriveFile]:
        try:
            for it in self._list_raw(fid):
                _fid = str(it.get("cid") or it.get("id", ""))
                if _fid == fid and not _is_dir(it):
                    return _item_to_drive_file(it)
        except Exception:
            pass
        return None

    def get_dir_info(self, fid: str, *args: Any, **kwargs: Any) -> Optional[DriveFile]:
        try:
            for it in self._list_raw(fid):
                _fid = str(it.get("cid") or it.get("id", ""))
                if _fid == fid and _is_dir(it):
                    return _item_to_drive_file(it)
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
        """
        下载文件
        需要文件的 pickcode 来获取下载链接。
        如果 fid 本身就是 pickcode 则直接使用，否则尝试从文件列表中查找。
        """
        try:
            pickcode = kwargs.get("pickcode", fid)
            url_map = batch_get_url(self._client, pickcode)
            urls = list(url_map.values()) if isinstance(url_map, dict) else []
            if not urls:
                logger.error(f"未获取到下载链接: {pickcode}")
                return False
            url_obj = urls[0]
            url = url_obj.url if hasattr(url_obj, "url") else str(url_obj)
            headers = getattr(url_obj, "headers", None) or {}
            if not filepath:
                save_filename = filename or os.path.basename(url.split("?")[0]) or "download"
                filepath = get_filepath(save_dir, save_filename)
            download(url, filepath=filepath, headers=headers, overwrite=overwrite)
            return True
        except Exception as e:
            logger.error(f"下载文件失败 {fid}: {e}")
            return False

    def upload_file(
        self,
        filepath: str,
        fid: str,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        上传文件到115网盘
        115网盘上传流程:
        1. 调用上传初始化获取凭证
        2. 若已秒传则直接成功
        3. 否则通过阿里云 OSS 上传（需安装 oss2）
        """
        try:
            try:
                init_resp = check_response(
                    self._client.request(
                        "https://proapi.115.com/app/uploadinfo",
                        method="GET",
                        payload={"cid": fid},
                    )
                )
            except Exception:
                init_resp = check_response(
                    self._client.request(
                        "https://webapi.115.com/files/upload_init",
                        method="POST",
                        payload={"cid": fid},
                        ecdh_encrypt=True,
                    )
                )
            if init_resp.get("status") == 2 or init_resp.get("quick") or init_resp.get("is_done"):
                logger.info(f"文件秒传成功: {filepath}")
                return True
            try:
                import oss2
            except ImportError:
                raise ImportError("上传大文件需要安装 oss2: pip install oss2")
            info = init_resp.get("data") or init_resp
            auth = oss2.StsAuth(
                access_key_id=info.get("access_key_id") or info.get("AccessKeyId"),
                access_key_secret=info.get("access_key_secret") or info.get("AccessKeySecret"),
                security_token=info.get("security_token") or info.get("SecurityToken", ""),
            )
            bucket = oss2.Bucket(
                auth=auth,
                endpoint=info.get("endpoint") or info.get("oss_endpoint", "oss-cn-hangzhou.aliyuncs.com"),
                bucket_name=info.get("bucket") or info.get("bucket_name"),
            )
            bucket.put_object_from_file(
                key=info.get("object_key") or info.get("key"),
                filename=filepath,
                headers=info.get("headers"),
            )
            return True
        except Exception as e:
            logger.error(f"上传文件失败 {filepath}: {e}")
            return False

    def search(
        self,
        keyword: str,
        fid: Optional[str] = None,
        file_type: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> List[DriveFile]:
        dir_id = fid or "0"
        resp = check_response(
            self._client.request(
                "https://webapi.115.com/files/search",
                method="GET",
                payload={"cid": dir_id, "keyword": keyword},
            )
        )
        data = resp.get("data") or resp.get("list") or []
        return [_item_to_drive_file(it) for it in (data if isinstance(data, list) else [])]

    def move(
        self,
        source_fid: str,
        target_fid: str,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        try:
            check_response(
                self._client.request(
                    "https://webapi.115.com/files/move",
                    method="POST",
                    payload={"fid": source_fid, "cid": target_fid},
                )
            )
            return True
        except Exception as e:
            logger.error(f"移动文件失败 {source_fid} -> {target_fid}: {e}")
            return False

    def rename(self, fid: str, new_name: str, *args: Any, **kwargs: Any) -> bool:
        try:
            check_response(
                self._client.request(
                    "https://webapi.115.com/files/rename",
                    method="POST",
                    payload={"fid": fid, "name": new_name},
                )
            )
            return True
        except Exception as e:
            logger.error(f"重命名失败 {fid} -> {new_name}: {e}")
            return False

    def get_quota(self, *args: Any, **kwargs: Any) -> dict:
        resp = check_response(
            self._client.request(
                "https://webapi.115.com/quota",
                method="GET",
            )
        )
        data = resp.get("data") or resp
        total = int(data.get("total") or data.get("total_size") or 0)
        used = int(data.get("used") or data.get("size") or 0)
        return {"total": total, "used": used, "free": total - used}

    def get_download_url(self, fid: str, *args: Any, **kwargs: Any) -> str:
        """
        获取下载链接
        参数 fid 应传入文件的 pickcode。
        """
        pickcode = kwargs.get("pickcode", fid)
        url_map = batch_get_url(self._client, pickcode)
        urls = list(url_map.values()) if isinstance(url_map, dict) else []
        if not urls:
            return ""
        url_obj = urls[0]
        return url_obj.url if hasattr(url_obj, "url") else str(url_obj)
