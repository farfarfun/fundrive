# 标准库导入
import os
import io
from typing import List, Optional, Any

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from funsecret import read_secret
from funutil import getLogger


from fundrive.core import BaseDrive, DriveFile

logger = getLogger("fundrive")


class GoogleDrive(BaseDrive):
    """
    Google Drive 网盘驱动实现

    基于 Google Drive API v3 实现的网盘驱动
    官方文档: https://developers.google.com/drive/api/v3/reference
    Python 客户端库: https://github.com/googleapis/google-api-python-client

    功能特点:
    - 支持文件和目录的基本操作
    - 支持大文件上传下载
    - 支持搜索和分享功能
    - 集成funsecret配置管理
    - 支持OAuth2认证流程
    """

    # Google Drive API 权限范围
    SCOPES = ["https://www.googleapis.com/auth/drive"]

    def __init__(
        self,
        credentials_file: Optional[str] = None,
        token_file: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """
        初始化Google Drive驱动

        Args:
            credentials_file: OAuth2 客户端凭据文件路径
            token_file: 访问令牌文件路径
            *args: 可变位置参数
            **kwargs: 可变关键字参数
        """
        super().__init__(*args, **kwargs)

        # 配置管理 - 优先使用传入参数，然后尝试从配置读取
        self.credentials_file = credentials_file or read_secret(
            "fundrive", "google_drive", "credentials_file"
        )
        self.token_file = (
            token_file
            or read_secret("fundrive", "google_drive", "token_file")
            or "token.json"
        )

        self.service = None
        self.creds = None

        if not self.credentials_file:
            logger.warning("未找到 Google Drive 凭据文件，请配置后使用")

    def login(self, *args, **kwargs) -> bool:
        """
        登录Google Drive服务

        Returns:
            bool: 登录是否成功
        """
        try:
            logger.info("开始Google Drive登录验证...")

            if not self.credentials_file:
                logger.error("缺少Google Drive凭据文件")
                return False

            # 检查是否存在有效的令牌文件
            if os.path.exists(self.token_file):
                self.creds = Credentials.from_authorized_user_file(
                    self.token_file, self.SCOPES
                )

            # 如果没有有效凭据，进行OAuth流程
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    # 刷新过期的令牌
                    self.creds.refresh(Request())
                else:
                    # 启动OAuth流程
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)

                # 保存凭据以供下次使用
                with open(self.token_file, "w") as token:
                    token.write(self.creds.to_json())

            # 构建Drive API服务
            self.service = build("drive", "v3", credentials=self.creds)

            # 测试API连接
            about = self.service.about().get(fields="user").execute()
            user_name = about.get("user", {}).get("displayName", "Unknown")

            self._is_logged_in = True
            self._root_fid = "root"  # Google Drive的根目录ID

            logger.info(f"Google Drive登录成功，用户: {user_name}")
            return True

        except Exception as e:
            logger.error(f"Google Drive登录失败: {e}")
            return False

    def exist(self, fid: str, *args, **kwargs) -> bool:
        """
        检查文件或目录是否存在

        Args:
            fid: 文件或目录ID

        Returns:
            bool: 是否存在
        """
        try:
            if not self.service:
                logger.error("未登录Google Drive服务")
                return False

            # 使用get方法检查文件是否存在
            self.service.files().get(fileId=fid, fields="id").execute()
            return True

        except HttpError as e:
            if e.resp.status == 404:
                return False
            logger.error(f"检查文件存在性失败: {e}")
            return False
        except Exception as e:
            logger.error(f"检查文件存在性失败: {e}")
            return False

    def mkdir(
        self, fid: str, name: str, return_if_exist: bool = True, *args, **kwargs
    ) -> str:
        """
        创建目录

        Args:
            fid: 父目录ID
            name: 目录名称
            return_if_exist: 如果目录已存在，是否返回已存在目录的ID

        Returns:
            str: 创建的目录ID
        """
        try:
            if not self.service:
                logger.error("未登录Google Drive服务")
                return ""

            # 检查目录是否已存在
            if return_if_exist:
                existing_dirs = self.get_dir_list(fid)
                for dir_info in existing_dirs:
                    if dir_info.name == name:
                        logger.info(f"目录已存在: {name}")
                        return dir_info.fid

            # 创建新目录
            file_metadata = {
                "name": name,
                "parents": [fid],
                "mimeType": "application/vnd.google-apps.folder",
            }

            file = (
                self.service.files().create(body=file_metadata, fields="id").execute()
            )
            logger.info(f"目录创建成功: {name}")
            return file.get("id")

        except Exception as e:
            logger.error(f"创建目录失败: {e}")
            return ""

    def delete(self, fid: str, *args, **kwargs) -> bool:
        """
        删除文件或目录

        Args:
            fid: 文件或目录ID

        Returns:
            bool: 删除是否成功
        """
        try:
            if not self.service:
                logger.error("未登录Google Drive服务")
                return False

            self.service.files().delete(fileId=fid).execute()
            logger.info(f"文件删除成功: {fid}")
            return True

        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False

    def get_file_list(self, fid: str, *args, **kwargs) -> List[DriveFile]:
        """
        获取目录下的文件列表

        Args:
            fid: 目录ID

        Returns:
            List[DriveFile]: 文件列表
        """
        try:
            if not self.service:
                logger.error("未登录Google Drive服务")
                return []

            # 查询指定目录下的文件（排除文件夹）
            query = f"'{fid}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false"
            results = (
                self.service.files()
                .list(q=query, fields="files(id, name, size, mimeType, modifiedTime)")
                .execute()
            )

            files = results.get("files", [])
            file_list = []

            for file in files:
                drive_file = DriveFile(
                    fid=file["id"],
                    name=file["name"],
                    size=int(file.get("size", 0)) if file.get("size") else 0,
                    ext={
                        "mimeType": file.get("mimeType"),
                        "modifiedTime": file.get("modifiedTime"),
                    },
                )
                file_list.append(drive_file)

            return file_list

        except Exception as e:
            logger.error(f"获取文件列表失败: {e}")
            return []

    def get_dir_list(self, fid: str, *args, **kwargs) -> List[DriveFile]:
        """
        获取目录下的子目录列表

        Args:
            fid: 目录ID

        Returns:
            List[DriveFile]: 子目录列表
        """
        try:
            if not self.service:
                logger.error("未登录Google Drive服务")
                return []

            # 查询指定目录下的文件夹
            query = f"'{fid}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = (
                self.service.files()
                .list(q=query, fields="files(id, name, mimeType, modifiedTime)")
                .execute()
            )

            dirs = results.get("files", [])
            dir_list = []

            for dir_info in dirs:
                drive_file = DriveFile(
                    fid=dir_info["id"],
                    name=dir_info["name"],
                    size=None,  # 目录没有大小
                    ext={
                        "mimeType": dir_info.get("mimeType"),
                        "modifiedTime": dir_info.get("modifiedTime"),
                    },
                )
                dir_list.append(drive_file)

            return dir_list

        except Exception as e:
            logger.error(f"获取目录列表失败: {e}")
            return []

    def get_file_info(self, fid: str, *args, **kwargs) -> Optional[DriveFile]:
        """
        获取文件详细信息

        Args:
            fid: 文件ID

        Returns:
            DriveFile: 文件信息对象
        """
        try:
            if not self.service:
                logger.error("未登录Google Drive服务")
                return None

            file = (
                self.service.files()
                .get(
                    fileId=fid, fields="id, name, size, mimeType, modifiedTime, parents"
                )
                .execute()
            )

            return DriveFile(
                fid=file["id"],
                name=file["name"],
                size=int(file.get("size", 0)) if file.get("size") else 0,
                ext={
                    "mimeType": file.get("mimeType"),
                    "modifiedTime": file.get("modifiedTime"),
                    "parents": file.get("parents", []),
                },
            )

        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return None

    def get_dir_info(self, fid: str, *args, **kwargs) -> DriveFile[Any] | None:
        """
        获取目录详细信息

        Args:
            fid: 目录ID

        Returns:
            DriveFile: 目录信息对象
        """
        try:
            if not self.service:
                logger.error("未登录Google Drive服务")
                return None

            dir_info = (
                self.service.files()
                .get(fileId=fid, fields="id, name, mimeType, modifiedTime, parents")
                .execute()
            )

            return DriveFile(
                fid=dir_info["id"],
                name=dir_info["name"],
                size=None,  # 目录没有大小
                ext={
                    "mimeType": dir_info.get("mimeType"),
                    "modifiedTime": dir_info.get("modifiedTime"),
                    "parents": dir_info.get("parents", []),
                },
            )

        except Exception as e:
            logger.error(f"获取目录信息失败: {e}")
            return None

    def upload_file(self, filedir: str, fid: str, *args, **kwargs) -> bool:
        """
        上传文件到Google Drive

        Args:
            filedir: 本地文件路径
            fid: 目标目录ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 上传是否成功
        """
        try:
            if not self.service:
                logger.error("未登录Google Drive服务")
                return False

            if not os.path.exists(filedir):
                logger.error(f"本地文件不存在: {filedir}")
                return False

            # 确定上传后的文件名
            filename = kwargs.get("filename") or os.path.basename(filedir)

            # 准备文件元数据
            file_metadata = {"name": filename, "parents": [fid]}

            # 创建媒体上传对象
            media = MediaFileUpload(filedir, resumable=True)

            # 执行上传
            request = self.service.files().create(
                body=file_metadata, media_body=media, fields="id"
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"上传进度: {progress}%")

            logger.info(f"文件上传成功: {filename}")
            return True

        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            return False

    def download_file(
        self,
        fid: str,
        filedir: Optional[str] = None,
        filename: Optional[str] = None,
        filepath: Optional[str] = None,
        overwrite: bool = False,
        *args,
        **kwargs,
    ) -> bool:
        """
        从Google Drive下载文件

        Args:
            fid: 文件ID
            filedir: 文件保存目录
            filename: 文件名
            filepath: 完整的文件保存路径
            overwrite: 是否覆盖已存在的文件

        Returns:
            bool: 下载是否成功
        """
        try:
            if not self.service:
                logger.error("未登录Google Drive服务")
                return False

            # 确定保存路径
            if filepath:
                save_path = filepath
            elif filedir and filename:
                save_path = os.path.join(filedir, filename)
            else:
                # 获取文件信息以确定文件名
                file_info = self.get_file_info(fid)
                if not file_info:
                    logger.error("无法获取文件信息")
                    return False
                save_path = os.path.join(filedir or ".", file_info.name)

            # 检查文件是否已存在
            if os.path.exists(save_path) and not overwrite:
                logger.warning(f"文件已存在，跳过下载: {save_path}")
                return False

            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # 执行下载
            request = self.service.files().get_media(fileId=fid)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"下载进度: {progress}%")

            # 保存文件
            with open(save_path, "wb") as f:
                f.write(fh.getvalue())

            logger.info(f"文件下载成功: {save_path}")
            return True

        except Exception as e:
            logger.error(f"文件下载失败: {e}")
            return False

    # 高级功能实现
    def search(
        self,
        keyword: str,
        fid: Optional[str] = None,
        file_type: Optional[str] = None,
        *args,
        **kwargs,
    ) -> List[DriveFile]:
        """
        搜索文件或目录

        Args:
            keyword: 搜索关键词
            fid: 搜索的起始目录ID，默认从根目录开始
            file_type: 文件类型筛选

        Returns:
            List[DriveFile]: 符合条件的文件列表
        """
        try:
            if not self.service:
                logger.error("未登录Google Drive服务")
                return []

            # 构建搜索查询
            query_parts = [f"name contains '{keyword}'", "trashed = false"]

            if fid and fid != "root":
                query_parts.append(f"'{fid}' in parents")

            if file_type:
                # 根据文件类型添加MIME类型过滤
                mime_type_map = {
                    "doc": "application/vnd.google-apps.document",
                    "sheet": "application/vnd.google-apps.spreadsheet",
                    "slide": "application/vnd.google-apps.presentation",
                    "pdf": "application/pdf",
                    "image": "image/",
                    "video": "video/",
                    "audio": "audio/",
                }
                if file_type in mime_type_map:
                    mime_type = mime_type_map[file_type]
                    if mime_type.endswith("/"):
                        query_parts.append(f"mimeType contains '{mime_type}'")
                    else:
                        query_parts.append(f"mimeType = '{mime_type}'")

            query = " and ".join(query_parts)

            # 执行搜索
            results = (
                self.service.files()
                .list(
                    q=query,
                    fields="files(id, name, size, mimeType, modifiedTime)",
                    pageSize=100,
                )
                .execute()
            )

            files = results.get("files", [])
            search_results = []

            for file in files:
                drive_file = DriveFile(
                    fid=file["id"],
                    name=file["name"],
                    size=int(file.get("size", 0)) if file.get("size") else 0,
                    ext={
                        "mimeType": file.get("mimeType"),
                        "modifiedTime": file.get("modifiedTime"),
                    },
                )
                search_results.append(drive_file)

            logger.info(f"搜索完成，找到 {len(search_results)} 个结果")
            return search_results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    def share(
        self,
        fid: str,
        password: str = "",
        expire_days: int = 0,
        description: str = "",
        *args,
        **kwargs,
    ) -> Optional[str]:
        """
        创建文件分享链接

        Args:
            fid: 要分享的文件或目录ID
            password: 分享密码（Google Drive不支持密码保护）
            expire_days: 分享链接有效期（Google Drive不支持过期时间）
            description: 分享描述

        Returns:
            str: 分享链接
        """
        try:
            if not self.service:
                logger.error("未登录Google Drive服务")
                return None

            # 设置文件权限为可查看
            permission = {"role": "reader", "type": "anyone"}

            self.service.permissions().create(fileId=fid, body=permission).execute()

            # 获取分享链接
            file = self.service.files().get(fileId=fid, fields="webViewLink").execute()

            share_link = file.get("webViewLink")

            if password:
                logger.warning("Google Drive不支持密码保护的分享链接")
            if expire_days > 0:
                logger.warning("Google Drive不支持设置分享链接过期时间")

            logger.info(f"分享链接创建成功: {share_link}")
            return share_link

        except Exception as e:
            logger.error(f"创建分享链接失败: {e}")
            return None

    def get_quota(self, *args, **kwargs) -> dict:
        """
        获取Google Drive存储配额信息

        Returns:
            dict: 包含总空间、已用空间等信息的字典
        """
        try:
            if not self.service:
                logger.error("未登录Google Drive服务")
                return {}

            about = self.service.about().get(fields="storageQuota").execute()

            storage_quota = about.get("storageQuota", {})

            total = int(storage_quota.get("limit", 0))
            used = int(storage_quota.get("usage", 0))
            available = total - used if total > 0 else 0

            quota_info = {
                "total": total,
                "used": used,
                "available": available,
                "usage_percentage": (used / total * 100) if total > 0 else 0,
            }

            logger.info(
                f"存储配额: 已用 {used / (1024**3):.2f}GB / 总计 {total / (1024**3):.2f}GB"
            )
            return quota_info

        except Exception as e:
            logger.error(f"获取存储配额失败: {e}")
            return {}

    def copy(
        self,
        source_fid: str,
        target_fid: str,
        new_name: Optional[str] = None,
        *args,
        **kwargs,
    ) -> bool:
        """
        复制文件或目录

        Args:
            source_fid: 源文件/目录ID
            target_fid: 目标目录ID
            new_name: 新文件名，如果不指定则使用原文件名

        Returns:
            bool: 复制是否成功
        """
        try:
            if not self.service:
                logger.error("未登录Google Drive服务")
                return False

            # 获取源文件信息
            source_file = (
                self.service.files()
                .get(fileId=source_fid, fields="name, mimeType")
                .execute()
            )

            # 准备复制的文件元数据
            copy_metadata = {
                "name": new_name or f"Copy of {source_file['name']}",
                "parents": [target_fid],
            }

            # 执行复制
            self.service.files().copy(fileId=source_fid, body=copy_metadata).execute()

            logger.info(f"文件复制成功: {copy_metadata['name']}")
            return True

        except Exception as e:
            logger.error(f"文件复制失败: {e}")
            return False

    def move(self, source_fid: str, target_fid: str, *args, **kwargs) -> bool:
        """
        移动文件或目录

        Args:
            source_fid: 源文件/目录ID
            target_fid: 目标目录ID

        Returns:
            bool: 移动是否成功
        """
        try:
            if not self.service:
                logger.error("未登录Google Drive服务")
                return False

            # 获取文件当前的父目录
            file = (
                self.service.files().get(fileId=source_fid, fields="parents").execute()
            )

            previous_parents = ",".join(file.get("parents"))

            # 移动文件
            file = (
                self.service.files()
                .update(
                    fileId=source_fid,
                    addParents=target_fid,
                    removeParents=previous_parents,
                    fields="id, parents",
                )
                .execute()
            )

            logger.info(f"文件移动成功: {source_fid}")
            return True

        except Exception as e:
            logger.error(f"文件移动失败: {e}")
            return False

    def rename(self, fid: str, new_name: str, *args, **kwargs) -> bool:
        """
        重命名文件或目录

        Args:
            fid: 文件/目录ID
            new_name: 新名称

        Returns:
            bool: 重命名是否成功
        """
        try:
            if not self.service:
                logger.error("未登录Google Drive服务")
                return False

            # 更新文件名
            file_metadata = {"name": new_name}

            self.service.files().update(
                fileId=fid, body=file_metadata, fields="name"
            ).execute()

            logger.info(f"文件重命名成功: {new_name}")
            return True

        except Exception as e:
            logger.error(f"文件重命名失败: {e}")
            return False

    # 不支持的功能实现
    def get_recycle_list(self, *args, **kwargs) -> List[DriveFile]:
        """获取回收站文件列表"""
        try:
            if not self.service:
                logger.warning("Google Drive 驱动不支持回收站功能（需要特殊权限）")
                return []

            # Google Drive API 需要特殊权限才能访问回收站
            results = (
                self.service.files()
                .list(
                    q="trashed = true",
                    fields="files(id, name, size, mimeType, modifiedTime)",
                )
                .execute()
            )

            files = results.get("files", [])
            recycle_list = []

            for file in files:
                drive_file = DriveFile(
                    fid=file["id"],
                    name=file["name"],
                    size=int(file.get("size", 0)) if file.get("size") else 0,
                    ext={
                        "mimeType": file.get("mimeType"),
                        "modifiedTime": file.get("modifiedTime"),
                        "trashed": True,
                    },
                )
                recycle_list.append(drive_file)

            return recycle_list

        except Exception as e:
            logger.warning(f"Google Drive 不支持回收站功能或权限不足: {e}")
            return []

    def restore(self, fid: str, *args, **kwargs) -> bool:
        """恢复文件 - Google Drive支持但需要特殊处理"""
        try:
            if not self.service:
                logger.warning("未登录Google Drive服务")
                return False

            # 从回收站恢复文件
            file_metadata = {"trashed": False}

            self.service.files().update(fileId=fid, body=file_metadata).execute()

            logger.info(f"文件恢复成功: {fid}")
            return True

        except Exception as e:
            logger.warning(f"Google Drive 文件恢复失败: {e}")
            return False

    def clear_recycle(self, *args, **kwargs) -> bool:
        """清空回收站 - Google Drive不支持批量清空"""
        logger.warning("Google Drive 不支持批量清空回收站功能")
        return False

    def save_shared(
        self, shared_url: str, fid: str, password: Optional[str] = None, *args, **kwargs
    ) -> bool:
        """保存分享文件 - Google Drive不支持此功能"""
        logger.warning("Google Drive 不支持保存分享文件功能")
        return False
