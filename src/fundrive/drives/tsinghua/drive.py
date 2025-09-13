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
from typing import Any, Dict, List, Optional
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
                except:
                    logger.warning("⚠️ 无法验证分享链接，将尝试继续")
                    return True
            else:
                logger.warning("⚠️ 未设置分享链接，某些功能可能无法使用")
                return True

        except Exception as e:
            logger.error(f"❌ 清华云盘登录失败: {e}")
            return False

    def exist(self, fid: str, filename: str = None) -> bool:
        """
        检查文件或目录是否存在

        Args:
            fid: 路径（相对于分享根目录）
            filename: 文件名（可选）

        Returns:
            文件是否存在
        """
        try:
            if filename:
                # 检查特定文件是否存在
                files = self.get_file_list(fid)
                for file in files:
                    if file.name == filename:
                        return True

                # 检查是否为目录
                dirs = self.get_dir_list(fid)
                for dir in dirs:
                    if dir.name == filename:
                        return True

                return False
            else:
                # 检查路径是否存在
                try:
                    url = f"{self.base_url}/api/v2.1/share-links/{self.share_key}/dirents/?path={quote(fid)}"
                    response = self.session.get(url, timeout=10)
                    return response.status_code == 200
                except:
                    return False

        except Exception as e:
            logger.error(f"检查文件存在性失败: {e}")
            return False

    def mkdir(self, fid: str, dirname: str) -> bool:
        """
        创建目录（清华云盘分享链接不支持创建目录）

        Args:
            fid: 父目录路径
            dirname: 目录名

        Returns:
            创建是否成功
        """
        logger.warning("清华云盘分享链接是只读的，不支持创建目录")
        return False

    def delete(self, fid: str) -> bool:
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
        filedir: str = ".",
        filename: str = None,
        callback: callable = None,
        **kwargs,
    ) -> bool:
        """
        下载文件

        Args:
            fid: 文件路径
            filedir: 下载目录
            filename: 保存的文件名
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
            filename = filename or os.path.basename(fid)
            os.makedirs(filedir, exist_ok=True)
            filepath = os.path.join(filedir, filename)

            # 下载文件
            success = simple_download(url=file_url, filepath=filepath, **kwargs)

            if success:
                logger.info(f"✅ 文件下载成功: {filepath}")
                return True
            else:
                logger.error(f"❌ 文件下载失败")
                return False

        except Exception as e:
            logger.error(f"下载文件失败: {e}")
            return False

    def download_dir(
        self, fid: str, filedir: str = "./cache", overwrite: bool = False, **kwargs
    ) -> bool:
        """
        下载整个目录

        Args:
            fid: 目录路径
            filedir: 下载目录
            overwrite: 是否覆盖已存在的文件

        Returns:
            下载是否成功
        """
        try:
            logger.info(f"正在下载目录: {fid}")

            # 获取文件列表和子目录列表
            files = self.get_file_list(fid)
            dirs = self.get_dir_list(fid)

            success_count = 0
            total_count = len(files)

            # 下载所有文件
            for i, file in enumerate(files):
                try:
                    file_path = file.ext.get("file_path", file.fid)
                    relative_path = (
                        os.path.relpath(file_path, fid) if fid else file_path
                    )

                    success = self.download_file(
                        fid=file_path, filedir=filedir, filename=relative_path, **kwargs
                    )

                    if success:
                        success_count += 1

                    logger.info(
                        f"文件进度: {i + 1}/{total_count}, 成功: {success_count}"
                    )

                except Exception as e:
                    logger.error(f"下载文件失败 {file.name}: {e}")

            # 递归下载子目录
            for dir in dirs:
                try:
                    dir_path = dir.ext.get("folder_path", dir.fid)
                    relative_dir = os.path.relpath(dir_path, fid) if fid else dir_path
                    sub_dir = os.path.join(filedir, relative_dir)

                    self.download_dir(
                        fid=dir_path, filedir=sub_dir, overwrite=overwrite, **kwargs
                    )

                except Exception as e:
                    logger.error(f"下载目录失败 {dir.name}: {e}")

            logger.info(f"✅ 目录下载完成: {success_count}/{total_count} 个文件成功")
            return success_count > 0 or total_count == 0

        except Exception as e:
            logger.error(f"下载目录失败: {e}")
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
