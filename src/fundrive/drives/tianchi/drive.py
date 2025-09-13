#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
天池云存储驱动实现

天池是阿里云推出的数据科学竞赛平台，提供数据集存储和AI竞赛服务。
本驱动基于天池API实现，支持数据集的浏览、下载等操作。

主要功能:
- 数据集浏览
- 文件下载
- 目录操作
- 文件信息查询

作者: FunDrive Team
"""

import os
from typing import Any, Dict, List, Optional

import orjson
import requests
from funget import simple_download
from funsecret import read_secret
from funutil import getLogger

from fundrive.core import BaseDrive, DriveFile

logger = getLogger("fundrive")


class TianChiDrive(BaseDrive):
    """
    天池云存储驱动

    基于天池API实现的云存储驱动，主要用于访问和下载竞赛数据集。
    支持Cookie和CSRF Token认证。
    """

    def __init__(
        self,
        tc_cookie: Optional[str] = None,
        csrf_cookie: Optional[str] = None,
        csrf_token: Optional[str] = None,
        **kwargs,
    ):
        """
        初始化天池驱动

        Args:
            tc_cookie: 天池TC Cookie
            csrf_cookie: CSRF Cookie
            csrf_token: CSRF Token
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)

        self.base_url = "https://tianchi.aliyun.com"
        self.cookies = {}
        self.headers = {"content-type": "application/json"}

        # 从配置或环境变量获取认证信息
        self.tc_cookie = (
            tc_cookie
            or read_secret("fundrive", "tianchi", "cookies", "tc")
            or os.getenv("TIANCHI_TC_COOKIE")
        )
        self.csrf_cookie = (
            csrf_cookie
            or read_secret("fundrive", "tianchi", "cookies", "_csrf")
            or os.getenv("TIANCHI_CSRF_COOKIE")
        )
        self.csrf_token = (
            csrf_token
            or read_secret("fundrive", "tianchi", "headers", "csrf-token")
            or os.getenv("TIANCHI_CSRF_TOKEN")
        )

    def login(
        self,
        tc_cookie: Optional[str] = None,
        csrf_cookie: Optional[str] = None,
        csrf_token: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        登录天池平台

        Args:
            tc_cookie: 天池TC Cookie
            csrf_cookie: CSRF Cookie
            csrf_token: CSRF Token

        Returns:
            登录是否成功
        """
        try:
            logger.info("正在登录天池平台...")

            # 更新认证信息
            if tc_cookie:
                self.tc_cookie = tc_cookie
            if csrf_cookie:
                self.csrf_cookie = csrf_cookie
            if csrf_token:
                self.csrf_token = csrf_token

            # 设置Cookie和Headers
            self.cookies.update(
                {
                    "tc": self.tc_cookie,
                    "_csrf": self.csrf_cookie,
                }
            )

            self.headers.update(
                {
                    "csrf-token": self.csrf_token,
                }
            )

            # 验证登录状态（尝试访问API）
            try:
                test_response = requests.get(
                    f"{self.base_url}/api/dataset/list",
                    cookies=self.cookies,
                    headers=self.headers,
                    timeout=10,
                )
                if test_response.status_code == 200:
                    logger.info("✅ 天池登录成功")
                    return True
                else:
                    logger.warning("⚠️ 天池登录状态未知，将尝试继续")
                    return True
            except:
                logger.warning("⚠️ 无法验证天池登录状态，将尝试继续")
                return True

        except Exception as e:
            logger.error(f"❌ 天池登录失败: {e}")
            return False

    def exist(self, fid: str, filename: str = None) -> bool:
        """
        检查数据集或文件是否存在

        Args:
            fid: 数据集ID
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
                return False
            else:
                # 检查数据集是否存在
                try:
                    data = orjson.dumps({"dataId": int(fid)}).decode("utf-8")
                    response = requests.post(
                        url=f"{self.base_url}/api/notebook/dataDetail",
                        cookies=self.cookies,
                        headers=self.headers,
                        data=data,
                        timeout=10,
                    )
                    return response.status_code == 200 and response.json().get(
                        "success", False
                    )
                except:
                    return False

        except Exception as e:
            logger.error(f"检查文件存在性失败: {e}")
            return False

    def mkdir(self, fid: str, dirname: str) -> bool:
        """
        创建目录（天池不支持创建目录）

        Args:
            fid: 父目录ID
            dirname: 目录名

        Returns:
            创建是否成功
        """
        logger.warning("天池是只读平台，不支持创建目录")
        return False

    def delete(self, fid: str) -> bool:
        """
        删除文件或目录（天池不支持删除）

        Args:
            fid: 文件或目录ID

        Returns:
            删除是否成功
        """
        logger.warning("天池是只读平台，不支持删除操作")
        return False

    def get_file_list(self, fid: str = "root", *args, **kwargs) -> List[DriveFile]:
        """
        获取数据集文件列表

        Args:
            fid: 数据集ID

        Returns:
            文件列表
        """
        try:
            logger.info(f"正在获取数据集文件列表: {fid}")

            if fid == "root":
                logger.warning("请指定具体的数据集ID")
                return []

            data = orjson.dumps({"dataId": int(fid)}).decode("utf-8")

            response = requests.post(
                url=f"{self.base_url}/api/notebook/dataDetail",
                cookies=self.cookies,
                headers=self.headers,
                data=data,
                timeout=30,
            )

            if response.status_code != 200:
                logger.error(f"获取数据集信息失败: {response.status_code}")
                return []

            result = response.json()
            if not result.get("success", False):
                logger.error("获取数据集信息失败")
                return []

            file_list = result.get("data", {}).get("datalabFile", [])

            files = []
            for item in file_list:
                drive_file = DriveFile(
                    fid=str(item.get("id", "")),
                    name=os.path.basename(item.get("filePath", "")),
                    size=int(item.get("size", 0)),
                    ext={
                        "type": "file",
                        "dataset_id": fid,
                        "file_path": item.get("filePath", ""),
                        "file_id": item.get("id", ""),
                        "modified": item.get("updateTime", ""),
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
            fid: 数据集ID

        Returns:
            目录列表
        """
        try:
            logger.info(f"正在获取数据集目录列表: {fid}")

            if fid == "root":
                logger.warning("请指定具体的数据集ID")
                return []

            # 获取文件列表并提取目录信息
            files = self.get_file_list(fid)

            # 提取目录信息
            dirs = []
            dir_paths = set()

            for file in files:
                file_path = file.ext.get("file_path", "")
                # 提取目录路径
                dir_path = os.path.dirname(file_path)
                if dir_path and dir_path not in dir_paths:
                    dir_paths.add(dir_path)

                    drive_file = DriveFile(
                        fid=dir_path,
                        name=os.path.basename(dir_path),
                        size=0,
                        ext={"type": "folder", "dataset_id": fid, "path": dir_path},
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

            # 通过下载URL API获取文件信息
            response = requests.get(
                url=f"{self.base_url}/api/dataset/getFileDownloadUrl?fileId={fid}",
                cookies=self.cookies,
                timeout=30,
            )

            if response.status_code != 200:
                logger.error(f"获取文件信息失败: {response.status_code}")
                return None

            result = response.json()
            if not result.get("success", False):
                logger.error("获取文件信息失败")
                return None

            # 天池API返回的信息有限，构建基本的文件信息
            return DriveFile(
                fid=fid,
                name=f"file_{fid}",  # 天池API可能不返回文件名
                size=0,  # 天池API可能不返回文件大小
                ext={
                    "type": "file",
                    "file_id": fid,
                    "download_url": result.get("data", ""),
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

            # 天池的目录信息比较简单
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
        上传文件（天池不支持上传）

        Args:
            filepath: 本地文件路径
            fid: 目标目录ID
            filename: 上传后的文件名
            callback: 进度回调函数

        Returns:
            上传是否成功
        """
        logger.warning("天池是只读平台，不支持文件上传")
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
            fid: 文件ID
            filedir: 下载目录
            filename: 保存的文件名
            callback: 进度回调函数

        Returns:
            下载是否成功
        """
        try:
            logger.info(f"正在下载文件: {fid}")

            # 获取下载URL
            download_url = self._get_dataset_url(fid)
            if not download_url:
                logger.error("获取下载链接失败")
                return False

            # 确定保存路径
            filename = filename or f"tianchi_file_{fid}"
            os.makedirs(filedir, exist_ok=True)
            filepath = os.path.join(filedir, filename)

            # 下载文件
            success = simple_download(url=download_url, filepath=filepath, **kwargs)

            if success:
                logger.info(f"✅ 文件下载成功: {filepath}")
                return True
            else:
                logger.error(f"❌ 文件下载失败")
                return False

        except Exception as e:
            logger.error(f"下载文件失败: {e}")
            return False

    def _get_dataset_url(self, fid: str) -> Optional[str]:
        """
        获取文件下载URL（内部方法）

        Args:
            fid: 文件ID

        Returns:
            下载URL
        """
        try:
            response = requests.get(
                url=f"{self.base_url}/api/dataset/getFileDownloadUrl?fileId={fid}",
                cookies=self.cookies,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success", False):
                    return result.get("data", "")

            logger.error(f"获取下载URL失败: {response.status_code}")
            return None

        except Exception as e:
            logger.error(f"获取下载URL异常: {e}")
            return None

    def download_dir(
        self, fid: str, filedir: str = "./cache", overwrite: bool = False, **kwargs
    ) -> bool:
        """
        下载整个数据集

        Args:
            fid: 数据集ID
            filedir: 下载目录
            overwrite: 是否覆盖已存在的文件

        Returns:
            下载是否成功
        """
        try:
            logger.info(f"正在下载数据集: {fid}")

            if fid == "root":
                logger.error("请指定具体的数据集ID")
                return False

            # 获取文件列表
            files = self.get_file_list(fid)
            if not files:
                logger.warning("数据集中没有文件")
                return True

            success_count = 0
            total_count = len(files)

            for i, file in enumerate(files):
                try:
                    file_id = file.ext.get("file_id", file.fid)
                    file_path = file.ext.get("file_path", file.name)

                    # 下载文件
                    success = self.download_file(
                        fid=file_id, filedir=filedir, filename=file_path, **kwargs
                    )

                    if success:
                        success_count += 1

                    logger.info(f"进度: {i + 1}/{total_count}, 成功: {success_count}")

                except Exception as e:
                    logger.error(f"下载文件失败 {file.name}: {e}")

            logger.info(f"✅ 数据集下载完成: {success_count}/{total_count} 个文件成功")
            return success_count > 0

        except Exception as e:
            logger.error(f"下载数据集失败: {e}")
            return False

    # 高级功能实现
    def search(self, keyword: str, fid: str = "root", **kwargs) -> List[DriveFile]:
        """
        搜索数据集

        Args:
            keyword: 搜索关键词
            fid: 搜索范围（数据集ID）

        Returns:
            搜索结果列表
        """
        try:
            logger.info(f"正在搜索数据集: {keyword}")

            # 天池的搜索功能有限，这里实现简单的文件名匹配
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
