#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gitee驱动实现

Gitee是中国领先的代码托管平台，本驱动将Gitee仓库作为云存储来操作，
支持文件的上传、下载、管理等功能。特别适合国内用户使用。

主要功能:
- 仓库文件管理
- 文件上传下载
- 目录操作
- 版本控制
- 分支管理

作者: FunDrive Team
"""

import base64
import os
from typing import Any, Dict, List, Optional

import requests
from funsecret import read_secret
from funutil import getLogger

from fundrive.core import BaseDrive, DriveFile

logger = getLogger("fundrive")


class GiteeDrive(BaseDrive):
    """
    Gitee驱动

    基于Gitee OpenAPI实现的代码仓库云存储驱动，将Gitee仓库作为云存储来操作。
    支持完整的文件管理功能和版本控制。
    """

    def __init__(
        self,
        access_token: Optional[str] = None,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
        branch: str = "master",
        **kwargs,
    ):
        """
        初始化Gitee驱动

        Args:
            access_token: Gitee访问令牌
            repo_owner: 仓库所有者
            repo_name: 仓库名称
            branch: 默认分支名称
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)

        # 从配置或环境变量获取认证信息
        self.access_token = (
            access_token
            or read_secret("fundrive", "gitee", "access_token")
            or os.getenv("GITEE_ACCESS_TOKEN")
        )
        self.repo_owner = (
            repo_owner
            or read_secret("fundrive", "gitee", "repo_owner")
            or os.getenv("GITEE_REPO_OWNER")
        )
        self.repo_name = (
            repo_name
            or read_secret("fundrive", "gitee", "repo_name")
            or os.getenv("GITEE_REPO_NAME")
        )
        self.branch = branch

        # API配置
        self.base_url = "https://gitee.com/api/v5"
        self.repo_str = None

    def login(
        self,
        access_token: Optional[str] = None,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
        branch: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        登录Gitee

        Args:
            access_token: Gitee访问令牌
            repo_owner: 仓库所有者
            repo_name: 仓库名称
            branch: 分支名称

        Returns:
            登录是否成功
        """
        try:
            logger.info("正在连接Gitee...")

            # 更新认证信息
            if access_token:
                self.access_token = access_token
            if repo_owner:
                self.repo_owner = repo_owner
            if repo_name:
                self.repo_name = repo_name
            if branch:
                self.branch = branch

            # 检查必需的认证信息
            if not self.access_token:
                logger.error("缺少Gitee访问令牌")
                return False

            if not self.repo_owner or not self.repo_name:
                logger.error("缺少Gitee仓库信息")
                return False

            self.repo_str = f"{self.repo_owner}/{self.repo_name}"

            # 验证仓库访问权限
            params = {"access_token": self.access_token}
            response = requests.get(
                f"{self.base_url}/repos/{self.repo_str}", params=params
            )

            if response.status_code == 200:
                repo_info = response.json()
                logger.info(f"✅ 成功连接到Gitee仓库: {self.repo_str}")
                logger.info(f"   仓库描述: {repo_info.get('description', '无')}")
                logger.info(f"   默认分支: {repo_info.get('default_branch', 'master')}")
                return True
            elif response.status_code == 404:
                logger.error(f"仓库不存在或无访问权限: {self.repo_str}")
                return False
            else:
                logger.error(f"Gitee API错误: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Gitee连接失败: {e}")
            return False

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        检查文件或目录是否存在

        Args:
            fid: 文件或目录路径

        Returns:
            文件或目录是否存在
        """
        try:
            params = {"access_token": self.access_token, "ref": self.branch}
            response = requests.get(
                f"{self.base_url}/repos/{self.repo_str}/contents/{fid}", params=params
            )

            return response.status_code == 200

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
        创建目录（通过创建.gitkeep文件）

        Args:
            fid: 父目录路径
            name: 目录名
            return_if_exist: 如果目录已存在，是否返回已存在目录的ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            创建的目录ID（路径）
        """
        try:
            logger.info(f"正在创建目录: {fid}/{name}")

            # 构建目录路径
            dir_path = f"{fid.rstrip('/')}/{name}" if fid else name

            # 检查目录是否已存在
            if return_if_exist and self.exist(dir_path):
                logger.info(f"目录已存在: {dir_path}")
                return dir_path

            # 创建.gitkeep文件来表示目录
            success = self.upload_file(
                filepath=None,
                fid=dir_path,
                filename=".gitkeep",
                content="# This file keeps the directory in git\n",
                commit_message=f"Create directory: {dir_path}",
            )

            if success:
                logger.info(f"✅ 目录创建成功: {dir_path}")
                return dir_path
            else:
                return ""

        except Exception as e:
            logger.error(f"创建目录失败: {e}")
            return ""

    def delete(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        删除文件

        Args:
            fid: 文件路径

        Returns:
            删除是否成功
        """
        try:
            logger.info(f"正在删除文件: {fid}")

            # 获取文件信息以获取SHA
            file_info = self.get_file_info(fid)
            if not file_info:
                logger.warning(f"文件不存在: {fid}")
                return False

            # 删除文件
            data = {
                "message": f"Delete file: {fid}",
                "sha": file_info.ext.get("sha"),
                "branch": self.branch,
                "access_token": self.access_token,
            }

            response = requests.delete(
                f"{self.base_url}/repos/{self.repo_str}/contents/{fid}", json=data
            )

            if response.status_code in (200, 204):
                logger.info(f"✅ 文件删除成功: {fid}")
                return True
            else:
                logger.error(f"删除文件失败: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False

    def get_file_list(self, fid: str = "", *args, **kwargs) -> List[DriveFile]:
        """
        获取文件列表

        Args:
            fid: 目录路径

        Returns:
            文件列表
        """
        try:
            logger.info(f"正在获取文件列表: {fid}")

            params = {"access_token": self.access_token, "ref": self.branch}
            response = requests.get(
                f"{self.base_url}/repos/{self.repo_str}/contents/{fid}", params=params
            )

            if response.status_code != 200:
                logger.error(f"获取文件列表失败: {response.status_code}")
                return []

            files = []
            for item in response.json():
                if item["type"] == "file":
                    drive_file = DriveFile(
                        fid=item["path"],
                        name=item["name"],
                        size=item["size"],
                        ext={
                            "type": "file",
                            "sha": item["sha"],
                            "download_url": item["download_url"],
                            "html_url": item["html_url"],
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
            fid: 目录路径

        Returns:
            目录列表
        """
        try:
            logger.info(f"正在获取目录列表: {fid}")

            params = {"access_token": self.access_token, "ref": self.branch}
            response = requests.get(
                f"{self.base_url}/repos/{self.repo_str}/contents/{fid}", params=params
            )

            if response.status_code != 200:
                logger.error(f"获取目录列表失败: {response.status_code}")
                return []

            dirs = []
            for item in response.json():
                if item["type"] == "dir":
                    drive_file = DriveFile(
                        fid=item["path"],
                        name=item["name"],
                        size=0,
                        ext={
                            "type": "folder",
                            "sha": item["sha"],
                            "html_url": item["html_url"],
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

            params = {"access_token": self.access_token, "ref": self.branch}
            response = requests.get(
                f"{self.base_url}/repos/{self.repo_str}/contents/{fid}", params=params
            )

            if response.status_code != 200:
                logger.warning(f"文件不存在: {fid}")
                return None

            data = response.json()
            if data["type"] != "file":
                logger.warning(f"路径不是文件: {fid}")
                return None

            drive_file = DriveFile(
                fid=data["path"],
                name=data["name"],
                size=data["size"],
                ext={
                    "type": "file",
                    "sha": data["sha"],
                    "download_url": data["download_url"],
                    "html_url": data["html_url"],
                    "encoding": data.get("encoding", "base64"),
                },
            )

            return drive_file

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
                return DriveFile(fid="", name="root", size=0, ext={"type": "folder"})

            params = {"access_token": self.access_token, "ref": self.branch}
            response = requests.get(
                f"{self.base_url}/repos/{self.repo_str}/contents/{fid}", params=params
            )

            if response.status_code != 200:
                logger.warning(f"目录不存在: {fid}")
                return None

            # Gitee API返回数组表示目录内容
            if isinstance(response.json(), list):
                return DriveFile(
                    fid=fid, name=os.path.basename(fid), size=0, ext={"type": "folder"}
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
        content: str = None,
        commit_message: str = None,
        callback: callable = None,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        上传文件到Gitee

        Args:
            filepath: 本地文件路径
            fid: 目标目录路径
            filename: 上传后的文件名
            content: 文件内容（如果不提供filepath）
            commit_message: 提交信息
            callback: 进度回调函数

        Returns:
            上传是否成功
        """
        try:
            logger.info(f"正在上传文件: {filepath or filename}")

            # 确定文件名和路径
            if filepath and os.path.exists(filepath):
                filename = filename or os.path.basename(filepath)
                with open(filepath, "rb") as f:
                    file_content = f.read()
            elif content:
                if not filename:
                    logger.error("必须提供文件名")
                    return False
                file_content = (
                    content.encode("utf-8") if isinstance(content, str) else content
                )
            else:
                logger.error("必须提供文件路径或内容")
                return False

            # 构建Gitee路径
            gitee_path = f"{fid.rstrip('/')}/{filename}" if fid else filename

            # 检查文件是否已存在
            existing_file = self.get_file_info(gitee_path)

            # 准备上传数据
            data = {
                "message": commit_message or f"Upload file: {filename}",
                "content": base64.b64encode(file_content).decode("utf-8"),
                "branch": self.branch,
                "access_token": self.access_token,
            }

            # 根据文件是否存在选择POST或PUT
            if existing_file:
                data["sha"] = existing_file.ext.get("sha")
                logger.info(f"更新已存在文件: {gitee_path}")
                response = requests.put(
                    f"{self.base_url}/repos/{self.repo_str}/contents/{gitee_path}",
                    json=data,
                )
            else:
                logger.info(f"创建新文件: {gitee_path}")
                response = requests.post(
                    f"{self.base_url}/repos/{self.repo_str}/contents/{gitee_path}",
                    json=data,
                )

            if response.status_code in (200, 201):
                logger.info(f"✅ 文件上传成功: {gitee_path}")
                if callback:
                    callback(len(file_content), len(file_content))
                return True
            else:
                logger.error(f"上传文件失败: {response.status_code} - {response.text}")
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
        从Gitee下载文件

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

            # 获取文件信息
            file_info = self.get_file_info(fid)
            if not file_info:
                logger.error(f"文件不存在: {fid}")
                return False

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
            download_url = file_info.ext.get("download_url")
            if download_url:
                response = requests.get(download_url)
                if response.status_code == 200:
                    with open(local_path, "wb") as f:
                        f.write(response.content)

                    logger.info(f"✅ 文件下载成功: {local_path}")
                    if callback:
                        callback(len(response.content), len(response.content))
                    return True

            logger.error("下载文件失败: 无法获取下载链接")
            return False

        except Exception as e:
            logger.error(f"下载文件失败: {e}")
            return False

    # 高级功能实现
    def search(self, keyword: str, fid: str = "", **kwargs) -> List[DriveFile]:
        """
        搜索文件（基于文件名匹配）

        Args:
            keyword: 搜索关键词
            fid: 搜索范围（目录路径）

        Returns:
            搜索结果列表
        """
        try:
            logger.info(f"正在搜索文件: {keyword}")

            results = []

            # 递归搜索函数
            def search_recursive(path: str):
                files = self.get_file_list(path)
                dirs = self.get_dir_list(path)

                # 搜索文件
                for file in files:
                    if keyword.lower() in file.name.lower():
                        results.append(file)

                # 递归搜索子目录
                for dir_item in dirs:
                    search_recursive(dir_item.fid)

            search_recursive(fid)

            logger.info(f"搜索完成，找到 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    def get_quota(self) -> Dict[str, Any]:
        """
        获取仓库信息

        Returns:
            仓库信息
        """
        try:
            params = {"access_token": self.access_token}
            response = requests.get(
                f"{self.base_url}/repos/{self.repo_str}", params=params
            )

            if response.status_code == 200:
                repo_data = response.json()
                return {
                    "repo_name": repo_data["full_name"],
                    "description": repo_data.get("description", ""),
                    "size": repo_data["size"],  # KB
                    "size_mb": round(repo_data["size"] / 1024, 2),
                    "default_branch": repo_data["default_branch"],
                    "language": repo_data.get("language", ""),
                    "stars": repo_data["stargazers_count"],
                    "forks": repo_data["forks_count"],
                    "open_issues": repo_data["open_issues_count"],
                    "created_at": repo_data["created_at"],
                    "updated_at": repo_data["updated_at"],
                    "unlimited": True,  # Gitee仓库没有硬性大小限制
                }

            return {}

        except Exception as e:
            logger.error(f"获取仓库信息失败: {e}")
            return {}

    def create_share_link(self, fid: str) -> str:
        """
        创建文件分享链接

        Args:
            fid: 文件路径

        Returns:
            分享链接URL
        """
        try:
            # Gitee文件的公开链接
            url = f"https://gitee.com/{self.repo_str}/blob/{self.branch}/{fid}"
            logger.info(f"生成分享链接: {fid}")
            return url

        except Exception as e:
            logger.error(f"生成分享链接失败: {e}")
            return ""

    def get_raw_url(self, fid: str) -> str:
        """
        获取文件原始内容链接

        Args:
            fid: 文件路径

        Returns:
            原始内容链接
        """
        return f"https://gitee.com/{self.repo_str}/raw/{self.branch}/{fid}"
