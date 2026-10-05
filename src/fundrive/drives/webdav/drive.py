import os
import posixpath
import re
from typing import Any
from urllib.parse import quote, unquote, urlparse

from farlog import getLogger
from funsecret import read_secret
import requests
from xml.etree import ElementTree as ET
from funget import simple_download, single_upload
from fundrive.core import BaseDrive, DriveFile
from fundrive.core.exceptions import InvalidParameterError

logger = getLogger("fundrive")


class WebDavDrive(BaseDrive):
    """
    WebDAV 网盘驱动

    直接用 ``requests`` 发 WebDAV 方法（PROPFIND/MKCOL/MOVE/COPY/DELETE），
    不依赖第三方 WebDAV 客户端库。驱动内部的 ``fid`` 就是服务器上的绝对路径
    （以 ``/`` 开头），所有入参都会先经 ``_normalize_fid`` 归一化。

    个别服务端不支持 ``HEAD``，:meth:`exist` 会自动回退到 ``PROPFIND``。
    """

    def __init__(self, *args, **kwargs):
        """
        初始化 WebDAV 驱动

        这里只准备字段，真正的连接与认证在 :meth:`login` 中完成。

        Args:
            *args: 透传给 ``BaseDrive`` 的可变位置参数
            **kwargs: 透传给 ``BaseDrive`` 的可变关键字参数
        """
        super().__init__(*args, **kwargs)
        self.server_url: str | None = None
        self.username: str | None = None
        self.password: str | None = None
        self._session: requests.Session | None = None
        self._timeout: int = 30

    def login(
        self, server_url=None, username=None, password=None, *args, **kwargs
    ) -> bool:
        """
        登录 WebDAV 服务器

        三个参数任意一个为空时，会从 funsecret 的 ``fundrive/webdav/*`` 读取。
        登录时会对根路径做一次 ``PROPFIND``，用来同时验证连通性和账号密码。

        Args:
            server_url (str, optional): WebDAV 服务地址，如 ``https://dav.example.com/dav``
            username (str, optional): 用户名
            password (str, optional): 密码或应用专用密码
            *args: 可变位置参数
            **kwargs: 可变关键字参数，支持 ``timeout``（秒，默认 30）

        Returns:
            bool: 登录成功返回 ``True``

        Raises:
            InvalidParameterError: 地址、用户名或密码为空
            requests.HTTPError: 服务端返回 4xx/5xx（如 401 认证失败）
        """
        server_url = server_url or read_secret("fundrive", "webdav", "server_url")
        username = username or read_secret("fundrive", "webdav", "username")
        password = password or read_secret("fundrive", "webdav", "password")

        if not server_url or not username or not password:
            raise InvalidParameterError(
                "server_url、username、password 均不能为空",
                parameter="server_url/username/password",
            )

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
        """
        在指定目录下创建子目录

        Args:
            fid (str): 父目录路径
            name (str): 新目录名
            return_if_exist (bool): 目录已存在时直接返回其路径，``False`` 则抛异常
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            str: 新目录的路径（本驱动的 fid 即路径）

        Raises:
            FileExistsError: 目录已存在且 ``return_if_exist=False``
        """
        parent = self._normalize_fid(fid)
        target = self._normalize_fid(posixpath.join(parent, name))
        if self.exist(target):
            if return_if_exist:
                return target
            raise FileExistsError(target)
        self._request("MKCOL", target)
        return target

    def delete(self, fid, *args, **kwargs) -> bool:
        """
        删除文件或目录（目录为递归删除）

        Args:
            fid (str): 待删除的路径
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            bool: 删除成功返回 ``True``；目标本就不存在返回 ``False``
        """
        target = self._normalize_fid(fid)
        if not self.exist(target):
            return False
        self._request("DELETE", target)
        return True

    def exist(self, fid: str, *args, **kwargs) -> bool:
        """
        判断路径是否存在

        先用 ``HEAD`` 探测；服务端不支持（405/501）时回退到 ``PROPFIND``。
        只有 404 才算"不存在"，401/403/5xx 一律抛出，避免把"没权限"和
        "服务端故障"误报成"文件不存在"。

        Args:
            fid (str): 待检查的路径
            *args: 兼容旧调用 ``exist(parent_fid, name)``，第一个位置参数会被拼到 fid 后
            **kwargs: 可变关键字参数

        Returns:
            bool: 存在返回 ``True``

        Raises:
            requests.HTTPError: 非 404 的 HTTP 错误
        """
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
                    # 只有 404 才算"不存在"。其它状态（401/403/5xx）必须抛出，
                    # 否则权限不足和服务端故障都会被报成"文件不存在"，调用方
                    # 无从区分。原实现两个分支都返回 False，等于吞掉了一切。
                    if e2.response is not None and e2.response.status_code == 404:
                        return False
                    raise
            raise

    def get_file_list(self, fid, *args, **kwargs) -> list[DriveFile]:
        """
        获取指定目录下的文件列表（不含子目录、不递归）

        Args:
            fid (str): 目录路径
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            list[DriveFile]: 文件列表
        """
        children = self._list_children(fid)
        return [item for item in children if item.get("type") == "file"]

    def get_dir_list(self, fid, *args, **kwargs) -> list[DriveFile]:
        """
        获取指定目录下的子目录列表（不递归）

        Args:
            fid (str): 目录路径
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            list[DriveFile]: 子目录列表
        """
        children = self._list_children(fid)
        return [item for item in children if item.get("type") == "directory"]

    def get_file_info(self, fid, *args, **kwargs) -> DriveFile:
        """
        获取文件详情

        Args:
            fid (str): 文件路径
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            DriveFile: 文件信息

        Raises:
            FileNotFoundError: 路径不存在
            ValueError: 路径指向的是目录而非文件
        """
        info = self._get_path_info(fid)
        if info.get("type") != "file":
            raise ValueError(f"{fid} is not a file")
        return info

    def get_dir_info(self, fid, *args, **kwargs) -> DriveFile:
        """
        获取目录详情

        Args:
            fid (str): 目录路径
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            DriveFile: 目录信息

        Raises:
            FileNotFoundError: 路径不存在
            ValueError: 路径指向的是文件而非目录
        """
        info = self._get_path_info(fid)
        if info.get("type") != "directory":
            raise ValueError(f"{fid} is not a directory")
        return info

    def download_file(
        self,
        fid: str,
        save_dir: str | None = None,
        filename: str | None = None,
        filepath: str | None = None,
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

        # 必须用 _build_destination_url 做百分号编码：手拼 f"{server_url}/{fid}"
        # 会在文件名含空格/中文/# 时产生非法 URL，且 fid 以 "/" 开头时出现 "//"。
        simple_download(
            self._build_destination_url(fid),
            local_path,
            auth=(self.username, self.password),
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
            self._build_destination_url(target),
            filepath,
            overwrite=overwrite,
            auth=(self.username, self.password),
        )
        return True

    def move(self, source_fid: str, target_fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        移动（重命名）文件或目录

        Args:
            source_fid (str): 源路径
            target_fid (str): 目标**完整路径**（不是目标父目录）
            *args: 可变位置参数
            **kwargs: 可变关键字参数，支持 ``overwrite``（默认 ``False``）

        Returns:
            bool: 移动成功返回 ``True``；源不存在、或目标已存在且不允许覆盖时返回 ``False``
        """
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
        """
        复制文件或目录

        Args:
            source_fid (str): 源路径
            target_fid (str): 目标**完整路径**（不是目标父目录）
            *args: 可变位置参数
            **kwargs: 可变关键字参数，支持 ``overwrite``（默认 ``False``）与
                ``depth``（目录复制深度，默认 ``"infinity"``，传 ``"0"`` 只复制目录本身）

        Returns:
            bool: 复制成功返回 ``True``；源不存在、或目标已存在且不允许覆盖时返回 ``False``
        """
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
        """
        重命名文件或目录（保持在原父目录下，内部走 ``MOVE``）

        Args:
            fid (str): 原路径
            new_name (str): 新名称（只是名字，不含路径）
            *args: 透传给 :meth:`move`
            **kwargs: 透传给 :meth:`move`，支持 ``overwrite``

        Returns:
            bool: 重命名成功返回 ``True``
        """
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
        """
        获取文件的下载地址

        WebDAV 没有临时直链概念，返回的就是经过百分号编码的资源 URL，
        访问时仍需带上 Basic 认证。

        Args:
            fid (str): 文件路径
            *args: 可变位置参数
            **kwargs: 可变关键字参数

        Returns:
            str: 完整的资源 URL

        Raises:
            RuntimeError: 尚未登录
        """
        return self._build_destination_url(fid)

    def get_file_sha(self, fid: str, *args: Any, **kwargs: Any) -> str | None:
        """
        通过 WebDAV PROPFIND 读取远端文件的 checksum 属性。

        说明：
        - 仅依赖服务端返回的属性，不做本地流式计算兜底
        - 优先读取 Nextcloud/ownCloud 常见的 oc:checksum
        - 如果服务端未提供 checksum，返回 None
        """
        info = self._get_path_info(fid)
        if info.get("type") != "file":
            raise ValueError(f"{fid} is not a file")

        checksum = info.get("checksum")
        if not checksum:
            return None

        # 常见格式: "SHA256:abcd..."，统一只返回哈希值部分
        match = re.match(r"^[A-Za-z0-9_-]+:(.+)$", str(checksum).strip())
        return match.group(1).strip() if match else str(checksum).strip()

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

    def _list_children(self, fid: str) -> list[DriveFile]:
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

    def _parse_propfind(self, xml_text: str) -> list[DriveFile]:
        # 解析 WebDAV 207 Multi-Status 响应，提取路径、类型、大小等基础信息
        root = ET.fromstring(xml_text)
        results: list[DriveFile] = []
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
            # 常见 checksum 属性（并非 WebDAV 标准字段，取决于服务端实现）
            checksum = (
                prop.findtext("{http://owncloud.org/ns}checksum")
                or prop.findtext("{http://nextcloud.org/ns}checksum")
                or prop.findtext("{*}checksum")
            )

            results.append(
                DriveFile(
                    fid=fid,
                    name=name,
                    size=size,
                    ext={"type": item_type, "href": href, "checksum": checksum},
                )
            )
        return results
