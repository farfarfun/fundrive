import os
import posixpath
from typing import Any, List, Optional
from urllib.parse import quote, unquote, urlparse

from nltlog import getLogger
from nltsecret import read_secret
import requests
from xml.etree import ElementTree as ET
from funget import simple_download, single_upload
from fundrive.core import BaseDrive, DriveFile

logger = getLogger("fundrive")


class WebDavDrive(BaseDrive):
    def __init__(self, *args, **kwargs):
        super(WebDavDrive, self).__init__(*args, **kwargs)
        self.server_url: Optional[str] = None
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self._session: Optional[requests.Session] = None
        self._timeout: int = 30

    def login(
        self, server_url=None, username=None, password=None, *args, **kwargs
    ) -> bool:
        server_url = server_url or read_secret("fundrive", "webdav", "server_url")
        username = username or read_secret("fundrive", "webdav", "username")
        password = password or read_secret("fundrive", "webdav", "password")

        if not server_url or not username or not password:
            raise Exception("server_url, username, password is None")

        self.server_url = server_url.rstrip("/")
        self.username = username
        self.password = password
        self._timeout = int(kwargs.get("timeout", self._timeout))
        self._session = requests.Session()
        self._session.auth = (username, password)

        # 通过根路径 PROPFIND 做一次连通性和认证探测
        self._request("PROPFIND", "/", headers={"Depth": "0"})
        return True

    def mkdir(self, fid, name, return_if_exist=True, *args, **kwargs) -> str:
        parent = self._normalize_fid(fid)
        target = self._normalize_fid(posixpath.join(parent, name))
        if self.exist(target):
            if return_if_exist:
                return target
            raise FileExistsError(target)
        self._request("MKCOL", target)
        return target

    def delete(self, fid, *args, **kwargs) -> bool:
        target = self._normalize_fid(fid)
        if not self.exist(target):
            return False
        self._request("DELETE", target)
        return True

    def exist(self, fid: str, *args, **kwargs) -> bool:
        if args:
            # 兼容旧调用：exist(parent_fid, name)
            fid = posixpath.join(fid, str(args[0]))
        if not fid:
            return False
        try:
            self._request("HEAD", fid)
            return True
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status in (404,):
                return False
            # 某些 WebDAV 服务端不支持 HEAD，回退到 PROPFIND depth=0
            if status in (405, 501):
                try:
                    self._request("PROPFIND", fid, headers={"Depth": "0"})
                    return True
                except requests.HTTPError as e2:
                    return (
                        False
                        if e2.response is not None and e2.response.status_code == 404
                        else False
                    )
            raise

    def get_file_list(self, fid, *args, **kwargs) -> List[DriveFile]:
        children = self._list_children(fid)
        return [item for item in children if item.get("type") == "file"]

    def get_dir_list(self, fid, *args, **kwargs) -> List[DriveFile]:
        children = self._list_children(fid)
        return [item for item in children if item.get("type") == "directory"]

    def get_file_info(self, fid, *args, **kwargs) -> DriveFile:
        info = self._get_path_info(fid)
        if info.get("type") != "file":
            raise ValueError(f"{fid} is not a file")
        return info

    def get_dir_info(self, fid, *args, **kwargs) -> DriveFile:
        info = self._get_path_info(fid)
        if info.get("type") != "directory":
            raise ValueError(f"{fid} is not a directory")
        return info

    def download_file(
        self,
        fid: str,
        save_dir: Optional[str] = None,
        filename: Optional[str] = None,
        filepath: Optional[str] = None,
        overwrite: bool = False,
        *args,
        **kwargs,
    ) -> bool:
        """
        下载单个文件

        Args:
            fid: 文件ID（远程路径）
            save_dir: 文件保存目录
            filename: 文件名
            filepath: 完整的文件保存路径
            overwrite: 是否覆盖已存在的文件

        Returns:
            bool: 下载是否成功
        """
        if filepath:
            local_path = filepath
        elif save_dir and filename:
            local_path = os.path.join(save_dir, filename)
        elif save_dir:
            local_path = os.path.join(save_dir, os.path.basename(fid.rstrip("/")))
        else:
            local_path = os.path.basename(fid.rstrip("/"))

        if not local_path:
            raise ValueError("invalid local download path")

        parent_dir = os.path.dirname(local_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        if os.path.exists(local_path) and not overwrite:
            return False

        simple_download(
            f"{self.server_url}/{fid}", local_path, auth=(self.username, self.password)
        )
        return True

    def upload_file(
        self, filepath: str, fid: str, recursion=True, overwrite=False, *args, **kwargs
    ) -> bool:
        """
        上传单个文件。

        兼容调用：
        - upload_file(filepath, fid)
        - upload_file(filepath, fid, "name.txt")
        - upload_file(filepath, fid, filename="name.txt", overwrite=True)
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(filepath)

        filename = kwargs.get("filename") or (
            args[0] if args else os.path.basename(filepath)
        )
        overwrite = bool(
            kwargs.get("overwrite", kwargs.get("overwrite_if_exists", overwrite))
        )
        target_dir = self._normalize_fid(fid)
        target = self._normalize_fid(posixpath.join(target_dir, filename))

        single_upload(
            f"{self.server_url}/{target_dir.strip('/')}/{filename}",
            filepath,
            overwrite=overwrite,
            auth=(self.username, self.password),
        )
        return True

    def move(self, source_fid: str, target_fid: str, *args: Any, **kwargs: Any) -> bool:
        source = self._normalize_fid(source_fid)
        target = self._normalize_fid(target_fid)
        if not self.exist(source):
            return False
        overwrite = bool(
            kwargs.get("overwrite", kwargs.get("overwrite_if_exists", False))
        )
        if self.exist(target) and not overwrite:
            return False

        self._request(
            "MOVE",
            source,
            headers={
                "Destination": self._build_destination_url(target),
                "Overwrite": "T" if overwrite else "F",
            },
        )
        return True

    def copy(self, source_fid: str, target_fid: str, *args: Any, **kwargs: Any) -> bool:
        source = self._normalize_fid(source_fid)
        target = self._normalize_fid(target_fid)
        if not self.exist(source):
            return False
        overwrite = bool(
            kwargs.get("overwrite", kwargs.get("overwrite_if_exists", False))
        )
        depth = str(kwargs.get("depth", "infinity"))
        if self.exist(target) and not overwrite:
            return False

        self._request(
            "COPY",
            source,
            headers={
                "Destination": self._build_destination_url(target),
                "Overwrite": "T" if overwrite else "F",
                "Depth": depth,
            },
        )
        return True

    def rename(self, fid: str, new_name: str, *args: Any, **kwargs: Any) -> bool:
        source = self._normalize_fid(fid)
        if not self.exist(source):
            return False
        parent = posixpath.dirname(source.rstrip("/")) or "/"
        target = self._normalize_fid(posixpath.join(parent, new_name))
        return self.move(source, target, *args, **kwargs)

    def get_download_url(
        self,
        fid: str,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        path = self._normalize_fid(fid)
        if not self.server_url:
            raise RuntimeError("please login first")
        return f"{self.server_url}/{path.lstrip('/')}"

    def _request(self, method: str, fid: str, **kwargs: Any) -> requests.Response:
        if not self._session or not self.server_url:
            raise RuntimeError("please login first")
        url = self._build_destination_url(fid)
        response = self._session.request(
            method=method, url=url, timeout=self._timeout, **kwargs
        )
        if response.status_code >= 400:
            try:
                response.raise_for_status()
            except requests.HTTPError:
                logger.warning(
                    f"webdav request failed method={method} fid={fid} status={response.status_code}"
                )
                raise
        return response

    def _build_destination_url(self, fid: str) -> str:
        if not self.server_url:
            raise RuntimeError("please login first")
        path = self._normalize_fid(fid)
        encoded_path = "/".join(
            quote(part, safe="") for part in path.lstrip("/").split("/")
        )
        return f"{self.server_url}/{encoded_path}"

    @staticmethod
    def _normalize_fid(fid: str) -> str:
        fid = fid or "/"
        if not fid.startswith("/"):
            fid = "/" + fid
        norm = posixpath.normpath(fid)
        return "/" if norm == "." else norm

    def _list_children(self, fid: str) -> List[DriveFile]:
        target = self._normalize_fid(fid)
        response = self._request("PROPFIND", target, headers={"Depth": "1"})
        entries = self._parse_propfind(response.text)
        # Depth=1 返回结果包含目标目录自身，需要过滤掉
        return [item for item in entries if self._normalize_fid(item.fid) != target]

    def _get_path_info(self, fid: str) -> DriveFile:
        target = self._normalize_fid(fid)
        response = self._request("PROPFIND", target, headers={"Depth": "0"})
        entries = self._parse_propfind(response.text)
        if not entries:
            raise FileNotFoundError(fid)
        return entries[0]

    def _parse_propfind(self, xml_text: str) -> List[DriveFile]:
        # 解析 WebDAV 207 Multi-Status 响应，提取路径、类型、大小等基础信息
        root = ET.fromstring(xml_text)
        results: List[DriveFile] = []
        server_path_prefix = (urlparse(self.server_url or "").path or "").rstrip("/")

        for response in root.findall(".//{*}response"):
            href = response.findtext("{*}href")
            if not href:
                continue
            raw_path = unquote(urlparse(href).path or "/")
            fid = raw_path
            if server_path_prefix and fid.startswith(server_path_prefix):
                # 将服务端 URL 前缀映射回驱动内部的相对 fid（如 /webdav 前缀）
                fid = fid[len(server_path_prefix) :]
            fid = self._normalize_fid(fid)

            prop = response.find(".//{*}prop")
            if prop is None:
                continue
            name = (
                prop.findtext("{*}displayname")
                or os.path.basename(fid.rstrip("/"))
                or "/"
            )
            size_text = prop.findtext("{*}getcontentlength")
            res_type = prop.find("{*}resourcetype")
            is_dir = res_type is not None and res_type.find("{*}collection") is not None
            item_type = "directory" if is_dir else "file"
            size = int(size_text) if size_text and size_text.isdigit() else 0

            results.append(
                DriveFile(
                    fid=fid,
                    name=name,
                    size=size,
                    ext={"type": item_type, "href": href},
                )
            )
        return results
