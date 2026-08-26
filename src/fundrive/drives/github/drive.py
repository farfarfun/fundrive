#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub驱动实现

GitHub是全球最大的代码托管平台，本驱动将GitHub仓库作为云存储来操作，
支持文件的上传、下载、管理等功能。特别适合存储代码、文档、配置文件等。

主要功能:
- 仓库文件管理
- 文件上传下载
- 目录操作
- 版本控制
- 分支管理

作者: FunDrive Team
"""

# 标准库导入
import base64
import os
import time
from typing import Any, Dict, List, Optional

# 第三方库导入
import requests
from nltlog import getLogger
from funsecret import read_secret

# 项目内部导入
from fundrive.core import BaseDrive, DriveFile, ensure_parent_dir
from fundrive.core.http import new_session
from fundrive.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    FileNotFoundError,
    InsufficientStorageError,
    InvalidParameterError,
    NetworkError,
    UploadError,
)

logger = getLogger("fundrive")


class GitHubDrive(BaseDrive):
    """
    GitHub驱动

    基于GitHub REST API实现的代码仓库云存储驱动，将GitHub仓库作为云存储来操作。
    支持完整的文件管理功能和版本控制。
    """

    def __init__(
        self,
        access_token: Optional[str] = None,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
        branch: str = "main",
        **kwargs,
    ):
        """
        初始化GitHub驱动

        Args:
            access_token: GitHub访问令牌
            repo_owner: 仓库所有者
            repo_name: 仓库名称
            branch: 默认分支名称
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)

        # 从配置或环境变量获取认证信息
        self.access_token = (
            access_token
            or read_secret("fundrive", "github", "access_token")
            or os.getenv("GITHUB_ACCESS_TOKEN")
        )
        self.repo_owner = (
            repo_owner
            or read_secret("fundrive", "github", "repo_owner")
            or os.getenv("GITHUB_REPO_OWNER")
        )
        self.repo_name = (
            repo_name
            or read_secret("fundrive", "github", "repo_name")
            or os.getenv("GITHUB_REPO_NAME")
        )
        self.branch = branch

        # API配置
        self.base_url = "https://api.github.com"
        # 统一会话：默认超时 + 幂等请求自动重试 + 连接池复用
        self.session = new_session()
        self.headers = {}
        self.repo_str = None

    @staticmethod
    def _response_error_message(response: requests.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            payload = response.text.strip()

        if isinstance(payload, dict):
            message = payload.get("message") or payload.get("error")
            if message:
                return str(message)

        if isinstance(payload, str) and payload:
            return payload

        return f"HTTP {response.status_code}"

    def _raise_for_github_response(
        self, response: requests.Response, action: str
    ) -> requests.Response:
        if response.status_code in (200, 201):
            return response

        message = self._response_error_message(response)
        details = {
            "status_code": response.status_code,
            "action": action,
            "repo": self.repo_str,
            "branch": self.branch,
        }

        if response.status_code == 401:
            raise AuthenticationError(
                f"{action}失败: GitHub认证失败(401): {message}",
                details=details,
            )
        if response.status_code == 402:
            raise InsufficientStorageError(
                f"{action}失败: GitHub返回402: {message}",
                details=details,
            )
        if response.status_code == 403:
            raise AuthorizationError(
                f"{action}失败: GitHub权限不足(403): {message}",
                details=details,
            )
        if response.status_code == 404:
            raise FileNotFoundError(
                f"{action}失败: 仓库或路径不存在(404): {message}",
                details=details,
            )

        raise UploadError(
            f"{action}失败: GitHub API返回{response.status_code}: {message}",
            details=details,
        )

    @staticmethod
    def _is_conflict_response(response: requests.Response) -> bool:
        return response.status_code == 409

    def login(
        self,
        access_token: Optional[str] = None,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
        branch: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        登录GitHub

        Args:
            access_token: GitHub访问令牌
            repo_owner: 仓库所有者
            repo_name: 仓库名称
            branch: 分支名称

        Returns:
            登录是否成功
        """
        logger.info("正在连接GitHub...")

        if access_token:
            self.access_token = access_token
        if repo_owner:
            self.repo_owner = repo_owner
        if repo_name:
            self.repo_name = repo_name
        if branch:
            self.branch = branch

        if not self.access_token:
            raise InvalidParameterError("缺少GitHub访问令牌", parameter="access_token")

        if not self.repo_owner or not self.repo_name:
            raise InvalidParameterError(
                "缺少GitHub仓库信息",
                parameter="repo_owner/repo_name",
            )

        self.headers = {
            "Authorization": f"token {self.access_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "FunDrive-GitHub-Driver",
        }
        self.repo_str = f"{self.repo_owner}/{self.repo_name}"

        try:
            response = self.session.get(
                f"{self.base_url}/repos/{self.repo_str}", headers=self.headers
            )
        except requests.RequestException as exc:
            raise NetworkError(f"GitHub连接失败: {exc}") from exc

        repo_info = self._raise_for_github_response(response, "登录验证").json()
        logger.info(f"✅ 成功连接到GitHub仓库: {self.repo_str}")
        logger.info(f"   仓库描述: {repo_info.get('description', '无')}")
        logger.info(f"   默认分支: {repo_info.get('default_branch', 'main')}")
        return True

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        检查文件或目录是否存在

        通过GitHub API检查指定路径的文件或目录是否存在于仓库中。

        Args:
            fid: 文件或目录路径，相对于仓库根目录
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 文件或目录是否存在

        Raises:
            Exception: 当API调用失败时抛出异常
        """
        try:
            response = self.session.get(
                f"{self.base_url}/repos/{self.repo_str}/contents/{fid}",
                headers=self.headers,
                params={"ref": self.branch},
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
            }

            response = self.session.delete(
                f"{self.base_url}/repos/{self.repo_str}/contents/{fid}",
                headers=self.headers,
                json=data,
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

            response = self.session.get(
                f"{self.base_url}/repos/{self.repo_str}/contents/{fid}",
                headers=self.headers,
                params={"ref": self.branch},
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
                            "git_url": item["git_url"],
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

            response = self.session.get(
                f"{self.base_url}/repos/{self.repo_str}/contents/{fid}",
                headers=self.headers,
                params={"ref": self.branch},
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
                            "git_url": item["git_url"],
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

            response = self.session.get(
                f"{self.base_url}/repos/{self.repo_str}/contents/{fid}",
                headers=self.headers,
                params={"ref": self.branch},
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
                    "git_url": data["git_url"],
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

            response = self.session.get(
                f"{self.base_url}/repos/{self.repo_str}/contents/{fid}",
                headers=self.headers,
                params={"ref": self.branch},
            )

            if response.status_code != 200:
                logger.warning(f"目录不存在: {fid}")
                return None

            # GitHub API返回数组表示目录内容
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
        上传文件到GitHub

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
        logger.info(f"正在上传文件: {filepath or filename}")

        if filepath and os.path.exists(filepath):
            filename = filename or os.path.basename(filepath)
            with open(filepath, "rb") as f:
                file_content = f.read()
        elif content is not None:
            if not filename:
                raise InvalidParameterError("必须提供文件名", parameter="filename")
            file_content = (
                content.encode("utf-8") if isinstance(content, str) else content
            )
        else:
            raise InvalidParameterError(
                "必须提供文件路径或内容",
                parameter="filepath/content",
            )

        github_path = f"{fid.rstrip('/')}/{filename}" if fid else filename
        encoded_content = base64.b64encode(file_content).decode("utf-8")
        max_attempts = kwargs.get("max_retries", 3) + 1
        response = None

        for attempt in range(1, max_attempts + 1):
            existing_file = self.get_file_info(github_path)
            data = {
                "message": commit_message or f"Upload file: {filename}",
                "content": encoded_content,
                "branch": self.branch,
            }

            if existing_file:
                data["sha"] = existing_file.ext.get("sha")
                logger.info(f"更新已存在文件: {github_path}")
            else:
                logger.info(f"创建新文件: {github_path}")

            try:
                response = self.session.put(
                    f"{self.base_url}/repos/{self.repo_str}/contents/{github_path}",
                    headers=self.headers,
                    json=data,
                )
            except requests.RequestException as exc:
                raise NetworkError(f"上传文件失败: {exc}") from exc

            if not self._is_conflict_response(response):
                break

            if attempt == max_attempts:
                break

            logger.warning(
                f"上传文件发生冲突，准备重试({attempt}/{max_attempts - 1}): {github_path}"
            )
            time.sleep(min(0.2 * attempt, 1.0))

        self._raise_for_github_response(response, f"上传文件 {github_path}")
        logger.info(f"✅ 文件上传成功: {github_path}")
        if callback:
            callback(len(file_content), len(file_content))
        return True

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
        从GitHub下载文件

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
            ensure_parent_dir(local_path)

            # 下载文件
            download_url = file_info.ext.get("download_url")
            if download_url:
                response = self.session.get(download_url)
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
    def search(
        self,
        keyword: str,
        fid: str = "",
        file_type: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> List[DriveFile]:
        """
        搜索文件

        Args:
            keyword: 搜索关键词
            fid: 搜索范围（目录路径）

        Returns:
            搜索结果列表
        """
        if file_type is not None:
            # 契约里有这个参数，本驱动尚未实现按类型过滤。明确告警，
            # 而不是像以前那样被 **kwargs 静默吞掉。
            logger.warning(
                f"{type(self).__name__}.search 暂不支持 file_type 过滤，已忽略: {file_type!r}"
            )
        try:
            logger.info(f"正在搜索文件: {keyword}")

            # GitHub搜索API
            query = f"repo:{self.repo_str} filename:{keyword}"
            if fid:
                query += f" path:{fid}"

            response = self.session.get(
                f"{self.base_url}/search/code",
                headers=self.headers,
                params={"q": query},
            )

            results = []
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    drive_file = DriveFile(
                        fid=item["path"],
                        name=item["name"],
                        size=0,  # 搜索API不返回大小
                        ext={
                            "type": "file",
                            "sha": item["sha"],
                            "html_url": item["html_url"],
                            "repository": item["repository"]["full_name"],
                        },
                    )
                    results.append(drive_file)

            logger.info(f"搜索完成，找到 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    def get_quota(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        获取仓库信息（GitHub没有存储配额限制）

        Returns:
            仓库信息
        """
        try:
            response = self.session.get(
                f"{self.base_url}/repos/{self.repo_str}", headers=self.headers
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
                    "unlimited": True,  # GitHub仓库没有硬性大小限制
                }

            return {}

        except Exception as e:
            logger.error(f"获取仓库信息失败: {e}")
            return {}

    def share(
        self,
        *fids: str,
        password: str = "",
        expire_days: int = 0,
        description: str = "",
        **kwargs: Any,
    ) -> dict:
        """生成分享链接（BaseDrive 契约）。

        代码托管平台的仓库可见性决定链接可见性，因此 ``password`` 和
        ``expire_days`` 不被支持——传了会明确告警，而不是静默忽略。
        """
        if password or expire_days:
            logger.warning(
                "%s 的分享链接由仓库可见性决定，不支持 password/expire_days，已忽略",
                type(self).__name__,
            )
        links = [self.create_share_link(fid) for fid in fids]
        return {"links": links, "total": len(links), "description": description}

    def create_share_link(self, fid: str) -> str:
        """
        创建文件分享链接

        Args:
            fid: 文件路径

        Returns:
            分享链接URL
        """
        try:
            # GitHub文件的公开链接
            url = f"https://github.com/{self.repo_str}/blob/{self.branch}/{fid}"
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
        return f"https://raw.githubusercontent.com/{self.repo_str}/{self.branch}/{fid}"


# 向后兼容的别名
GithubDrive = GitHubDrive
