#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenXLab云存储驱动实现

OpenXLab是上海人工智能实验室推出的开放平台，提供数据集存储和AI模型托管服务。
本驱动基于OpenXLab API实现，支持数据集的浏览、下载等操作。

主要功能:
- 数据集浏览
- 文件下载
- 目录操作
- 文件信息查询

作者: FunDrive Team
"""

import os
from typing import Any, Dict, List, Optional

import requests
from funget import simple_download
from funsecret import read_secret
from funutil import getLogger

from fundrive.core import BaseDrive, DriveFile

logger = getLogger("fundrive")


class OpenXLabDrive(BaseDrive):
    """
    OpenXLab云存储驱动

    基于OpenXLab API实现的云存储驱动，主要用于访问和下载数据集。
    支持Cookie认证和数据集文件管理。
    """

    def __init__(
        self,
        opendatalab_session: Optional[str] = None,
        ssouid: Optional[str] = None,
        **kwargs,
    ):
        """
        初始化OpenXLab驱动

        Args:
            opendatalab_session: OpenDataLab会话Cookie
            ssouid: SSO用户ID Cookie
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)

        self.host = "https://openxlab.org.cn"
        self.cookies = {}
        self.headers = {"accept": "application/json"}

        # 从配置或环境变量获取认证信息
        self.opendatalab_session = (
            opendatalab_session
            or read_secret("fundrive", "openxlab", "opendatalab_session")
            or os.getenv("OPENXLAB_SESSION")
        )
        self.ssouid = (
            ssouid
            or read_secret("fundrive", "openxlab", "ssouid")
            or os.getenv("OPENXLAB_SSOUID")
        )

    def login(
        self,
        opendatalab_session: Optional[str] = None,
        ssouid: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        登录OpenXLab

        Args:
            opendatalab_session: OpenDataLab会话Cookie
            ssouid: SSO用户ID Cookie

        Returns:
            登录是否成功
        """
        try:
            logger.info("正在登录OpenXLab...")

            # 更新认证信息
            if opendatalab_session:
                self.opendatalab_session = opendatalab_session
            if ssouid:
                self.ssouid = ssouid

            # 设置Cookie
            self.cookies.update(
                {
                    "opendatalab_session": self.opendatalab_session,
                    "ssouid": self.ssouid,
                }
            )

            # 验证登录状态（尝试访问API）
            try:
                test_response = requests.get(
                    f"{self.host}/datasets/api/v2/datasets",
                    headers=self.headers,
                    cookies=self.cookies,
                    timeout=10,
                )
                if test_response.status_code == 200:
                    logger.info("✅ OpenXLab登录成功")
                    return True
                else:
                    logger.warning("⚠️ OpenXLab登录状态未知，将尝试继续")
                    return True
            except Exception as e:
                logger.warning("⚠️ 无法验证OpenXLab登录状态，将尝试继续", e)
                return True

        except Exception as e:
            logger.error(f"❌ OpenXLab登录失败: {e}")
            return False

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        检查数据集是否存在

        Args:
            fid: 数据集名称（格式：owner/dataset_name）

        Returns:
            数据集是否存在
        """
        try:
            # 检查数据集是否存在
            dataset_name = fid.replace("/", ",")
            resp = requests.get(
                url=f"{self.host}/datasets/api/v2/datasets/{dataset_name}",
                headers=self.headers,
                cookies=self.cookies,
                timeout=10,
            )
            return resp.status_code == 200

        except Exception as e:
            logger.error(f"检查数据集存在性失败: {e}")
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
        创建目录（OpenXLab不支持创建目录）

        Args:
            fid: 父目录ID
            name: 目录名
            return_if_exist: 如果目录已存在，是否返回已存在目录的ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            创建的目录ID（此驱动不支持创建，返回空字符串）
        """
        logger.warning("OpenXLab是只读平台，不支持创建目录")
        return ""

    def delete(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        删除文件或目录（OpenXLab不支持删除）

        Args:
            fid: 文件或目录ID

        Returns:
            删除是否成功
        """
        logger.warning("OpenXLab是只读平台，不支持删除操作")
        return False

    def get_file_list(self, fid: str = "root", *args, **kwargs) -> List[DriveFile]:
        """
        获取数据集文件列表

        Args:
            fid: 数据集名称（格式：owner/dataset_name）

        Returns:
            文件列表
        """
        try:
            logger.info(f"正在获取数据集文件列表: {fid}")

            if fid == "root":
                logger.warning("请指定具体的数据集名称，格式：owner/dataset_name")
                return []

            dataset_name = fid.replace("/", ",")
            data = {"recursive": True}

            resp = requests.get(
                url=f"{self.host}/datasets/api/v2/datasets/{dataset_name}/r/main",
                params=data,
                headers=self.headers,
                cookies=self.cookies,
                timeout=30,
            )

            if resp.status_code != 200:
                logger.error(f"获取数据集信息失败: {resp.status_code}")
                return []

            result_dict = resp.json()["data"]["list"]

            files = []
            for item in result_dict:
                if item.get("type") == "file":
                    drive_file = DriveFile(
                        fid=item.get("path", ""),
                        name=os.path.basename(item.get("path", "")),
                        size=int(item.get("size", 0)),
                        ext={
                            "type": "file",
                            "dataset_id": item.get("dataset_id", ""),
                            "path": item.get("path", ""),
                            "modified": item.get("last_modified", ""),
                            "download_url": f"{self.host}/datasets/resolve/{item.get('dataset_id')}/main/{item.get('path')}",
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
        获取数据集目录列表

        Args:
            fid: 数据集名称（格式：owner/dataset_name）

        Returns:
            目录列表
        """
        try:
            logger.info(f"正在获取数据集目录列表: {fid}")

            if fid == "root":
                logger.warning("请指定具体的数据集名称，格式：owner/dataset_name")
                return []

            dataset_name = fid.replace("/", ",")
            data = {"recursive": True}

            resp = requests.get(
                url=f"{self.host}/datasets/api/v2/datasets/{dataset_name}/r/main",
                params=data,
                headers=self.headers,
                cookies=self.cookies,
                timeout=30,
            )

            if resp.status_code != 200:
                logger.error(f"获取数据集信息失败: {resp.status_code}")
                return []

            result_dict = resp.json()["data"]["list"]

            # 提取目录信息
            dirs = []
            dir_paths = set()

            for item in result_dict:
                if item.get("type") == "file":
                    file_path = item.get("path", "")
                    # 提取目录路径
                    dir_path = os.path.dirname(file_path)
                    if dir_path and dir_path not in dir_paths:
                        dir_paths.add(dir_path)

                        drive_file = DriveFile(
                            fid=dir_path,
                            name=os.path.basename(dir_path),
                            size=0,
                            ext={
                                "type": "folder",
                                "dataset_id": item.get("dataset_id", ""),
                                "path": dir_path,
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
            fid: 文件路径（格式：dataset_id/file_path）

        Returns:
            文件信息
        """
        try:
            logger.info(f"正在获取文件信息: {fid}")

            # 解析文件ID
            if "/" not in fid:
                logger.error("文件ID格式错误，应为：dataset_id/file_path")
                return None

            parts = fid.split("/", 1)
            dataset_id = parts[0]
            file_path = "/" + parts[1] if not parts[1].startswith("/") else parts[1]

            resp = requests.get(
                url=f"{self.host}/datasets/resolve/{dataset_id}/main{file_path}",
                headers=self.headers,
                cookies=self.cookies,
                allow_redirects=False,
                stream=True,
                timeout=30,
            )

            if resp.status_code not in [302, 307]:
                logger.error(f"获取文件信息失败: {resp.status_code}")
                return None

            return DriveFile(
                fid=fid,
                name=os.path.basename(file_path),
                size=int(resp.headers.get("content-length", 0)),
                ext={
                    "type": "file",
                    "dataset_id": dataset_id,
                    "path": file_path,
                    "download_url": resp.headers.get("Location", ""),
                },
            )

        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return None

    def get_dir_info(self, fid: str, *args, **kwargs) -> Optional[DriveFile]:
        """
        获取目录信息

        Args:
            fid: 目录路径

        Returns:
            目录信息
        """
        try:
            logger.info(f"正在获取目录信息: {fid}")

            # OpenXLab的目录信息比较简单
            return DriveFile(
                fid=fid,
                name=os.path.basename(fid) if fid != "root" else "root",
                size=0,
                ext={"type": "folder", "path": fid},
            )

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
        上传文件（OpenXLab不支持上传）

        Args:
            filepath: 本地文件路径
            fid: 目标目录ID
            filename: 上传后的文件名
            callback: 进度回调函数

        Returns:
            上传是否成功
        """
        logger.warning("OpenXLab是只读平台，不支持文件上传")
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
            fid: 文件ID（格式：dataset_id/file_path）
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

            # 解析文件ID
            if "/" not in fid:
                logger.error("文件ID格式错误，应为：dataset_id/file_path")
                return False

            parts = fid.split("/", 1)
            dataset_id = parts[0]
            file_path = "/" + parts[1] if not parts[1].startswith("/") else parts[1]

            # 获取文件信息和下载链接
            file_info_dict = self._get_raw_file_info(dataset_id, file_path)
            if not file_info_dict:
                logger.error("获取文件信息失败")
                return False

            # 确定保存路径
            if filepath:
                local_path = filepath
            elif save_dir and filename:
                local_path = os.path.join(save_dir, filename)
            elif save_dir:
                local_path = os.path.join(save_dir, os.path.basename(file_path))
            else:
                local_path = os.path.basename(file_path)

            # 检查文件是否已存在
            if os.path.exists(local_path):
                if not overwrite:
                    # 检查文件大小是否匹配
                    existing_size = os.path.getsize(local_path)
                    expected_size = int(file_info_dict.get("size", 0))
                    if existing_size == expected_size:
                        logger.info(f"文件已存在且大小匹配，跳过下载: {local_path}")
                        return True
                    else:
                        logger.warning(
                            f"文件已存在但大小不匹配，跳过下载: {local_path}"
                        )
                        return False

            # 确保目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # 使用funget下载文件
            success = simple_download(
                url=file_info_dict["url"], filepath=local_path, overwrite=True, **kwargs
            )

            if success:
                logger.info(f"✅ 文件下载成功: {local_path}")
                return True
            else:
                logger.error("❌ 文件下载失败")
                return False

        except Exception as e:
            logger.error(f"下载文件失败: {e}")
            return False

    def _get_raw_file_info(
        self, dataset_id: str, file_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取原始文件信息（内部方法）

        Args:
            dataset_id: 数据集ID
            file_path: 文件路径

        Returns:
            文件信息字典
        """
        try:
            resp = requests.get(
                url=f"{self.host}/datasets/resolve/{dataset_id}/main{file_path}",
                headers=self.headers,
                cookies=self.cookies,
                allow_redirects=False,
                stream=True,
                timeout=30,
            )

            if resp.status_code in [302, 307]:
                return {
                    "url": resp.headers["Location"],
                    "dataset_id": dataset_id,
                    "path": file_path.lstrip("/"),
                    "size": resp.headers.get("content-length", 0),
                }
            else:
                logger.error(f"获取文件信息失败: {resp.status_code}")
                return None

        except Exception as e:
            logger.error(f"获取原始文件信息失败: {e}")
            return None

    # 高级功能实现
    def search(self, keyword: str, fid: str = "root", **kwargs) -> List[DriveFile]:
        """
        搜索数据集

        Args:
            keyword: 搜索关键词
            fid: 搜索范围（数据集名称）

        Returns:
            搜索结果列表
        """
        try:
            logger.info(f"正在搜索数据集: {keyword}")

            # OpenXLab的搜索功能有限，这里实现简单的文件名匹配
            if fid == "root":
                logger.warning("请指定具体的数据集进行搜索")
                return []

            files = self.get_file_list(fid)
            results = []

            for file in files:
                if keyword.lower() in file.name.lower():
                    results.append(file)

            logger.info(f"搜索完成，找到 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
