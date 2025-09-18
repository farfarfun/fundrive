#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
清华云盘驱动实现

清华云盘是清华大学提供的云存储服务，支持文件分享和协作。
本驱动基于清华云盘分享链接API实现，支持公开分享文件的浏览和下载。

主要功能:
- 分享链接访问
- 文件下载
- 目录浏览
- 文件信息查询

作者: FunDrive Team
"""

import os
from typing import List, Optional, Any
from urllib.parse import quote

import requests
from funget import simple_download
from funsecret import read_secret
from funutil import getLogger

from fundrive.core import BaseDrive, DriveFile

logger = getLogger("fundrive")


class TSingHuaDrive(BaseDrive):
    """
    清华云盘驱动

    基于清华云盘分享链接API实现的云存储驱动，主要用于访问公开分享的文件和目录。
    支持通过分享链接访问文件，不需要登录认证。
    """

    def __init__(
        self, share_key: Optional[str] = None, password: Optional[str] = None, **kwargs
    ):
        """
        初始化清华云盘驱动

        Args:
            share_key: 分享链接的key
            password: 分享链接的密码（如果有）
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)

        self.base_url = "https://cloud.tsinghua.edu.cn"

        # 从配置或环境变量获取分享信息
        self.share_key = (
            share_key
            or read_secret("fundrive", "tsinghua", "share_key")
            or os.getenv("TSINGHUA_SHARE_KEY")
        )
        self.password = (
            password
            or read_secret("fundrive", "tsinghua", "password")
            or os.getenv("TSINGHUA_PASSWORD")
        )

        # 初始化会话
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "FunDrive Tsinghua Client/1.0"})

    def login(
        self, share_key: Optional[str] = None, password: Optional[str] = None, **kwargs
    ) -> bool:
        """
        登录清华云盘（设置分享链接信息）

        Args:
            share_key: 分享链接的key
            password: 分享链接的密码（如果有）

        Returns:
            登录是否成功
        """
        try:
            logger.info("正在设置清华云盘分享链接...")

            # 更新分享信息
            if share_key:
                self.share_key = share_key
            if password:
                self.password = password

            # 验证分享链接是否有效
            if self.share_key:
                try:
                    test_url = f"{self.base_url}/api/v2.1/share-links/{self.share_key}/dirents/?path="
                    response = self.session.get(test_url, timeout=10)
                    if response.status_code == 200:
                        logger.info("✅ 清华云盘分享链接验证成功")
                        return True
                    else:
                        logger.warning("⚠️ 分享链接可能无效，将尝试继续")
                        return True
                except Exception as e:
                    logger.warning("⚠️ 无法验证分享链接，将尝试继续", e)
                    return True
            else:
                logger.warning("⚠️ 未设置分享链接，某些功能可能无法使用")
                return True

        except Exception as e:
            logger.error(f"❌ 清华云盘登录失败: {e}")
            return False

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        检查文件或目录是否存在

        Args:
            fid: 路径（相对于分享根目录）

        Returns:
            文件或目录是否存在
        """
        try:
            # 检查路径是否存在
            url = f"{self.base_url}/api/v2.1/share-links/{self.share_key}/dirents/?path={quote(fid)}"
            response = self.session.get(url, timeout=10)
            return response.status_code == 200

        except Exception as e:
            logger.error(f"检查路径存在性失败: {e}")
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
        创建目录（清华云盘分享链接不支持创建目录）

        Args:
            fid: 父目录路径
            name: 目录名
            return_if_exist: 如果目录已存在，是否返回已存在目录的ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            创建的目录ID（此驱动不支持创建，返回空字符串）
        """
        logger.warning("清华云盘分享链接是只读的，不支持创建目录")
        return ""

    def delete(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        删除文件或目录（清华云盘分享链接不支持删除）

        Args:
            fid: 文件或目录路径

        Returns:
            删除是否成功
        """
        logger.warning("清华云盘分享链接是只读的，不支持删除操作")
        return False

    def get_file_list(self, fid: str = "", *args, **kwargs) -> List[DriveFile]:
        """
        获取文件列表

        Args:
            fid: 目录路径（相对于分享根目录）

        Returns:
            文件列表
        """
        try:
            logger.info(f"正在获取文件列表: {fid}")

            if not self.share_key:
                logger.error("未设置分享链接")
                return []

            url = f"{self.base_url}/api/v2.1/share-links/{self.share_key}/dirents/?path={quote(fid)}"

            response = self.session.get(url, timeout=30)

            if response.status_code != 200:
                logger.error(f"获取文件列表失败: {response.status_code}")
                return []

            result = response.json()
            objects = result.get("dirent_list", [])

            files = []
            for obj in objects:
                if not obj.get("is_dir", False):
                    drive_file = DriveFile(
                        fid=obj.get("file_path", ""),
                        name=obj.get("file_name", ""),
                        size=int(obj.get("size", 0)),
                        ext={
                            "type": "file",
                            "modified": obj.get("last_modified", ""),
                            "share_key": self.share_key,
                            "file_path": obj.get("file_path", ""),
                        },
                    )
                    files.append(drive_file)

            logger.info(f"✅ 获取到 {len(files)} 个文件")
            return files

        except Exception as e:
            logger.error(f"获取文件列表失败: {e}")
            return []

    def get_dir_list(self, fid: str = "", *args, **kwargs) -> List[DriveFile]:
        """
        获取目录列表

        Args:
            fid: 目录路径（相对于分享根目录）

        Returns:
            目录列表
        """
        try:
            logger.info(f"正在获取目录列表: {fid}")

            if not self.share_key:
                logger.error("未设置分享链接")
                return []

            url = f"{self.base_url}/api/v2.1/share-links/{self.share_key}/dirents/?path={quote(fid)}"

            response = self.session.get(url, timeout=30)

            if response.status_code != 200:
                logger.error(f"获取目录列表失败: {response.status_code}")
                return []

            result = response.json()
            objects = result.get("dirent_list", [])

            dirs = []
            for obj in objects:
                if obj.get("is_dir", False):
                    drive_file = DriveFile(
                        fid=obj.get("folder_path", ""),
                        name=obj.get("folder_name", ""),
                        size=0,
                        ext={
                            "type": "folder",
                            "modified": obj.get("last_modified", ""),
                            "share_key": self.share_key,
                            "folder_path": obj.get("folder_path", ""),
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
            fid: 文件路径

        Returns:
            文件信息
        """
        try:
            logger.info(f"正在获取文件信息: {fid}")

            # 通过获取父目录列表来查找文件信息
            parent_path = os.path.dirname(fid)
            filename = os.path.basename(fid)

            files = self.get_file_list(parent_path)
            for file in files:
                if file.name == filename:
                    return file

            logger.warning(f"未找到文件: {fid}")
            return None

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

            if fid == "" or fid == "/":
                # 根目录
                return DriveFile(
                    fid="",
                    name="root",
                    size=0,
                    ext={
                        "type": "folder",
                        "share_key": self.share_key,
                        "folder_path": "",
                    },
                )

            # 通过获取父目录列表来查找目录信息
            parent_path = os.path.dirname(fid)
            dirname = os.path.basename(fid)

            dirs = self.get_dir_list(parent_path)
            for dir in dirs:
                if dir.name == dirname:
                    return dir

            logger.warning(f"未找到目录: {fid}")
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
        上传文件（清华云盘分享链接不支持上传）

        Args:
            filepath: 本地文件路径
            fid: 目标目录路径
            filename: 上传后的文件名
            callback: 进度回调函数

        Returns:
            上传是否成功
        """
        logger.warning("清华云盘分享链接是只读的，不支持文件上传")
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
            fid: 文件路径
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

            if not self.share_key:
                logger.error("未设置分享链接")
                return False

            # 构建下载URL
            file_url = f"{self.base_url}/d/{self.share_key}/files/?p={quote(fid)}&dl=1"

            # 确定保存路径
            if filepath:
                local_path = filepath
            elif save_dir and filename:
                local_path = os.path.join(save_dir, filename)
            elif save_dir:
                local_path = os.path.join(save_dir, os.path.basename(fid))
            else:
                local_path = os.path.basename(fid)

            # 检查文件是否已存在
            if os.path.exists(local_path) and not overwrite:
                logger.warning(f"文件已存在，跳过下载: {local_path}")
                return False

            # 确保目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # 下载文件
            success = simple_download(url=file_url, filepath=local_path, **kwargs)

            if success:
                logger.info(f"✅ 文件下载成功: {local_path}")
                return True
            else:
                logger.error("❌ 文件下载失败")
                return False

        except Exception as e:
            logger.error(f"下载文件失败: {e}")
            return False

    # 高级功能实现
    def search(self, keyword: str, fid: str = "", **kwargs) -> List[DriveFile]:
        """
        搜索文件

        Args:
            keyword: 搜索关键词
            fid: 搜索范围（目录路径）

        Returns:
            搜索结果列表
        """
        try:
            logger.info(f"正在搜索文件: {keyword}")

            # 清华云盘的搜索功能有限，这里实现简单的文件名匹配
            files = self.get_file_list(fid)
            results = []

            for file in files:
                if keyword.lower() in file.name.lower():
                    results.append(file)

            # 递归搜索子目录
            dirs = self.get_dir_list(fid)
            for dir in dirs:
                try:
                    dir_path = dir.ext.get("folder_path", dir.fid)
                    sub_results = self.search(keyword, dir_path)
                    results.extend(sub_results)
                except Exception as e:
                    logger.error(f"搜索子目录失败 {dir.name}: {e}")

            logger.info(f"搜索完成，找到 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []


# 保持向后兼容的函数
def download(
    share_key,
    dir_path=".cache",
    path="/",
    is_dir=True,
    overwrite=False,
    *args,
    **kwargs,
):
    """
    下载清华云盘分享文件或目录（向后兼容函数）

    Args:
        share_key: 分享链接key
        dir_path: 下载目录
        path: 文件或目录路径
        is_dir: 是否为目录
        overwrite: 是否覆盖已存在文件
    """
    drive = TSingHuaDrive(share_key=share_key)
    drive.login()

    if is_dir:
        return drive.download_dir(
            fid=path,
            filedir=dir_path,
            overwrite=overwrite,
            *args,
            **kwargs,
        )
    else:
        return drive.download_file(
            fid=path,
            filedir=dir_path,
            overwrite=overwrite,
            *args,
            **kwargs,
        )
