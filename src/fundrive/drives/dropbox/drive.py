# 标准库
import os
from typing import List, Any, Optional


import dropbox
from dropbox.exceptions import ApiError, AuthError
from funsecret import read_secret
from funutil import getLogger
from tqdm import tqdm

# 项目内部
from fundrive.core import BaseDrive, DriveFile
from fundrive.core.base import get_filepath


class DropboxDrive(BaseDrive):
    """
    Dropbox 网盘驱动实现

    基于 Dropbox API v2 实现的网盘驱动
    官方文档: https://dropbox.github.io/dropbox-api-v2-explorer/
    Python SDK: https://dropbox-sdk-python.readthedocs.io/

    功能特点:
    - 支持文件和目录的基本操作
    - 支持大文件上传下载进度显示
    - 支持批量操作和递归处理
    - 集成funsecret配置管理
    - 支持分享链接和协作功能
    """

    def __init__(self, *args, **kwargs):
        """
        初始化Dropbox驱动

        Args:
            *args: 可变位置参数
            **kwargs: 可变关键字参数
        """
        super(DropboxDrive, self).__init__(*args, **kwargs)
        self.client: dropbox.Dropbox = None
        self.logger = getLogger("dropbox_drive")
        self._account_info = None

    def login(
        self,
        access_token: Optional[str] = None,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        *args,
        **kwargs,
    ) -> bool:
        """
        登录Dropbox服务

        Args:
            access_token (str, optional): 访问令牌
            app_key (str, optional): 应用密钥
            app_secret (str, optional): 应用密码
        Returns:
            bool: 登录是否成功
        """

        try:
            # 读取配置信息
            access_token = access_token or read_secret(
                "fundrive",
                "dropbox",
                "access_token",
            )

            if not access_token:
                self.logger.error("Dropbox访问令牌未配置，请设置access_token")
                return False

            # 创建Dropbox客户端
            self.client = dropbox.Dropbox(access_token)

            # 测试连接并获取账户信息
            self._account_info = self.client.users_get_current_account()
            self._is_logged_in = True
            self._root_fid = ""

            self.logger.info(
                f"Dropbox登录成功，用户: {self._account_info.name.display_name}"
            )
            return True

        except AuthError as e:
            self.logger.error(f"Dropbox认证失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Dropbox登录失败: {e}")
            return False

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        检查文件或目录是否存在

        Args:
            fid: 文件或目录ID（Dropbox中为路径）
        Returns:
            bool: 是否存在
        """
        try:
            if not self.client:
                self.logger.error("未登录Dropbox服务")
                return False

            # 确保路径格式正确
            path = self._normalize_path(fid)

            # 尝试获取文件/目录元数据
            self.client.files_get_metadata(path)
            return True

        except ApiError as e:
            # 文件不存在时返回 False
            if hasattr(e.error, "is_path") and e.error.is_path():
                path_error = e.error.get_path()
                if hasattr(path_error, "is_not_found") and path_error.is_not_found():
                    return False
            self.logger.error(f"检查文件存在失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"检查文件存在失败: {e}")
            return False

    def _normalize_path(self, path: str) -> str:
        """
        规范化路径格式

        Args:
            path: 原始路径
        Returns:
            str: 规范化后的路径
        """
        if not path or path == "/":
            return ""

        # 确保路径以/开头但不以/结尾（除非是根目录）
        path = path.replace("\\", "/")
        if not path.startswith("/"):
            path = "/" + path
        if path.endswith("/") and path != "/":
            path = path.rstrip("/")

        return path if path != "/" else ""

    def mkdir(
        self, fid: str, name: str, return_if_exist: bool = True, *args, **kwargs
    ) -> str:
        """
        创建目录

        Args:
            fid: 父目录ID
            name: 目录名
            return_if_exist: 如果目录存在是否返回
        Returns:
            str: 创建的目录路径
        """
        try:
            if not self.client:
                self.logger.error("未登录Dropbox服务")
                return ""

            # 构建目录路径
            parent_path = self._normalize_path(fid)
            dir_path = os.path.join(parent_path, name).replace("\\", "/")
            dir_path = self._normalize_path(dir_path)

            # 检查目录是否已存在
            if return_if_exist and self.exist(dir_path):
                self.logger.info(f"目录已存在: {dir_path}")
                return dir_path

            # 创建目录
            self.client.files_create_folder_v2(dir_path)

            self.logger.info(f"创建目录成功: {dir_path}")
            return dir_path

        except ApiError as e:
            # 处理目录已存在的情况
            if hasattr(e.error, "is_path") and e.error.is_path():
                path_error = e.error.get_path()
                if hasattr(path_error, "is_conflict") and path_error.is_conflict():
                    if return_if_exist:
                        self.logger.info(f"目录已存在: {dir_path}")
                        return dir_path
            self.logger.error(f"创建目录失败: {e}")
            return ""
        except Exception as e:
            self.logger.error(f"创建目录失败: {e}")
            return ""

    def delete(self, fid: str, *args, **kwargs) -> bool:
        """
        删除文件或目录

        Args:
            fid: 文件或目录ID
        Returns:
            bool: 是否删除成功
        """
        try:
            if not self.client:
                self.logger.error("未登录Dropbox服务")
                return False

            path = self._normalize_path(fid)

            if not self.exist(path):
                self.logger.warning(f"文件或目录不存在: {path}")
                return True

            # 删除文件或目录
            self.client.files_delete_v2(path)

            self.logger.info(f"删除成功: {path}")
            return True

        except Exception as e:
            self.logger.error(f"删除失败: {e}")
            return False

    def get_file_info(self, fid: str, *args, **kwargs) -> Optional[DriveFile]:
        """
        获取文件信息

        Args:
            fid: 文件ID
        Returns:
            DriveFile: 文件信息对象
        """
        try:
            if not self.client:
                self.logger.error("未登录Dropbox服务")
                return None

            path = self._normalize_path(fid)

            # 获取文件元数据
            metadata = self.client.files_get_metadata(path)

            # 检查是否为文件
            if isinstance(metadata, dropbox.files.FileMetadata):
                return DriveFile(
                    fid=metadata.path_display,
                    name=metadata.name,
                    isfile=True,
                    path=metadata.path_display,
                    size=metadata.size,
                    last_modified=metadata.server_modified.isoformat()
                    if metadata.server_modified
                    else None,
                    content_hash=metadata.content_hash,
                )
            else:
                self.logger.warning(f"路径不是文件: {path}")
                return None

        except ApiError as e:
            # 文件不存在时返回 None
            if hasattr(e.error, "is_path") and e.error.is_path():
                path_error = e.error.get_path()
                if hasattr(path_error, "is_not_found") and path_error.is_not_found():
                    self.logger.warning(f"文件不存在: {fid}")
                    return None
            self.logger.error(f"获取文件信息失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取文件信息失败: {e}")
            return None

    def get_dir_info(self, fid: str, *args, **kwargs) -> Optional[DriveFile]:
        """
        获取目录信息

        Args:
            fid: 目录ID
        Returns:
            DriveFile: 目录信息对象
        """
        try:
            if not self.client:
                self.logger.error("未登录Dropbox服务")
                return None

            path = self._normalize_path(fid)

            # 获取目录元数据
            metadata = self.client.files_get_metadata(path)

            # 检查是否为目录
            if isinstance(metadata, dropbox.files.FolderMetadata):
                return DriveFile(
                    fid=metadata.path_display,
                    name=metadata.name,
                    isfile=False,
                    path=metadata.path_display,
                    size=0,
                )
            else:
                self.logger.warning(f"路径不是目录: {path}")
                return None

        except ApiError as e:
            # 目录不存在时返回 None
            if hasattr(e.error, "is_path") and e.error.is_path():
                path_error = e.error.get_path()
                if hasattr(path_error, "is_not_found") and path_error.is_not_found():
                    self.logger.warning(f"目录不存在: {fid}")
                    return None
            self.logger.error(f"获取目录信息失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取目录信息失败: {e}")
            return None

    def get_file_list(self, fid: str, *args, **kwargs) -> List[DriveFile]:
        """
        获取目录下的文件列表

        Args:
            fid: 目录ID
        Returns:
            List[DriveFile]: 文件列表
        """
        try:
            if not self.client:
                self.logger.error("未登录Dropbox服务")
                return []

            path = self._normalize_path(fid)
            result = []

            # 获取目录内容
            response = self.client.files_list_folder(path)

            while True:
                for entry in response.entries:
                    if isinstance(entry, dropbox.files.FileMetadata):
                        result.append(
                            DriveFile(
                                fid=entry.path_display,
                                name=entry.name,
                                isfile=True,
                                path=entry.path_display,
                                size=entry.size,
                                last_modified=entry.server_modified.isoformat()
                                if entry.server_modified
                                else None,
                                content_hash=entry.content_hash,
                            )
                        )

                # 检查是否有更多结果
                if not response.has_more:
                    break
                response = self.client.files_list_folder_continue(response.cursor)

            return result

        except Exception as e:
            self.logger.error(f"获取文件列表失败: {e}")
            return []

    def get_dir_list(self, fid: str, *args, **kwargs) -> List[DriveFile]:
        """
        获取目录下的子目录列表

        Args:
            fid: 目录ID
        Returns:
            List[DriveFile]: 目录列表
        """
        try:
            if not self.client:
                self.logger.error("未登录Dropbox服务")
                return []

            path = self._normalize_path(fid)
            result = []

            # 获取目录内容
            response = self.client.files_list_folder(path)

            while True:
                for entry in response.entries:
                    if isinstance(entry, dropbox.files.FolderMetadata):
                        result.append(
                            DriveFile(
                                fid=entry.path_display,
                                name=entry.name,
                                isfile=False,
                                path=entry.path_display,
                                size=0,
                            )
                        )

                # 检查是否有更多结果
                if not response.has_more:
                    break
                response = self.client.files_list_folder_continue(response.cursor)

            return result

        except Exception as e:
            self.logger.error(f"获取目录列表失败: {e}")
            return []

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
        下载单个文件

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
            if not self.client:
                self.logger.error("未登录Dropbox服务")
                return False

            # 获取保存路径
            save_path = get_filepath(filedir, filename, filepath)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # 检查文件是否已存在
            if not overwrite and os.path.exists(save_path):
                self.logger.info(f"文件已存在，跳过下载: {save_path}")
                return True

            path = self._normalize_path(fid)

            # 获取文件信息用于进度显示
            file_info = self.get_file_info(fid)
            file_size = file_info.size if file_info else 0

            # 创建进度条
            progress_bar = None
            if file_size > 0:
                progress_bar = tqdm(
                    total=file_size,
                    ncols=120,
                    desc=os.path.basename(save_path),
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                )

            # 下载文件
            with open(save_path, "wb") as f:
                _, response = self.client.files_download(path)

                # 分块下载并更新进度
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_bar:
                            progress_bar.update(len(chunk))

            if progress_bar:
                progress_bar.close()

            self.logger.info(f"下载成功: {save_path}")
            return True

        except Exception as e:
            self.logger.error(f"下载文件失败: {e}")
            return False

    def upload_file(
        self,
        filepath: str,
        fid: str,
        recursion: bool = True,
        overwrite: bool = False,
        *args,
        **kwargs,
    ) -> bool:
        """
        上传单个文件

        Args:
            filepath (str): 本地文件路径
            fid (str): 目标文件夹ID
            recursion (bool): 是否递归上传(目录)
            overwrite (bool): 是否覆盖已存在文件
        Returns:
            bool: 上传是否成功
        """
        try:
            if not self.client:
                self.logger.error("未登录Dropbox服务")
                return False

            if not os.path.exists(filepath):
                self.logger.error(f"本地文件不存在: {filepath}")
                return False

            filename = os.path.basename(filepath)
            parent_path = self._normalize_path(fid)
            target_path = os.path.join(parent_path, filename).replace("\\", "/")
            target_path = self._normalize_path(target_path)

            file_size = os.path.getsize(filepath)

            # 检查文件是否已存在
            if not overwrite and self.exist(target_path):
                self.logger.info(f"文件已存在，跳过上传: {target_path}")
                return True

            # 创建进度条
            progress_bar = tqdm(
                total=file_size,
                ncols=120,
                desc=filename,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            )

            # 上传文件
            with open(filepath, "rb") as f:
                if file_size <= 150 * 1024 * 1024:  # 150MB以下使用普通上传
                    # 小文件直接上传
                    file_data = f.read()
                    self.client.files_upload(
                        file_data,
                        target_path,
                        mode=dropbox.files.WriteMode.overwrite
                        if overwrite
                        else dropbox.files.WriteMode.add,
                    )
                    progress_bar.update(file_size)
                else:
                    # 大文件分块上传
                    chunk_size = 4 * 1024 * 1024  # 4MB块大小

                    # 开始上传会话
                    first_chunk = f.read(chunk_size)
                    session_start_result = self.client.files_upload_session_start(
                        first_chunk
                    )
                    cursor = dropbox.files.UploadSessionCursor(
                        session_id=session_start_result.session_id,
                        offset=len(first_chunk),
                    )
                    progress_bar.update(len(first_chunk))

                    # 继续上传剩余块
                    while True:
                        chunk = f.read(chunk_size)
                        if len(chunk) == 0:
                            break

                        if len(chunk) < chunk_size:
                            # 最后一块
                            commit = dropbox.files.CommitInfo(
                                path=target_path,
                                mode=dropbox.files.WriteMode.overwrite
                                if overwrite
                                else dropbox.files.WriteMode.add,
                            )
                            self.client.files_upload_session_finish(
                                chunk, cursor, commit
                            )
                        else:
                            # 中间块
                            self.client.files_upload_session_append_v2(chunk, cursor)
                            cursor.offset += len(chunk)

                        progress_bar.update(len(chunk))

            progress_bar.close()
            self.logger.info(f"上传成功: {target_path}")
            return True

        except Exception as e:
            self.logger.error(f"上传文件失败: {e}")
            return False

    # ========== 以下是高级功能的实现 ==========

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

        Args:
            keyword: 搜索关键词
            fid: 搜索的起始目录ID，默认从根目录开始
            file_type: 文件类型筛选
        Returns:
            List[DriveFile]: 符合条件的文件列表
        """
        try:
            if not self.client:
                self.logger.error("未登录Dropbox服务")
                return []

            results = []

            # 使用Dropbox搜索API
            search_result = self.client.files_search_v2(
                query=keyword,
                options=dropbox.files.SearchOptions(
                    path=self._normalize_path(fid) if fid else None, max_results=100
                ),
            )

            for match in search_result.matches:
                metadata = match.metadata.get_metadata()

                # 文件类型筛选
                if file_type and isinstance(metadata, dropbox.files.FileMetadata):
                    file_ext = os.path.splitext(metadata.name)[1].lower().lstrip(".")
                    type_mapping = {
                        "image": ["jpg", "jpeg", "png", "gif", "bmp", "webp", "svg"],
                        "video": ["mp4", "avi", "mkv", "mov", "wmv", "flv", "m4v"],
                        "audio": ["mp3", "wav", "flac", "aac", "m4a", "ogg"],
                        "doc": ["pdf", "doc", "docx", "txt", "rtf", "odt"],
                        "archive": ["zip", "rar", "7z", "tar", "gz", "bz2"],
                    }

                    if file_type in type_mapping:
                        if file_ext not in type_mapping[file_type]:
                            continue
                    elif file_ext != file_type:
                        continue

                # 添加到结果中
                if isinstance(metadata, dropbox.files.FileMetadata):
                    results.append(
                        DriveFile(
                            fid=metadata.path_display,
                            name=metadata.name,
                            isfile=True,
                            path=metadata.path_display,
                            size=metadata.size,
                            last_modified=metadata.server_modified.isoformat()
                            if metadata.server_modified
                            else None,
                        )
                    )
                elif isinstance(metadata, dropbox.files.FolderMetadata):
                    results.append(
                        DriveFile(
                            fid=metadata.path_display,
                            name=metadata.name,
                            isfile=False,
                            path=metadata.path_display,
                            size=0,
                        )
                    )

            self.logger.info(f"搜索到 {len(results)} 个匹配的结果")
            return results

        except Exception as e:
            self.logger.error(f"搜索失败: {e}")
            return []

    def move(
        self,
        source_fid: str,
        target_fid: str,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        移动文件或目录

        Args:
            source_fid: 源文件/目录ID
            target_fid: 目标目录ID
        Returns:
            bool: 移动是否成功
        """
        try:
            if not self.client:
                self.logger.error("未登录Dropbox服务")
                return False

            source_path = self._normalize_path(source_fid)
            target_dir = self._normalize_path(target_fid)

            if not self.exist(source_path):
                self.logger.error(f"源文件不存在: {source_path}")
                return False

            # 构建目标路径
            source_name = os.path.basename(source_path)
            target_path = os.path.join(target_dir, source_name).replace("\\", "/")
            target_path = self._normalize_path(target_path)

            # 移动文件/目录
            self.client.files_move_v2(from_path=source_path, to_path=target_path)

            self.logger.info(f"移动成功: {source_path} -> {target_path}")
            return True

        except Exception as e:
            self.logger.error(f"移动失败: {e}")
            return False

    def copy(
        self,
        source_fid: str,
        target_fid: str,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        复制文件或目录

        Args:
            source_fid: 源文件/目录ID
            target_fid: 目标目录ID
        Returns:
            bool: 复制是否成功
        """
        try:
            if not self.client:
                self.logger.error("未登录Dropbox服务")
                return False

            source_path = self._normalize_path(source_fid)
            target_dir = self._normalize_path(target_fid)

            if not self.exist(source_path):
                self.logger.error(f"源文件不存在: {source_path}")
                return False

            # 构建目标路径
            source_name = os.path.basename(source_path)
            target_path = os.path.join(target_dir, source_name).replace("\\", "/")
            target_path = self._normalize_path(target_path)

            # 复制文件/目录
            self.client.files_copy_v2(from_path=source_path, to_path=target_path)

            self.logger.info(f"复制成功: {source_path} -> {target_path}")
            return True

        except Exception as e:
            self.logger.error(f"复制失败: {e}")
            return False

    def rename(self, fid: str, new_name: str, *args: Any, **kwargs: Any) -> bool:
        """
        重命名文件或目录

        Args:
            fid: 文件/目录ID
            new_name: 新名称
        Returns:
            bool: 重命名是否成功
        """
        try:
            if not self.client:
                self.logger.error("未登录Dropbox服务")
                return False

            source_path = self._normalize_path(fid)

            if not self.exist(source_path):
                self.logger.error(f"文件或目录不存在: {source_path}")
                return False

            # 构建新路径
            parent_dir = os.path.dirname(source_path)
            new_path = os.path.join(parent_dir, new_name).replace("\\", "/")
            new_path = self._normalize_path(new_path)

            # 重命名文件/目录
            self.client.files_move_v2(from_path=source_path, to_path=new_path)

            self.logger.info(f"重命名成功: {source_path} -> {new_path}")
            return True

        except Exception as e:
            self.logger.error(f"重命名失败: {e}")
            return False

    def share(
        self,
        *fids: str,
        password: str = "",
        expire_days: int = 0,
        description: str = "",
    ) -> Any:
        """
        分享文件或目录

        Args:
            fids: 要分享的文件或目录ID列表
            password: 分享密码（Dropbox不支持）
            expire_days: 分享链接有效期(天)
            description: 分享描述
        Returns:
            dict: 分享链接信息
        """
        try:
            if not self.client:
                self.logger.error("未登录Dropbox服务")
                return None

            if password:
                self.logger.warning("Dropbox不支持密码保护的分享链接")

            share_links = []
            for fid in fids:
                path = self._normalize_path(fid)

                if not self.exist(path):
                    self.logger.warning(f"文件不存在，无法分享: {path}")
                    continue

                try:
                    # 创建分享链接
                    settings = dropbox.sharing.SharedLinkSettings(
                        requested_visibility=dropbox.sharing.RequestedVisibility.public
                    )

                    # 设置过期时间
                    if expire_days > 0:
                        from datetime import datetime, timedelta

                        expire_time = datetime.now() + timedelta(days=expire_days)
                        settings = dropbox.sharing.SharedLinkSettings(
                            requested_visibility=dropbox.sharing.RequestedVisibility.public,
                            expires=expire_time,
                        )

                    shared_link = self.client.sharing_create_shared_link_with_settings(
                        path=path, settings=settings
                    )

                    share_links.append(
                        {
                            "fid": path,
                            "url": shared_link.url,
                            "expire_days": expire_days,
                            "description": description,
                        }
                    )

                except ApiError as e:
                    if e.error.is_shared_link_already_exists():
                        # 分享链接已存在，获取现有链接
                        existing_links = self.client.sharing_list_shared_links(
                            path=path, direct_only=True
                        )
                        if existing_links.links:
                            share_links.append(
                                {
                                    "fid": path,
                                    "url": existing_links.links[0].url,
                                    "expire_days": 0,  # 现有链接的过期时间未知
                                    "description": description,
                                }
                            )
                    else:
                        self.logger.error(f"创建分享链接失败: {e}")

            return {"links": share_links, "total": len(share_links)}

        except Exception as e:
            self.logger.error(f"分享失败: {e}")
            return None

    def get_quota(self, *args: Any, **kwargs: Any) -> dict:
        """
        获取网盘空间使用情况

        Returns:
            dict: 包含总空间、已用空间等信息的字典
        """
        try:
            if not self.client:
                self.logger.error("未登录Dropbox服务")
                return {}

            # 获取空间使用情况
            space_usage = self.client.users_get_space_usage()

            return {
                "total_space": space_usage.allocation.get_individual().allocated
                if hasattr(space_usage.allocation, "get_individual")
                else -1,
                "used_space": space_usage.used,
                "free_space": (
                    space_usage.allocation.get_individual().allocated - space_usage.used
                )
                if hasattr(space_usage.allocation, "get_individual")
                else -1,
                "account_type": "individual"
                if hasattr(space_usage.allocation, "get_individual")
                else "team",
            }

        except Exception as e:
            self.logger.error(f"获取配额信息失败: {e}")
            return {}

    # ========== 以下是不支持功能的警告实现 ==========

    def get_recycle_list(self, *args: Any, **kwargs: Any) -> List[DriveFile]:
        """
        获取回收站文件列表

        注意: Dropbox不支持回收站功能，删除的文件会直接永久删除
        可以通过文件版本历史恢复最近30天内的文件

        Returns:
            List[DriveFile]: 空列表
        """
        self.logger.warning(
            "Dropbox不支持回收站功能。删除的文件会直接永久删除。"
            "可以通过Dropbox网页版的文件版本历史恢复最近30天内的文件。"
        )
        return []

    def restore(self, *fids: str, **kwargs: Any) -> bool:
        """
        从回收站恢复文件

        注意: Dropbox不支持回收站功能，无法直接恢复文件
        可以通过文件版本历史恢复最近30天内的文件

        Args:
            fids: 要恢复的文件ID列表
        Returns:
            bool: 始终返回False
        """
        self.logger.warning(
            "Dropbox不支持回收站功能，无法直接恢复文件。"
            "请访问 Dropbox 网页版，通过文件版本历史恢复最近30天内的文件。"
        )
        return False

    def clear_recycle(self, *args: Any, **kwargs: Any) -> bool:
        """
        清空回收站

        注意: Dropbox不支持回收站功能，没有需要清空的内容

        Returns:
            bool: 始终返回True
        """
        self.logger.warning("Dropbox不支持回收站功能，没有需要清空的内容。")
        return True

    def save_shared(
        self,
        shared_url: str,
        fid: str = "/",
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        保存他人分享的内容到自己的网盘

        注意: Dropbox不支持直接保存他人分享的内容到自己的网盘
        需要手动下载后再上传

        Args:
            shared_url: 分享链接
            fid: 保存到的目录ID
        Returns:
            bool: 始终返回False
        """
        self.logger.warning(
            "Dropbox不支持直接保存他人分享的内容到自己的网盘。"
            "请手动下载分享的文件后再上传到您的Dropbox。"
        )
        return False
