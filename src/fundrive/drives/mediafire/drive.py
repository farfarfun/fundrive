#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MediaFire云存储驱动实现

MediaFire是一个流行的云存储服务，提供文件存储、共享和同步功能。
本驱动基于MediaFire API实现，支持文件上传、下载、管理等操作。

主要功能:
- 文件上传下载
- 目录管理
- 文件搜索
- 分享链接生成
- 存储配额查询

作者: FunDrive Team
"""

import os
import json
import hashlib
import requests
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

from funsecret import read_secret
from funutil import getLogger

from fundrive.core import BaseDrive, DriveFile

logger = getLogger("fundrive")


class MediaFireDrive(BaseDrive):
    """
    MediaFire云存储驱动

    基于MediaFire Core API实现的云存储驱动，提供完整的文件管理功能。
    支持API Key认证和Session Token管理。
    """

    # MediaFire API基础URL
    API_BASE_URL = "https://www.mediafire.com/api/1.5/"

    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        app_id: Optional[str] = None,
        api_key: Optional[str] = None,
        session_token: Optional[str] = None,
        **kwargs,
    ):
        """
        初始化MediaFire驱动

        Args:
            email: MediaFire账户邮箱
            password: MediaFire账户密码
            app_id: MediaFire应用ID
            api_key: MediaFire API密钥
            session_token: 会话令牌（可选，用于避免重复登录）
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)

        # 从配置或环境变量获取认证信息
        self.email = (
            email
            or read_secret("fundrive", "mediafire", "email")
            or os.getenv("MEDIAFIRE_EMAIL")
        )
        self.password = (
            password
            or read_secret("fundrive", "mediafire", "password")
            or os.getenv("MEDIAFIRE_PASSWORD")
        )
        self.app_id = (
            app_id
            or read_secret("fundrive", "mediafire", "app_id")
            or os.getenv("MEDIAFIRE_APP_ID")
        )
        self.api_key = (
            api_key
            or read_secret("fundrive", "mediafire", "api_key")
            or os.getenv("MEDIAFIRE_API_KEY")
        )
        self.session_token = (
            session_token
            or read_secret("fundrive", "mediafire", "session_token")
            or os.getenv("MEDIAFIRE_SESSION_TOKEN")
        )

        # 初始化HTTP会话
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "FunDrive MediaFire Client/1.0"})

        # 验证必要参数
        if not all([self.email, self.password, self.app_id, self.api_key]):
            logger.warning("MediaFire认证信息不完整，某些功能可能无法使用")

    def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any] = None,
        method: str = "GET",
        data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        发送API请求

        Args:
            endpoint: API端点
            params: URL参数
            method: HTTP方法
            data: 请求数据

        Returns:
            API响应数据

        Raises:
            Exception: 请求失败时抛出异常
        """
        url = urljoin(self.API_BASE_URL, endpoint)

        # 准备请求参数
        if params is None:
            params = {}

        # 添加API密钥
        if self.api_key:
            params["api_key"] = self.api_key

        # 添加会话令牌（如果已登录）
        if self.session_token:
            params["session_token"] = self.session_token

        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, params=params, data=data, timeout=30)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            response.raise_for_status()

            # 解析JSON响应
            result = response.json()

            # 检查API响应状态
            if result.get("response", {}).get("result") != "Success":
                error_msg = result.get("response", {}).get("message", "未知错误")
                logger.error(f"MediaFire API错误: {error_msg}")
                raise Exception(f"MediaFire API错误: {error_msg}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"MediaFire API请求失败: {e}")
            raise Exception(f"MediaFire API请求失败: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"MediaFire API响应解析失败: {e}")
            raise Exception(f"MediaFire API响应解析失败: {e}")

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        生成API请求签名

        Args:
            params: 请求参数

        Returns:
            签名字符串
        """
        # 按键名排序参数
        sorted_params = sorted(params.items())

        # 构建签名字符串
        signature_string = ""
        for key, value in sorted_params:
            signature_string += f"{key}={value}"

        # 添加API密钥
        signature_string += self.api_key

        # 计算MD5哈希
        signature = hashlib.md5(signature_string.encode("utf-8")).hexdigest()

        return signature

    def login(self) -> bool:
        """
        登录MediaFire账户

        Returns:
            登录是否成功
        """
        try:
            logger.info("正在登录MediaFire...")

            # 如果已有会话令牌，先验证其有效性
            if self.session_token:
                try:
                    result = self._make_request("user/get_info.php")
                    if result:
                        logger.info("✅ 使用现有会话令牌登录成功")
                        return True
                except Exception as e:
                    logger.info("现有会话令牌无效，重新登录", e)
                    self.session_token = None

            # 检查必要的登录参数
            if not all([self.email, self.password, self.app_id, self.api_key]):
                logger.error("❌ MediaFire登录信息不完整")
                return False

            # 准备登录参数
            params = {
                "email": self.email,
                "password": self.password,
                "application_id": self.app_id,
                "api_key": self.api_key,
            }

            # 生成签名
            params["signature"] = self._generate_signature(params)

            # 发送登录请求
            result = self._make_request(
                "user/get_session_token.php", params=params, method="POST"
            )

            # 提取会话令牌
            session_token = result.get("response", {}).get("session_token")
            if session_token:
                self.session_token = session_token
                logger.info("✅ MediaFire登录成功")
                return True
            else:
                logger.error("❌ 未能获取会话令牌")
                return False

        except Exception as e:
            logger.error(f"❌ MediaFire登录失败: {e}")
            return False

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        检查文件或目录是否存在

        Args:
            fid: 文件或目录ID，"root"表示根目录

        Returns:
            文件或目录是否存在
        """
        try:
            # 先尝试作为目录检查
            try:
                result = self._make_request(
                    "folder/get_info.php", params={"folder_key": fid}
                )
                if result is not None:
                    return True
            except Exception as e:
                logger.error("目录检查失败", e)

            # 再尝试作为文件检查
            try:
                result = self._make_request(
                    "file/get_info.php", params={"quick_key": fid}
                )
                return result is not None
            except Exception as e:
                logger.debug("", e)
                return False

        except Exception as e:
            logger.error(f"检查文件存在性失败: {e}")
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

        Args:
            fid: 父目录ID
            name: 目录名
            return_if_exist: 如果目录已存在，是否返回已存在目录的ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            创建的目录ID
        """
        try:
            logger.info(f"正在创建目录: {name}")

            # 检查目录是否已存在
            if return_if_exist and self.exist(fid, name):
                logger.info(f"目录 {name} 已存在")
                # 尝试获取已存在目录的ID
                for dir_info in self.get_dir_list(fid):
                    if dir_info.name == name:
                        return dir_info.fid
                return fid  # 如果无法获取具体ID，返回父目录ID

            # 创建目录
            params = {"parent_key": fid if fid != "root" else "", "foldername": name}

            result = self._make_request(
                "folder/create.php", params=params, method="POST"
            )

            if result and result.get("response", {}).get("folder_key"):
                folder_key = result["response"]["folder_key"]
                logger.info(f"✅ 目录 {name} 创建成功，ID: {folder_key}")
                return folder_key
            else:
                logger.error(f"❌ 目录 {name} 创建失败")
                return ""

        except Exception as e:
            logger.error(f"创建目录失败: {e}")
            return ""

    def delete(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        删除文件或目录

        Args:
            fid: 文件或目录ID

        Returns:
            删除是否成功
        """
        try:
            logger.info(f"正在删除文件/目录: {fid}")

            # 先尝试作为文件删除
            try:
                result = self._make_request(
                    "file/delete.php", params={"quick_key": fid}, method="POST"
                )
                if result:
                    logger.info("✅ 文件删除成功")
                    return True
            except Exception as e:
                logger.error("删除失败", e)

            # 再尝试作为目录删除
            try:
                result = self._make_request(
                    "folder/delete.php", params={"folder_key": fid}, method="POST"
                )
                if result:
                    logger.info("✅ 目录删除成功")
                    return True
            except Exception as e:
                logger.error("删除失败", e)

            logger.error("❌ 删除失败")
            return False

        except Exception as e:
            logger.error(f"删除文件/目录失败: {e}")
            return False

    def get_file_list(self, fid: str = "root", *args, **kwargs) -> List[DriveFile]:
        """
        获取文件列表

        Args:
            fid: 目录ID

        Returns:
            文件列表
        """
        try:
            logger.info(f"正在获取文件列表: {fid}")

            params = {
                "folder_key": fid if fid != "root" else "",
                "content_type": "files",
            }

            result = self._make_request("folder/get_content.php", params=params)

            files = []
            folder_content = result.get("response", {}).get("folder_content", {})
            file_list = folder_content.get("files", [])

            for item in file_list:
                drive_file = DriveFile(
                    fid=item.get("quickkey", ""),
                    name=item.get("filename", ""),
                    size=int(item.get("size", 0)),
                    ext={
                        "type": "file",
                        "created": item.get("created", ""),
                        "modified": item.get(
                            "created", ""
                        ),  # MediaFire可能没有修改时间
                        "mimetype": item.get("mimetype", ""),
                        "download_url": item.get("links", {}).get(
                            "normal_download", ""
                        ),
                    },
                )
                files.append(drive_file)

            logger.info(f"✅ 获取到 {len(files)} 个文件")
            return files

        except Exception as e:
            logger.error(f"获取文件列表失败: {e}")
            return []

    def get_dir_list(self, fid: str = "root", *args, **kwargs) -> List[DriveFile]:
        """
        获取目录列表

        Args:
            fid: 目录ID

        Returns:
            目录列表
        """
        try:
            logger.info(f"正在获取目录列表: {fid}")

            params = {
                "folder_key": fid if fid != "root" else "",
                "content_type": "folders",
            }

            result = self._make_request("folder/get_content.php", params=params)

            dirs = []
            folder_content = result.get("response", {}).get("folder_content", {})
            folder_list = folder_content.get("folders", [])

            for item in folder_list:
                drive_file = DriveFile(
                    fid=item.get("folderkey", ""),
                    name=item.get("name", ""),
                    size=0,  # 目录没有大小
                    ext={
                        "type": "folder",
                        "created": item.get("created", ""),
                        "file_count": int(item.get("file_count", 0)),
                        "folder_count": int(item.get("folder_count", 0)),
                    },
                )
                dirs.append(drive_file)

            logger.info(f"✅ 获取到 {len(dirs)} 个目录")
            return dirs

        except Exception as e:
            logger.error(f"获取目录列表失败: {e}")
            return []

    def get_file_info(self, fid: str, *args, **kwargs) -> Optional[DriveFile]:
        """
        获取文件信息

        Args:
            fid: 文件ID

        Returns:
            文件信息
        """
        try:
            logger.info(f"正在获取文件信息: {fid}")

            result = self._make_request("file/get_info.php", params={"quick_key": fid})

            file_info = result.get("response", {}).get("file_info", {})

            if file_info:
                return DriveFile(
                    fid=file_info.get("quickkey", fid),
                    name=file_info.get("filename", ""),
                    size=int(file_info.get("size", 0)),
                    ext={
                        "type": "file",
                        "created": file_info.get("created", ""),
                        "mimetype": file_info.get("mimetype", ""),
                        "download_url": file_info.get("links", {}).get(
                            "normal_download", ""
                        ),
                        "description": file_info.get("description", ""),
                    },
                )

            return None

        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return None

    def get_dir_info(self, fid: str, *args, **kwargs) -> Optional[DriveFile]:
        """
        获取目录信息

        Args:
            fid: 目录ID

        Returns:
            目录信息
        """
        try:
            logger.info(f"正在获取目录信息: {fid}")

            result = self._make_request(
                "folder/get_info.php", params={"folder_key": fid}
            )

            folder_info = result.get("response", {}).get("folder_info", {})

            if folder_info:
                return DriveFile(
                    fid=folder_info.get("folderkey", fid),
                    name=folder_info.get("name", ""),
                    size=0,
                    ext={
                        "type": "folder",
                        "created": folder_info.get("created", ""),
                        "file_count": int(folder_info.get("file_count", 0)),
                        "folder_count": int(folder_info.get("folder_count", 0)),
                        "description": folder_info.get("description", ""),
                    },
                )

            return None

        except Exception as e:
            logger.error(f"获取目录信息失败: {e}")
            return None

    def upload_file(
        self,
        filepath: str,
        fid: str,
        filename: str = None,
        callback: callable = None,
        **kwargs,
    ) -> bool:
        """
        上传文件

        Args:
            filepath: 本地文件路径
            fid: 目标目录ID
            filename: 上传后的文件名
            callback: 进度回调函数

        Returns:
            上传是否成功
        """
        try:
            if not os.path.exists(filepath):
                logger.error(f"文件不存在: {filepath}")
                return False

            filename = filename or os.path.basename(filepath)
            logger.info(f"正在上传文件: {filename}")

            # 获取上传URL
            upload_result = self._make_request("upload/check.php", method="POST")
            upload_url = upload_result.get("response", {}).get("upload_url")

            if not upload_url:
                logger.error("获取上传URL失败")
                return False

            # 准备上传参数
            upload_params = {
                "session_token": self.session_token,
                "folder_key": fid if fid != "root" else "",
                "filename": filename,
            }

            # 上传文件
            with open(filepath, "rb") as f:
                files = {"Filedata": (filename, f, "application/octet-stream")}

                response = self.session.post(
                    upload_url,
                    data=upload_params,
                    files=files,
                    timeout=300,  # 5分钟超时
                )

                response.raise_for_status()
                result = response.json()

                if result.get("response", {}).get("result") == "Success":
                    logger.info(f"✅ 文件 {filename} 上传成功")
                    return True
                else:
                    error_msg = result.get("response", {}).get("message", "未知错误")
                    logger.error(f"❌ 文件上传失败: {error_msg}")
                    return False

        except Exception as e:
            logger.error(f"上传文件失败: {e}")
            return False

    def download_file(
        self,
        fid: str,
        save_dir: Optional[str] = None,
        filename: Optional[str] = None,
        filepath: Optional[str] = None,
        overwrite: bool = False,
        callback: callable = None,
        *args,
        **kwargs,
    ) -> bool:
        """
        下载文件

        Args:
            fid: 文件ID
            save_dir: 文件保存目录
            filename: 文件名
            filepath: 完整的文件保存路径
            overwrite: 是否覆盖已存在的文件
            callback: 进度回调函数

        Returns:
            下载是否成功
        """
        try:
            logger.info(f"正在下载文件: {fid}")

            # 获取文件信息和下载链接
            file_info = self.get_file_info(fid)
            if not file_info:
                logger.error("获取文件信息失败")
                return False

            download_url = file_info.ext.get("download_url")
            if not download_url:
                # 获取下载链接
                result = self._make_request(
                    "file/get_links.php", params={"quick_key": fid}
                )
                links = result.get("response", {}).get("links", [])
                if links:
                    download_url = links[0].get("direct_download")

            if not download_url:
                logger.error("获取下载链接失败")
                return False

            # 确定保存路径
            if filepath:
                local_path = filepath
            elif save_dir and filename:
                local_path = os.path.join(save_dir, filename)
            elif save_dir:
                local_path = os.path.join(save_dir, file_info.name)
            else:
                local_path = file_info.name

            # 检查文件是否已存在
            if os.path.exists(local_path) and not overwrite:
                logger.warning(f"文件已存在，跳过下载: {local_path}")
                return False

            # 确保目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # 下载文件
            response = self.session.get(download_url, stream=True, timeout=300)
            response.raise_for_status()

            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        if callback:
                            callback(len(chunk))

            logger.info(f"✅ 文件下载成功: {local_path}")
            return True

        except Exception as e:
            logger.error(f"下载文件失败: {e}")
            return False

    # 高级功能实现
    def search(self, keyword: str, fid: str = "root", **kwargs) -> List[DriveFile]:
        """
        搜索文件

        Args:
            keyword: 搜索关键词
            fid: 搜索目录ID

        Returns:
            搜索结果列表
        """
        try:
            logger.info(f"正在搜索文件: {keyword}")

            params = {"query": keyword, "folder_key": fid if fid != "root" else ""}

            result = self._make_request("file/search.php", params=params)

            results = []
            search_results = result.get("response", {}).get("results", [])

            for item in search_results:
                drive_file = DriveFile(
                    fid=item.get("quickkey", ""),
                    name=item.get("filename", ""),
                    size=int(item.get("size", 0)),
                    ext={
                        "type": "file",
                        "created": item.get("created", ""),
                        "mimetype": item.get("mimetype", ""),
                        "download_url": item.get("links", {}).get(
                            "normal_download", ""
                        ),
                    },
                )
                results.append(drive_file)

            logger.info(f"搜索完成，找到 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    def share(self, fid: str, **kwargs) -> Optional[str]:
        """
        创建分享链接

        Args:
            fid: 文件ID

        Returns:
            分享链接
        """
        try:
            logger.info(f"正在创建分享链接: {fid}")

            result = self._make_request("file/get_links.php", params={"quick_key": fid})

            links = result.get("response", {}).get("links", [])
            if links:
                share_url = links[0].get("normal_download")
                if share_url:
                    logger.info("✅ 分享链接创建成功")
                    return share_url

            logger.error("❌ 分享链接创建失败")
            return None

        except Exception as e:
            logger.error(f"创建分享链接失败: {e}")
            return None

    def get_quota(self) -> Optional[Dict[str, int]]:
        """
        获取存储配额信息

        Returns:
            配额信息字典，包含total、used、available字段
        """
        try:
            logger.info("正在获取存储配额信息...")

            result = self._make_request("user/get_info.php")

            user_info = result.get("response", {}).get("user_info", {})

            if user_info:
                # MediaFire的存储信息（字节）
                total_space = int(user_info.get("storage_limit", 0))
                used_space = int(user_info.get("used_storage_size", 0))
                available_space = total_space - used_space

                quota_info = {
                    "total": total_space,
                    "used": used_space,
                    "available": available_space,
                }

                logger.info(
                    f"✅ 存储配额: 总计 {total_space / (1024**3):.2f}GB, "
                    f"已用 {used_space / (1024**3):.2f}GB, "
                    f"可用 {available_space / (1024**3):.2f}GB"
                )

                return quota_info

            return None

        except Exception as e:
            logger.error(f"获取存储配额失败: {e}")
            return None
