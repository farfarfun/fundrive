import json
import requests
from typing import Any, List, Optional, Dict
from urllib.parse import urljoin
from pathlib import Path

from funsecret import read_secret
from funget import download

from fundrive.core import BaseDrive, DriveFile
from funutil import getLogger

logger = getLogger("pcloud_drive")


class PCloudDrive(BaseDrive):
    """
    pCloud 网盘驱动类

    基于 pCloud API 实现的网盘操作类
    API 文档: https://docs.pcloud.com/
    """

    def __init__(
        self, api_server: str = "https://api.pcloud.com", *args: Any, **kwargs: Any
    ):
        """
        初始化 pCloud 驱动

        Args:
            api_server (str): pCloud API 服务器地址，默认为 https://api.pcloud.com
            *args: 位置参数
            **kwargs: 关键字参数
        """
        super().__init__(*args, **kwargs)
        self.api_server = api_server
        self.auth_token = None
        self.session = requests.Session()
        self._root_fid = "0"  # pCloud 根目录 ID 为 0

    def _normalize_fid(self, fid: str) -> str:
        """
        标准化文件夹 ID，将路径格式转换为 pCloud 文件夹 ID 格式

        Args:
            fid (str): 文件夹 ID 或路径

        Returns:
            str: 标准化的文件夹 ID
        """
        # 如果是根路径，返回根目录 ID
        if fid == "/" or fid == "root":
            return self._root_fid

        # 如果已经是数字 ID，直接返回
        if fid.isdigit():
            return fid

        # 如果是路径格式，尝试通过路径查找对应的文件夹 ID
        if fid.startswith("/"):
            return self._get_folder_id_by_path(fid)

        return fid

    def _get_folder_id_by_path(self, path: str) -> str:
        """
        通过路径获取文件夹 ID

        Args:
            path (str): 文件夹路径

        Returns:
            str: 文件夹 ID，如果不存在则返回根目录 ID
        """
        if path == "/" or path == "":
            return self._root_fid

        # 分解路径
        path_parts = [part for part in path.strip("/").split("/") if part]
        current_fid = self._root_fid

        # 逐级查找文件夹
        for part in path_parts:
            try:
                params = {"folderid": current_fid}
                result = self._make_request("listfolder", params)

                if result.get("result") == 0:
                    metadata = result.get("metadata", {})
                    contents = metadata.get("contents", [])

                    # 查找匹配的文件夹
                    found = False
                    for item in contents:
                        if item.get("isfolder", False) and item.get("name") == part:
                            current_fid = str(item.get("folderid", ""))
                            found = True
                            break

                    if not found:
                        # 如果找不到，返回当前层级的 ID
                        return current_fid
                else:
                    return current_fid

            except Exception:
                return current_fid

        return current_fid

    def _get_file_id_by_path(self, path: str) -> Optional[str]:
        """
        通过文件路径获取文件 ID

        Args:
            path (str): 文件路径，如 "/fundrive_pcloud_测试/test_upload.txt"

        Returns:
            Optional[str]: 文件 ID，如果不存在则返回 None
        """
        if not path or not path.startswith("/"):
            return None

        # 分解路径获取目录和文件名
        path_parts = path.strip("/").split("/")
        if len(path_parts) == 0:
            return None

        filename = path_parts[-1]  # 最后一部分是文件名
        dir_path = "/" + "/".join(path_parts[:-1]) if len(path_parts) > 1 else "/"

        try:
            # 获取父目录的文件夹 ID
            parent_fid = self._get_folder_id_by_path(dir_path)

            # 在父目录中查找文件
            params = {"folderid": parent_fid}
            result = self._make_request("listfolder", params)

            if result.get("result") == 0:
                metadata = result.get("metadata", {})
                contents = metadata.get("contents", [])

                # 查找匹配的文件
                for item in contents:
                    if not item.get("isfolder", False) and item.get("name") == filename:
                        file_id = str(item.get("fileid", ""))
                        return file_id

                logger.warning(f"在目录 {dir_path} 中未找到文件 {filename}")

        except Exception as e:
            logger.error(f"通过路径获取文件 ID 失败, path={path}: {e}")

        return None

    def _make_request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发起 API 请求

        Args:
            method (str): API 方法名
            params (Optional[Dict[str, Any]]): 请求参数

        Returns:
            Dict[str, Any]: API 响应结果

        Raises:
            Exception: 当 API 返回错误时抛出异常
        """
        url = urljoin(self.api_server, method)

        # 添加认证 token
        if params is None:
            params = {}
        if self.auth_token:
            params["auth"] = self.auth_token

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()

            result = response.json()

            # 检查 pCloud API 返回的错误码
            if result.get("result", 0) != 0:
                error_msg = result.get(
                    "error", f"API 错误，错误码: {result.get('result')}"
                )
                raise Exception(f"pCloud API 错误: {error_msg}")

            return result

        except requests.RequestException as e:
            raise Exception(f"请求失败: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"响应解析失败: {e}")

    def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        auth_token: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        登录 pCloud

        API 文档: https://docs.pcloud.com/protocols/http_json_protocol/authentication.html
        使用方法: userinfo (https://docs.pcloud.com/methods/general/userinfo.html)

        Args:
            username (str, optional): 用户名
            password (str, optional): 密码
            auth_token (str, optional): 认证 token（如果已有）
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 登录是否成功
        """
        username = username or read_secret("fundrive", "pcloud", "username")
        password = password or read_secret("fundrive", "pcloud", "password")
        try:
            if auth_token:
                # 使用已有的 auth token
                self.auth_token = auth_token
                # 验证 token 有效性
                result = self._make_request("userinfo")
                if result.get("result") == 0:
                    self._is_logged_in = True
                    return True
            elif username and password:
                # 使用用户名密码登录
                params = {
                    "username": username,
                    "password": password,
                    "getauth": 1,  # 获取认证 token
                }
                result = self._make_request("userinfo", params)

                if result.get("result") == 0:
                    self.auth_token = result.get("auth")
                    self._is_logged_in = True
                    return True
            else:
                raise ValueError("必须提供用户名密码或认证 token")

        except Exception as e:
            logger.error(f"登录失败: {e}")
            self._is_logged_in = False

        return False

    def _convert_metadata_to_drive_file(self, metadata: Dict[str, Any]) -> DriveFile:
        """
        将 pCloud 元数据转换为 DriveFile 对象

        Args:
            metadata (Dict[str, Any]): pCloud 元数据

        Returns:
            DriveFile: 转换后的文件对象
        """
        fid = str(
            metadata.get("folderid", metadata.get("fileid", metadata.get("id", "")))
        )
        name = metadata.get("name", "")
        size = metadata.get("size", 0) if not metadata.get("isfolder", False) else None

        # 构建扩展信息
        ext = {
            "path": metadata.get("path", ""),
            "created": metadata.get("created", ""),
            "modified": metadata.get("modified", ""),
            "isfolder": metadata.get("isfolder", False),
            "isshared": metadata.get("isshared", False),
            "parentfolderid": metadata.get("parentfolderid"),
            "contenttype": metadata.get("contenttype", ""),
            "category": metadata.get("category"),
        }

        return DriveFile(fid=fid, name=name, size=size, ext=ext)

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        检查文件或目录是否存在

        API 文档: https://docs.pcloud.com/methods/file/stat.html

        Args:
            fid (str): 文件或目录 ID 或路径
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 是否存在
        """
        try:
            normalized_fid = self._normalize_fid(fid)
            params = (
                {"folderid": normalized_fid}
                if normalized_fid != "0"
                else {"folderid": 0}
            )
            result = self._make_request("stat", params)
            return result.get("result") == 0
        except Exception as e:
            logger.error(f"检查文件存在性失败, fid={fid}: {e}")
            return False

    def mkdir(
        self,
        fid: str,
        name: str,
        return_if_exist: bool = True,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """
        创建目录

        API 文档: https://docs.pcloud.com/methods/folder/createfolder.html

        Args:
            fid (str): 父目录 ID 或路径
            name (str): 目录名称
            return_if_exist (bool): 如果目录已存在，是否返回已存在目录的 ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            str: 创建的目录 ID
        """
        normalized_fid = self._normalize_fid(fid)

        if return_if_exist:
            # 检查目录是否已存在
            dir_list = self.get_dir_list(fid)
            for dir_item in dir_list:
                if dir_item.name == name:
                    return dir_item.fid

        try:
            params = {"folderid": normalized_fid, "name": name}
            result = self._make_request("createfolder", params)

            if result.get("result") == 0:
                metadata = result.get("metadata", {})
                return str(metadata.get("folderid", ""))
            else:
                raise Exception(f"创建目录失败: {result.get('error', '未知错误')}")

        except Exception as e:
            logger.error(f"创建目录失败, fid={fid}, name={name}: {e}")
            raise Exception(f"创建目录失败: {e}")

    def delete(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        删除文件或目录

        API 文档:
        - 删除文件: https://docs.pcloud.com/methods/file/deletefile.html
        - 删除目录: https://docs.pcloud.com/methods/folder/deletefolderrecursive.html

        Args:
            fid (str): 文件或目录 ID 或路径
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 删除是否成功
        """
        try:
            # 转换文件/目录 ID
            if fid.startswith("/"):
                # 尝试获取文件 ID
                file_id = self._get_file_id_by_path(fid)
                if file_id:
                    # 是文件
                    params = {"fileid": file_id}
                    result = self._make_request("deletefile", params)
                else:
                    # 是目录
                    folder_id = self._get_folder_id_by_path(fid)
                    params = {"folderid": folder_id}
                    result = self._make_request("deletefolderrecursive", params)
            else:
                # 直接使用 ID，通过 get_file_info 判断是否为文件
                file_info = self.get_file_info(fid)
                if file_info:
                    # 是文件
                    params = {"fileid": fid}
                    result = self._make_request("deletefile", params)
                else:
                    # 是目录
                    params = {"folderid": fid}
                    result = self._make_request("deletefolderrecursive", params)

            return result.get("result") == 0

        except Exception as e:
            logger.error(f"删除文件/目录失败, fid={fid}: {e}")
            return False

    def get_file_list(self, fid: str, *args: Any, **kwargs: Any) -> List[DriveFile]:
        """
        获取目录下的文件列表

        API 文档: https://docs.pcloud.com/methods/folder/listfolder.html

        Args:
            fid (str): 目录 ID 或路径
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            List[DriveFile]: 文件列表
        """
        try:
            normalized_fid = self._normalize_fid(fid)
            params = {"folderid": normalized_fid}
            result = self._make_request("listfolder", params)

            if result.get("result") == 0:
                metadata = result.get("metadata", {})
                contents = metadata.get("contents", [])

                # 过滤出文件（非目录）
                files = []
                for item in contents:
                    if not item.get("isfolder", False):
                        files.append(self._convert_metadata_to_drive_file(item))

                return files
            else:
                return []

        except Exception as e:
            logger.error(f"获取目录列表失败, fid={fid}: {e}")
            return []

    def get_dir_list(self, fid: str, *args: Any, **kwargs: Any) -> List[DriveFile]:
        """
        获取目录下的子目录列表

        API 文档: https://docs.pcloud.com/methods/folder/listfolder.html

        Args:
            fid (str): 目录 ID 或路径
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            List[DriveFile]: 子目录列表
        """
        try:
            normalized_fid = self._normalize_fid(fid)
            params = {"folderid": normalized_fid}
            result = self._make_request("listfolder", params)

            if result.get("result") == 0:
                metadata = result.get("metadata", {})
                contents = metadata.get("contents", [])

                # 过滤出目录
                dirs = []
                for item in contents:
                    if item.get("isfolder", False):
                        dirs.append(self._convert_metadata_to_drive_file(item))

                return dirs
            else:
                return []

        except Exception as e:
            logger.error(f"获取目录列表失败, fid={fid}: {e}")
            return []

    def get_file_info(self, fid: str, *args: Any, **kwargs: Any) -> Optional[DriveFile]:
        """
        获取文件详细信息

        API 文档: https://docs.pcloud.com/methods/file/stat.html

        Args:
            fid (str): 文件 ID 或路径
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Optional[DriveFile]: 文件信息对象，如果不存在则返回 None
        """
        try:
            # 对于文件路径，需要先获取文件 ID
            if fid.startswith("/"):
                file_id = self._get_file_id_by_path(fid)
                if not file_id:
                    logger.error(f"无法找到文件, path={fid}")
                    return None
                params = {"fileid": file_id}
            else:
                params = {"fileid": fid}

            result = self._make_request("stat", params)

            if result.get("result") == 0:
                metadata = result.get("metadata", {})
                if not metadata.get("isfolder", False):
                    return self._convert_metadata_to_drive_file(metadata)

            return None

        except Exception as e:
            logger.error(f"获取文件信息失败, fid={fid}: {e}")
            return None

    def get_dir_info(self, fid: str, *args: Any, **kwargs: Any) -> Optional[DriveFile]:
        """
        获取目录详细信息

        API 文档: https://docs.pcloud.com/methods/file/stat.html

        Args:
            fid (str): 目录 ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Optional[DriveFile]: 目录信息对象，如果不存在则返回 None
        """
        try:
            params = {"folderid": fid}
            result = self._make_request("stat", params)

            if result.get("result") == 0:
                metadata = result.get("metadata", {})
                if metadata.get("isfolder", False):
                    return self._convert_metadata_to_drive_file(metadata)

            return None

        except Exception as e:
            logger.error(f"获取目录信息失败, fid={fid}: {e}")
            return None

    def download_file(
        self,
        fid: str,
        filedir: Optional[str] = None,
        filename: Optional[str] = None,
        filepath: Optional[str] = None,
        overwrite: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        下载单个文件

        API 文档: https://docs.pcloud.com/methods/file/getfilelink.html

        Args:
            fid (str): 文件 ID
            filedir (Optional[str]): 文件保存目录
            filename (Optional[str]): 文件名
            filepath (Optional[str]): 完整的文件保存路径
            overwrite (bool): 是否覆盖已存在的文件
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 下载是否成功
        """
        save_path = None
        try:
            # 获取文件信息
            file_info = self.get_file_info(fid)
            if not file_info:
                raise Exception(f"文件 {fid} 不存在")

            # 确定保存路径
            if filepath:
                save_path = Path(filepath)
            elif filedir and filename:
                save_path = Path(filedir) / filename
            elif filedir:
                save_path = Path(filedir) / file_info.name
            else:
                save_path = Path(file_info.name)

            # 检查文件是否已存在
            if save_path.exists() and not overwrite:
                logger.info(f"文件 {save_path} 已存在，跳过下载")
                return True

            # 创建保存目录
            save_path.parent.mkdir(parents=True, exist_ok=True)

            # 获取下载链接
            download_url = self.get_download_url(fid)
            if not download_url:
                raise Exception(f"无法获取文件 {fid} 的下载链接")

            # 使用 funget 工具下载文件
            download(download_url, str(save_path))

            return True

        except Exception as e:
            save_path_str = str(save_path) if save_path else "未知路径"
            logger.error(f"下载文件失败, fid={fid}, save_path={save_path_str}: {e}")
            return False

    def upload_file(
        self,
        filepath: str,
        fid: str,
        filename: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        上传单个文件

        API 文档: https://docs.pcloud.com/methods/file/uploadfile.html

        Args:
            filepath (str): 本地文件路径
            fid (str): 目标目录 ID
            filename (str, optional): 目标文件名，如果不指定则使用本地文件名
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 上传是否成功
        """
        try:
            file_path = Path(filepath)
            if not file_path.exists():
                raise Exception(f"文件 {filepath} 不存在")

            # 规范化目标目录 ID
            normalized_fid = self._normalize_fid(fid)

            # 构建上传 URL
            url = urljoin(self.api_server, "uploadfile")

            # 准备参数
            params = {
                "folderid": normalized_fid,
                "renameifexists": 1,  # 如果文件已存在则重命名
            }
            if self.auth_token:
                params["auth"] = self.auth_token

            # 确定上传文件名：优先使用指定的文件名，否则使用本地文件名
            upload_filename = filename if filename else file_path.name

            # 准备文件数据
            files = {
                "file": (
                    upload_filename,
                    open(file_path, "rb"),
                    "application/octet-stream",
                )
            }

            try:
                # 发起上传请求
                response = self.session.post(url, params=params, files=files)
                response.raise_for_status()

                result = response.json()

                # 检查上传结果
                if result.get("result") == 0:
                    return True
                else:
                    error_msg = result.get(
                        "error", f"上传失败，错误码: {result.get('result')}"
                    )
                    raise Exception(f"pCloud API 错误: {error_msg}")

            finally:
                # 关闭文件
                files["file"][1].close()

        except Exception as e:
            logger.error(f"上传文件失败, filepath={filepath}, fid={fid}: {e}")
            return False

    def get_download_url(self, fid: str, *args: Any, **kwargs: Any) -> str:
        """
        获取文件下载链接

        API 文档: https://docs.pcloud.com/methods/file/getfilelink.html

        Args:
            fid (str): 文件 ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            str: 下载链接
        """
        try:
            # 对于文件路径，我们需要使用 path 参数而不是 fileid
            if fid.startswith("/"):
                params = {"path": fid}
            else:
                params = {"fileid": fid}
            result = self._make_request("getfilelink", params)

            if result.get("result") == 0:
                # pCloud 返回的下载链接通常在 hosts 数组中
                hosts = result.get("hosts", [])
                path = result.get("path", "")

                if hosts and path:
                    # 构建完整的下载链接
                    host = hosts[0]  # 使用第一个可用的主机
                    download_url = f"https://{host}{path}"
                    return download_url

            return ""

        except Exception as e:
            logger.error(f"获取下载链接失败, fid={fid}: {e}")
            return ""

    def rename(self, fid: str, new_name: str, *args: Any, **kwargs: Any) -> bool:
        """
        重命名文件或目录

        API 文档:
        - 重命名文件: https://docs.pcloud.com/methods/file/renamefile.html
        - 重命名目录: https://docs.pcloud.com/methods/folder/renamefolder.html

        Args:
            fid (str): 文件/目录 ID
            new_name (str): 新名称
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 重命名是否成功
        """
        try:
            # 先判断是文件还是目录
            file_info = self.get_file_info(fid)
            if file_info:
                # 是文件，需要获取文件 ID
                if fid.startswith("/"):
                    file_id = self._get_file_id_by_path(fid)
                    if not file_id:
                        raise Exception(f"无法找到文件, path={fid}")
                    params = {"fileid": file_id, "toname": new_name}
                else:
                    params = {"fileid": fid, "toname": new_name}
                result = self._make_request("renamefile", params)
            else:
                # 是目录，使用文件夹 ID
                normalized_fid = self._normalize_fid(fid)
                params = {"folderid": normalized_fid, "toname": new_name}
                result = self._make_request("renamefolder", params)

            return result.get("result") == 0

        except Exception as e:
            logger.error(f"重命名失败, fid={fid}, new_name={new_name}: {e}")
            return False

    def move(self, source_fid: str, target_fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        移动文件或目录

        API 文档:
        - 移动文件: https://docs.pcloud.com/methods/file/renamefile.html (使用 tofolderid 参数)
        - 移动目录: https://docs.pcloud.com/methods/folder/renamefolder.html (使用 tofolderid 参数)

        Args:
            source_fid (str): 源文件/目录 ID
            target_fid (str): 目标目录 ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 移动是否成功
        """
        try:
            # 先判断是文件还是目录
            file_info = self.get_file_info(source_fid)
            if file_info:
                # 是文件
                params = {"fileid": source_fid, "tofolderid": target_fid}
                result = self._make_request("renamefile", params)
            else:
                # 是目录
                params = {"folderid": source_fid, "tofolderid": target_fid}
                result = self._make_request("renamefolder", params)

            return result.get("result") == 0

        except Exception as e:
            logger.error(
                f"移动失败, source_fid={source_fid}, target_fid={target_fid}: {e}"
            )
            return False

    def copy(self, source_fid: str, target_fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        复制文件或目录

        API 文档:
        - 复制文件: https://docs.pcloud.com/methods/file/copyfile.html
        - 复制目录: https://docs.pcloud.com/methods/folder/copyfolder.html

        Args:
            source_fid (str): 源文件/目录 ID 或路径
            target_fid (str): 目标目录 ID 或路径
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 复制是否成功
        """
        try:
            # 转换源文件/目录 ID
            if source_fid.startswith("/"):
                # 尝试获取文件 ID
                source_file_id = self._get_file_id_by_path(source_fid)
                if source_file_id:
                    # 是文件
                    source_id = source_file_id
                    is_file = True
                else:
                    # 是目录
                    source_id = self._get_folder_id_by_path(source_fid)
                    is_file = False
            else:
                # 直接使用 ID，通过 get_file_info 判断是否为文件
                source_id = source_fid
                file_info = self.get_file_info(source_fid)
                is_file = file_info is not None

            # 转换目标目录 ID
            if target_fid.startswith("/"):
                target_id = self._get_folder_id_by_path(target_fid)
            else:
                target_id = target_fid

            # 根据类型调用相应的 API
            if is_file:
                params = {"fileid": source_id, "tofolderid": target_id}
                result = self._make_request("copyfile", params)
            else:
                params = {"folderid": source_id, "tofolderid": target_id}
                result = self._make_request("copyfolder", params)

            return result.get("result") == 0

        except Exception as e:
            logger.error(
                f"复制失败, source_fid={source_fid}, target_fid={target_fid}: {e}"
            )
            return False

    def get_quota(self, *args: Any, **kwargs: Any) -> dict:
        """
        获取网盘空间使用情况

        API 文档: https://docs.pcloud.com/methods/general/userinfo.html

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            dict: 包含总空间、已用空间等信息的字典
        """
        try:
            result = self._make_request("userinfo")

            if result.get("result") == 0:
                quota_info = {
                    "total": result.get("quota", 0),
                    "used": result.get("usedquota", 0),
                    "free": result.get("quota", 0) - result.get("usedquota", 0),
                }
                return quota_info
            else:
                return {"total": 0, "used": 0, "free": 0}

        except Exception as e:
            logger.error(f"获取配额信息失败: {e}")
            return {"total": 0, "used": 0, "free": 0}

    def search(
        self,
        keyword: str,
        fid: Optional[str] = None,
        file_type: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> List[DriveFile]:
        """
        搜索文件或目录

        API 文档: https://docs.pcloud.com/methods/general/search.html
        注意: 这里使用 searchpublinks 作为示例，实际可能需要根据具体需求调整

        Args:
            keyword (str): 搜索关键词
            fid (Optional[str]): 搜索的起始目录 ID，默认从根目录开始
            file_type (Optional[str]): 文件类型筛选
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            List[DriveFile]: 符合条件的文件列表
        """
        try:
            params = {"query": keyword}
            if fid:
                # 对于搜索功能，如果是路径格式，需要转换为文件夹ID
                if fid.startswith("/"):
                    # 对于路径格式的搜索，我们暂时使用根目录ID
                    # 在实际使用中，可能需要通过API查找路径对应的文件夹ID
                    params["folderid"] = self._normalize_fid(fid)
                else:
                    params["folderid"] = fid

            result = self._make_request("search", params)

            if result.get("result") == 0:
                results = result.get("results", [])
                files = []

                for item in results:
                    # 根据文件类型筛选
                    if file_type:
                        content_type = item.get("contenttype", "")
                        if file_type.lower() not in content_type.lower():
                            continue

                    files.append(self._convert_metadata_to_drive_file(item))

                return files
            else:
                return []

        except Exception as e:
            logger.error(
                f"搜索失败, keyword={keyword}, fid={fid}, file_type={file_type}: {e}"
            )
            return []

    def share(
        self,
        *fids: str,
        password: str = "",
        expire_days: int = 0,
        description: str = "",
    ) -> Any:
        """
        分享文件或目录

        API 文档: https://docs.pcloud.com/methods/public_links/getpublink.html
        相关文档: https://docs.pcloud.com/methods/sharing/

        Args:
            *fids: 要分享的文件或目录 ID 列表
            password (str): 分享密码
            expire_days (int): 分享链接有效期(天)，0表示永久有效
            description (str): 分享描述

        Returns:
            Any: 分享链接信息
        """
        try:
            # pCloud 分享 API 需要先创建链接，然后设置属性
            # 简化版本：只支持单个文件/文件夹分享
            if not fids:
                return None

            fid = fids[0]  # 只处理第一个文件

            # 转换文件/目录 ID
            if fid.startswith("/"):
                # 尝试获取文件 ID
                file_id = self._get_file_id_by_path(fid)
                if file_id:
                    # 是文件，使用 getfilepublink
                    params = {"fileid": file_id}
                    api_method = "getfilepublink"
                else:
                    # 是文件夹，使用 getfolderpublink
                    folder_id = self._get_folder_id_by_path(fid)
                    params = {"folderid": folder_id}
                    api_method = "getfolderpublink"
            else:
                # 直接使用 ID，通过 get_file_info 判断是否为文件
                file_info = self.get_file_info(fid)
                if file_info:
                    # 是文件，使用 getfilepublink
                    params = {"fileid": fid}
                    api_method = "getfilepublink"
                else:
                    # 是文件夹，使用 getfolderpublink
                    params = {"folderid": fid}
                    api_method = "getfolderpublink"

            # 添加可选参数
            if password:
                params["password"] = password
            if expire_days > 0:
                params["expire"] = expire_days

            result = self._make_request(api_method, params)

            if result.get("result") == 0:
                return {
                    "link": result.get("link", ""),
                    "linkid": result.get("linkid", ""),
                    "code": result.get("code", ""),
                }
            else:
                return None

        except Exception as e:
            logger.error(
                f"分享失败, fids={fids}, password={password}, expire_days={expire_days}: {e}"
            )
            return None

    def get_recycle_list(self, *args: Any, **kwargs: Any) -> List[DriveFile]:
        """
        获取回收站文件列表

        注意：pCloud 不支持回收站功能

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            List[DriveFile]: 空列表（pCloud 不支持回收站）
        """
        logger.warning("pCloud 不支持回收站功能")
        return []

    def restore(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        从回收站恢复文件

        注意：pCloud 不支持回收站功能

        Args:
            fid (str): 文件ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: False（pCloud 不支持回收站）
        """
        logger.warning("pCloud 不支持回收站恢复功能")
        return False

    def clear_recycle(self, *args: Any, **kwargs: Any) -> bool:
        """
        清空回收站

        注意：pCloud 不支持回收站功能

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: False（pCloud 不支持回收站）
        """
        logger.warning("pCloud 不支持回收站清空功能")
        return False

    def get_upload_url(self, fid: str, filename: str, *args: Any, **kwargs: Any) -> str:
        """
        获取文件上传链接

        注意：pCloud 使用直接上传 API，不提供预签名上传 URL

        Args:
            fid (str): 目标目录ID
            filename (str): 文件名
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            str: 空字符串（pCloud 不支持预签名上传URL）
        """
        logger.warning("pCloud 不支持预签名上传URL，请使用 upload_file 方法")
        return ""

    def save_shared(
        self, shared_url: str, fid: str, password: Optional[str] = None
    ) -> bool:
        """
        保存分享的文件到网盘

        注意：pCloud 不直接支持通过分享链接保存文件的 API

        Args:
            shared_url (str): 分享链接
            fid (str): 保存到的目录ID
            password (Optional[str]): 分享密码

        Returns:
            bool: False（pCloud 不支持此功能）
        """
        logger.warning("pCloud 不支持通过分享链接直接保存文件功能")
        return False
