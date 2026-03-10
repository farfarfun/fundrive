import os
from typing import Any, List, Optional

import py115
import py115.types
from funget import download
from funsecret import read_secret
from nltlog import getLogger

from fundrive.core import BaseDrive, DriveFile
from fundrive.core.base import get_filepath

logger = getLogger("fundrive")


def convert(file: py115.types.File) -> DriveFile:
    """转换115网盘文件对象为通用文件对象"""
    return DriveFile(
        fid=file.file_id,
        name=file.name,
        size=file.size,
        ext={
            "parent_id": file.parent_id,
            "modified_time": str(file.modified_time) if file.modified_time else None,
            "sha1": file.sha1,
            "pickcode": file.pickcode,
            "is_dir": file.is_dir,
        },
    )


class Pan115Drive(BaseDrive):
    """115网盘驱动，基于py115库实现"""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.cloud: py115.cloud.Cloud = None
        self.storage: py115.services.StorageService = None

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
        cid = cid or read_secret("fundrive", "pan115", "cid")
        seid = seid or read_secret("fundrive", "pan115", "seid")

        credential = py115.types.Credential(uid=uid, cid=cid, seid=seid)
        self.cloud = py115.connect(credential=credential)
        self.storage = self.cloud.storage()
        self._is_logged_in = True
        self._root_fid = "0"
        return True

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

        result = self.storage.make_dir(parent_id=fid, name=name)
        return result.file_id

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        try:
            for _ in self.storage.list(dir_id=fid):
                return True
            return True
        except Exception:
            return False

    def delete(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        try:
            self.storage.delete(fid)
            return True
        except Exception as e:
            logger.error(f"删除文件失败 {fid}: {e}")
            return False

    def get_file_list(self, fid: str, *args: Any, **kwargs: Any) -> List[DriveFile]:
        return [
            convert(f) for f in self.storage.list(dir_id=fid) if not f.is_dir
        ]

    def get_dir_list(self, fid: str, *args: Any, **kwargs: Any) -> List[DriveFile]:
        return [
            convert(f) for f in self.storage.list(dir_id=fid) if f.is_dir
        ]

    def get_file_info(self, fid: str, *args: Any, **kwargs: Any) -> Optional[DriveFile]:
        try:
            for f in self.storage.list(dir_id=fid):
                if f.file_id == fid and not f.is_dir:
                    return convert(f)
        except Exception:
            pass
        return None

    def get_dir_info(self, fid: str, *args: Any, **kwargs: Any) -> Optional[DriveFile]:
        try:
            for f in self.storage.list(dir_id=fid):
                if f.file_id == fid and f.is_dir:
                    return convert(f)
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
            ticket = self.storage.request_download(pickcode=pickcode)

            if not filepath:
                save_filename = filename or ticket.file_name
                filepath = get_filepath(save_dir, save_filename)

            download(
                ticket.url,
                filepath=filepath,
                headers=ticket.headers,
                overwrite=overwrite,
            )
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
        1. 调用 request_upload 获取上传凭证
        2. 如果文件已秒传(is_done=True)则直接返回成功
        3. 否则需要通过阿里云OSS SDK上传(需要安装oss2)
        """
        try:
            ticket = self.storage.request_upload(dir_id=fid, file_path=filepath)
            if ticket is None:
                logger.error(f"请求上传凭证失败: {filepath}")
                return False

            if ticket.is_done:
                logger.info(f"文件秒传成功: {filepath}")
                return True

            try:
                import oss2
            except ImportError:
                raise ImportError(
                    "上传大文件需要安装 oss2: pip install oss2"
                )

            auth = oss2.StsAuth(**ticket.oss_token)
            bucket = oss2.Bucket(
                auth=auth,
                endpoint=ticket.oss_endpoint,
                bucket_name=ticket.bucket_name,
            )
            bucket.put_object_from_file(
                key=ticket.object_key,
                filename=filepath,
                headers=ticket.headers,
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
        return [convert(f) for f in self.storage.search(keyword=keyword, dir_id=dir_id)]

    def move(
        self,
        source_fid: str,
        target_fid: str,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        try:
            self.storage.move(target_fid, source_fid)
            return True
        except Exception as e:
            logger.error(f"移动文件失败 {source_fid} -> {target_fid}: {e}")
            return False

    def rename(self, fid: str, new_name: str, *args: Any, **kwargs: Any) -> bool:
        try:
            self.storage.rename(file_id=fid, new_name=new_name)
            return True
        except Exception as e:
            logger.error(f"重命名失败 {fid} -> {new_name}: {e}")
            return False

    def get_quota(self, *args: Any, **kwargs: Any) -> dict:
        total, used = self.storage.space()
        return {
            "total": total,
            "used": used,
            "free": total - used,
        }

    def get_download_url(self, fid: str, *args: Any, **kwargs: Any) -> str:
        """
        获取下载链接

        参数 fid 应传入文件的 pickcode。
        """
        pickcode = kwargs.get("pickcode", fid)
        ticket = self.storage.request_download(pickcode=pickcode)
        return ticket.url
