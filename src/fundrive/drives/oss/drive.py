import os
from typing import List, Any, Optional


import oss2
from funsecret import read_secret
from funutil import getLogger
from tqdm import tqdm


from fundrive.core import BaseDrive, DriveFile
from fundrive.core.base import get_filepath


def public_oss_url(
    bucket_name="nm-algo", endpoint="oss-cn-hangzhou.aliyuncs.com", path=""
):
    """生成OSS公共访问URL

    声明:
    此函数用于生成阿里云OSS对象存储的公共访问URL。

    Args:
        bucket_name (str): OSS bucket名称
        endpoint (str): OSS访问域名
        path (str): 文件路径
    Returns:
        str: 完整的OSS URL
    """
    return f"https://{bucket_name}.{endpoint}/{path}"


class OSSDrive(BaseDrive):
    """阿里云OSS存储驱动实现

    基于阿里云OSS Python SDK实现的网盘驱动
    官方文档: https://help.aliyun.com/document_detail/32026.html
    SDK文档: https://oss-python-sdk-doc.readthedocs.io/

    功能特点:
    - 支持文件和目录的基本操作
    - 支持大文件上传下载进度显示
    - 支持批量操作和递归处理
    - 集成funsecret配置管理
    """

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """检查文件或目录是否存在

        Args:
            fid: 文件或目录ID
        Returns:
            bool: 是否存在
        """
        try:
            if not self.bucket:
                self.logger.error("未登录OSS服务")
                return False

            # 对于文件，直接检查对象是否存在
            if not fid.endswith("/"):
                return self.bucket.object_exists(fid)

            # 对于目录，检查是否有对象以该前缀开头
            result = self.bucket.list_objects(prefix=fid, max_keys=1)
            return len(result.object_list) > 0

        except Exception as e:
            self.logger.error(f"检查文件存在失败: {e}")
            return False

    def __init__(self, *args, **kwargs):
        """初始化OSS驱动

        Args:
            *args: 可变位置参数
            **kwargs: 可变关键字参数
        """
        super(OSSDrive, self).__init__(*args, **kwargs)
        self.bucket: oss2.Bucket = None
        self.logger = getLogger("oss_drive")
        self._bucket_name = None
        self._endpoint = None

    def login(
        self,
        access_key=None,
        access_secret=None,
        bucket_name=None,
        endpoint=None,
        connect_timeout=3600,
        *args,
        **kwargs,
    ) -> bool:
        """登录OSS服务

        Args:
            access_key (str, optional): 访问密钥ID
            access_secret (str, optional): 访问密钥密码
            bucket_name (str, optional): Bucket名称
            endpoint (str, optional): 访问域名
            connect_timeout (int, optional): 连接超时时间(秒)
        Returns:
            bool: 登录是否成功
        """
        try:
            # 读取配置信息
            access_key = access_key or read_secret(
                cate1="fundrive", cate2="oss", cate3="access_key"
            )
            access_secret = access_secret or read_secret(
                cate1="fundrive", cate2="oss", cate3="access_secret"
            )
            bucket_name = bucket_name or read_secret(
                cate1="fundrive", cate2="oss", cate3="bucket_name"
            )
            endpoint = endpoint or read_secret(
                cate1="fundrive", cate2="oss", cate3="endpoint"
            )

            if not all([access_key, access_secret, bucket_name, endpoint]):
                self.logger.error(
                    "OSS配置信息不完整，请检查access_key、access_secret、bucket_name、endpoint"
                )
                return False

            # 创建OSS连接
            auth = oss2.Auth(access_key, access_secret)
            self.bucket = oss2.Bucket(
                auth,
                endpoint,
                bucket_name,
                connect_timeout=connect_timeout,
                *args,
                **kwargs,
            )

            # 保存配置信息
            self._bucket_name = bucket_name
            self._endpoint = endpoint

            # 测试连接
            self.bucket.get_bucket_info()
            self._is_logged_in = True
            self._root_fid = ""

            self.logger.info(f"OSS登录成功，Bucket: {bucket_name}")
            return True

        except Exception as e:
            self.logger.error(f"OSS登录失败: {e}")
            return False

    def __get_file_list(self, oss_path: str) -> List[DriveFile]:
        """获取指定路径下的文件列表

        Args:
            oss_path: OSS路径
        Returns:
            List[DriveFile]: 文件列表
        """
        try:
            if not self.bucket:
                self.logger.error("未登录OSS服务")
                return []

            result = []
            dir_names = set()

            # 确保路径以/结尾
            prefix = oss_path.rstrip("/") + "/" if oss_path else ""

            # 获取所有对象
            for obj in oss2.ObjectIterator(self.bucket, prefix=prefix, delimiter="/"):
                if isinstance(obj, oss2.models.PrefixInfo):
                    # 这是一个目录
                    dir_name = obj.prefix.rstrip("/").split("/")[-1]
                    if dir_name and dir_name not in dir_names:
                        dir_names.add(dir_name)
                        result.append(
                            DriveFile(
                                fid=obj.prefix.rstrip("/"),
                                name=dir_name,
                                isfile=False,
                                path=obj.prefix.rstrip("/"),
                                size=0,
                            )
                        )
                else:
                    # 这是一个文件
                    if obj.key != prefix:  # 排除目录本身
                        filename = os.path.basename(obj.key)
                        if filename:  # 排除空文件名
                            result.append(
                                DriveFile(
                                    fid=obj.key,
                                    name=filename,
                                    isfile=True,
                                    path=obj.key,
                                    size=obj.size,
                                )
                            )

            return result

        except Exception as e:
            self.logger.error(f"获取文件列表失败: {e}")
            return []

    def mkdir(self, fid, name, return_if_exist=True, *args, **kwargs) -> str:
        """创建目录

        Args:
            fid: 父目录ID
            name: 目录名
            return_if_exist: 如果目录存在是否返回
        Returns:
            str: 创建的目录路径
        """
        try:
            if not self.bucket:
                self.logger.error("未登录OSS服务")
                return ""

            # 构建目录路径
            dir_path = os.path.join(fid, name).replace("\\", "/").strip("/")
            if not dir_path.endswith("/"):
                dir_path += "/"

            # 检查目录是否已存在
            if return_if_exist and self.exist(dir_path):
                self.logger.info(f"目录已存在: {dir_path}")
                return dir_path.rstrip("/")

            # 在OSS中创建目录（通过创建一个空对象）
            self.bucket.put_object(dir_path, b"")

            self.logger.info(f"创建目录成功: {dir_path}")
            return dir_path.rstrip("/")

        except Exception as e:
            self.logger.error(f"创建目录失败: {e}")
            return ""

    def delete(self, fid, *args, **kwargs) -> bool:
        """删除文件或目录

        Args:
            fid: 文件或目录ID
        Returns:
            bool: 是否删除成功
        """
        try:
            if not self.bucket:
                self.logger.error("未登录OSS服务")
                return False

            if not self.exist(fid):
                self.logger.warning(f"文件或目录不存在: {fid}")
                return True

            # 如果是目录，需要删除所有子对象
            if fid.endswith("/") or not fid or self.__is_directory(fid):
                prefix = fid.rstrip("/") + "/" if fid else ""
                # 获取所有子对象
                objects_to_delete = []
                for obj in oss2.ObjectIterator(self.bucket, prefix=prefix):
                    objects_to_delete.append(obj.key)

                # 批量删除
                if objects_to_delete:
                    result = self.bucket.batch_delete_objects(objects_to_delete)
                    if result.delete_result:
                        self.logger.info(f"成功删除 {len(result.delete_result)} 个对象")
            else:
                # 删除单个文件
                self.bucket.delete_object(fid)

            self.logger.info(f"删除成功: {fid}")
            return True

        except Exception as e:
            self.logger.error(f"删除失败: {e}")
            return False

    def __is_directory(self, fid: str) -> bool:
        """判断是否为目录

        Args:
            fid: 文件ID
        Returns:
            bool: 是否为目录
        """
        try:
            # 检查是否有以该路径为前缀的对象
            prefix = fid.rstrip("/") + "/"
            result = self.bucket.list_objects(prefix=prefix, max_keys=1)
            return len(result.object_list) > 0
        except:
            return False

    def get_file_info(self, fid, *args, **kwargs) -> Optional[DriveFile]:
        """获取文件信息

        Args:
            fid: 文件ID
        Returns:
            DriveFile: 文件信息对象
        """
        try:
            if not self.bucket:
                self.logger.error("未登录OSS服务")
                return None

            # 直接获取文件元数据
            try:
                obj_meta = self.bucket.get_object_meta(fid)
                return DriveFile(
                    fid=fid,
                    name=os.path.basename(fid),
                    isfile=True,
                    path=fid,
                    size=int(obj_meta.headers.get("Content-Length", 0)),
                    last_modified=obj_meta.headers.get("Last-Modified", ""),
                    content_type=obj_meta.headers.get("Content-Type", ""),
                )
            except oss2.exceptions.NoSuchKey:
                self.logger.warning(f"文件不存在: {fid}")
                return None

        except Exception as e:
            self.logger.error(f"获取文件信息失败: {e}")
            return None

    def get_dir_info(self, fid, *args, **kwargs) -> Optional[DriveFile]:
        """获取目录信息

        Args:
            fid: 目录ID
        Returns:
            DriveFile: 目录信息对象
        """
        try:
            if not self.bucket:
                self.logger.error("未登录OSS服务")
                return None

            # 检查目录是否存在
            dir_path = fid.rstrip("/") + "/" if fid else ""
            if not self.exist(dir_path):
                self.logger.warning(f"目录不存在: {fid}")
                return None

            # 返回目录信息
            return DriveFile(
                fid=fid,
                name=os.path.basename(fid.rstrip("/")) or "root",
                isfile=False,
                path=fid,
                size=0,
            )

        except Exception as e:
            self.logger.error(f"获取目录信息失败: {e}")
            return None

    def get_file_list(self, fid, *args, **kwargs) -> List[DriveFile]:
        """获取目录下的文件列表

        Args:
            fid: 目录ID
        Returns:
            List[DriveFile]: 文件列表
        """
        result = []
        for file in self.__get_file_list(fid):
            if file.isfile:  # 使用属性访问而不是字典访问
                result.append(file)
        return result

    def get_dir_list(self, fid, *args, **kwargs) -> List[DriveFile]:
        """获取目录下的子目录列表

        Args:
            fid: 目录ID
        Returns:
            List[DriveFile]: 目录列表
        """
        result = []
        for file in self.__get_file_list(fid):
            if not file.isfile and len(file.name) > 0:  # 使用属性访问
                result.append(file)
        return result

    def __download_file(self, save_path, oss_path, size=0, overwrite=False) -> bool:
        """下载单个文件的内部实现

        Args:
            save_path (str): 保存路径
            oss_path (str): OSS文件路径
            size (int): 文件大小
            overwrite (bool): 是否覆盖已存在文件
        Returns:
            bool: 下载是否成功
        """
        try:
            # 检查文件是否已存在且大小相同
            if (
                not overwrite
                and os.path.exists(save_path)
                and size > 0
                and size == os.path.getsize(save_path)
            ):
                self.logger.info(f"文件已存在，跳过下载: {save_path}")
                return True

            # 创建进度条
            bar = tqdm(
                total=size,
                ncols=120,
                desc=os.path.basename(save_path),
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            )

            def progress_callback(consumed_bytes, total_bytes):
                bar.update(consumed_bytes - bar.n)

            # 下载文件
            self.bucket.get_object_to_file(
                oss_path, save_path, progress_callback=progress_callback
            )
            bar.close()

            self.logger.info(f"下载成功: {save_path}")
            return True

        except Exception as e:
            self.logger.error(f"下载文件失败: {e}")
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
        """下载单个文件

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
            if not self.bucket:
                self.logger.error("未登录OSS服务")
                return False

            # 获取保存路径
            save_path = get_filepath(filedir, filename, filepath)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # 获取文件信息
            file_info = self.get_file_info(fid=fid)
            if not file_info:
                self.logger.error(f"文件不存在: {fid}")
                return False

            return self.__download_file(
                save_path=save_path,
                oss_path=fid,
                size=file_info.size or 0,  # 使用属性访问
                overwrite=overwrite,
            )

        except Exception as e:
            self.logger.error(f"下载文件失败: {e}")
            return False

    def upload_file(
        self, filepath, fid, recursion=True, overwrite=False, *args, **kwargs
    ) -> bool:
        """上传单个文件

        Args:
            filepath (str): 本地文件路径
            fid (str): 目标文件夹ID(OSS路径)
            recursion (bool): 是否递归上传(目录)
            overwrite (bool): 是否覆盖已存在文件
        Returns:
            bool: 上传是否成功
        """
        try:
            if not self.bucket:
                self.logger.error("未登录OSS服务")
                return False

            if not os.path.exists(filepath):
                self.logger.error(f"本地文件不存在: {filepath}")
                return False

            filename = os.path.basename(filepath)
            oss_path = os.path.join(fid, filename).replace("\\", "/")
            size = os.path.getsize(filepath)

            # 检查文件是否已存在
            if not overwrite:
                file_info = self.get_file_info(oss_path)
                if file_info and file_info.size == size:
                    self.logger.info(f"文件已存在，跳过上传: {oss_path}")
                    return True

            # 创建进度条
            bar = tqdm(
                total=size,
                ncols=120,
                desc=filename,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            )

            def progress_callback(consumed_bytes, total_bytes):
                bar.update(consumed_bytes - bar.n)

            # 上传文件
            with open(filepath, "rb") as f:
                self.bucket.put_object(oss_path, f, progress_callback=progress_callback)

            bar.close()
            self.logger.info(f"上传成功: {oss_path}")
            return True

        except Exception as e:
            self.logger.error(f"上传文件失败: {e}")
            return False

    # ========== 以下是其他抽象方法的实现 ==========

    def share(
        self,
        *fids: str,
        password: str = "",
        expire_days: int = 0,
        description: str = "",
    ) -> Any:
        """分享文件或目录

        注意: OSS 不直接支持分享功能，但可以生成公共访问链接

        Args:
            fids: 要分享的文件或目录ID列表
            password: 分享密码（OSS不支持）
            expire_days: 分享链接有效期(天)，0表示永久有效
            description: 分享描述
        Returns:
            dict: 分享链接信息
        """
        try:
            if not self.bucket:
                self.logger.error("未登录OSS服务")
                return None

            if password:
                self.logger.warning("OSS不支持密码保护的分享链接")

            share_links = []
            for fid in fids:
                if self.exist(fid):
                    # 生成预签名URL
                    if expire_days > 0:
                        expires = expire_days * 24 * 3600  # 转换为秒
                        url = self.bucket.sign_url("GET", fid, expires)
                    else:
                        # 生成公共访问URL（需要bucket为公共读）
                        url = public_oss_url(self._bucket_name, self._endpoint, fid)

                    share_links.append(
                        {
                            "fid": fid,
                            "url": url,
                            "expire_days": expire_days,
                            "description": description,
                        }
                    )
                else:
                    self.logger.warning(f"文件不存在，无法分享: {fid}")

            return {"links": share_links, "total": len(share_links)}

        except Exception as e:
            self.logger.error(f"分享失败: {e}")
            return None

    def save_shared(
        self,
        shared_url: str,
        fid: str,
        password: Optional[str] = None,
    ) -> bool:
        """保存他人的分享内容到自己的网盘

        注意: OSS不支持此功能

        Args:
            shared_url: 分享链接
            fid: 保存到的目标目录ID
            password: 分享密码
        Returns:
            bool: 保存是否成功
        """
        self.logger.warning("OSS不支持保存分享内容功能")
        return False

    def search(
        self,
        keyword: str,
        fid: Optional[str] = None,
        file_type: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> List[DriveFile]:
        """搜索文件或目录

        Args:
            keyword: 搜索关键词
            fid: 搜索的起始目录ID，默认从根目录开始
            file_type: 文件类型筛选
        Returns:
            List[DriveFile]: 符合条件的文件列表
        """
        try:
            if not self.bucket:
                self.logger.error("未登录OSS服务")
                return []

            results = []
            prefix = fid.rstrip("/") + "/" if fid else ""

            # 遍历所有对象进行搜索
            for obj in oss2.ObjectIterator(self.bucket, prefix=prefix):
                filename = os.path.basename(obj.key)

                # 关键词匹配
                if keyword.lower() in filename.lower():
                    # 文件类型筛选
                    if file_type:
                        file_ext = os.path.splitext(filename)[1].lower().lstrip(".")
                        type_mapping = {
                            "image": [
                                "jpg",
                                "jpeg",
                                "png",
                                "gif",
                                "bmp",
                                "webp",
                                "svg",
                            ],
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

                    results.append(
                        DriveFile(
                            fid=obj.key,
                            name=filename,
                            isfile=True,
                            path=obj.key,
                            size=obj.size,
                        )
                    )

            self.logger.info(f"搜索到 {len(results)} 个匹配的文件")
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
        """移动文件或目录

        Args:
            source_fid: 源文件/目录ID
            target_fid: 目标目录ID
        Returns:
            bool: 移动是否成功
        """
        try:
            if not self.bucket:
                self.logger.error("未登录OSS服务")
                return False

            # 先复制，再删除原文件
            if self.copy(source_fid, target_fid):
                return self.delete(source_fid)

            return False

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
        """复制文件或目录

        Args:
            source_fid: 源文件/目录ID
            target_fid: 目标目录ID
        Returns:
            bool: 复制是否成功
        """
        try:
            if not self.bucket:
                self.logger.error("未登录OSS服务")
                return False

            if not self.exist(source_fid):
                self.logger.error(f"源文件不存在: {source_fid}")
                return False

            # 构建目标路径
            source_name = os.path.basename(source_fid.rstrip("/"))
            target_path = os.path.join(target_fid, source_name).replace("\\", "/")

            # 如果是文件，直接复制
            if not source_fid.endswith("/") and not self.__is_directory(source_fid):
                self.bucket.copy_object(self._bucket_name, source_fid, target_path)
                self.logger.info(f"复制文件成功: {source_fid} -> {target_path}")
                return True

            # 如果是目录，递归复制所有子对象
            prefix = source_fid.rstrip("/") + "/"
            for obj in oss2.ObjectIterator(self.bucket, prefix=prefix):
                # 计算相对路径
                relative_path = obj.key[len(prefix) :]
                new_target = os.path.join(target_path, relative_path).replace("\\", "/")

                # 复制对象
                self.bucket.copy_object(self._bucket_name, obj.key, new_target)

            self.logger.info(f"复制目录成功: {source_fid} -> {target_path}")
            return True

        except Exception as e:
            self.logger.error(f"复制失败: {e}")
            return False

    def rename(self, fid: str, new_name: str, *args: Any, **kwargs: Any) -> bool:
        """重命名文件或目录

        Args:
            fid: 文件/目录ID
            new_name: 新名称
        Returns:
            bool: 重命名是否成功
        """
        try:
            if not self.bucket:
                self.logger.error("未登录OSS服务")
                return False

            if not self.exist(fid):
                self.logger.error(f"文件或目录不存在: {fid}")
                return False

            # 构建新路径
            parent_dir = os.path.dirname(fid.rstrip("/"))
            new_path = os.path.join(parent_dir, new_name).replace("\\", "/")

            # 如果是文件，直接重命名
            if not fid.endswith("/") and not self.__is_directory(fid):
                self.bucket.copy_object(self._bucket_name, fid, new_path)
                self.bucket.delete_object(fid)
                self.logger.info(f"重命名文件成功: {fid} -> {new_path}")
                return True

            # 如果是目录，重命名所有子对象
            prefix = fid.rstrip("/") + "/"
            new_prefix = new_path.rstrip("/") + "/"

            objects_to_copy = []
            for obj in oss2.ObjectIterator(self.bucket, prefix=prefix):
                relative_path = obj.key[len(prefix) :]
                new_obj_path = new_prefix + relative_path
                objects_to_copy.append((obj.key, new_obj_path))

            # 复制所有对象到新位置
            for old_path, new_obj_path in objects_to_copy:
                self.bucket.copy_object(self._bucket_name, old_path, new_obj_path)

            # 删除原对象
            objects_to_delete = [old_path for old_path, _ in objects_to_copy]
            if objects_to_delete:
                self.bucket.batch_delete_objects(objects_to_delete)

            self.logger.info(f"重命名目录成功: {fid} -> {new_path}")
            return True

        except Exception as e:
            self.logger.error(f"重命名失败: {e}")
            return False

    def get_quota(self, *args: Any, **kwargs: Any) -> dict:
        """获取网盘空间使用情况

        Returns:
            dict: 包含总空间、已用空间等信息的字典
        """
        try:
            if not self.bucket:
                self.logger.error("未登录OSS服务")
                return {}

            # OSS没有直接的配额查询API，这里提供bucket信息
            bucket_info = self.bucket.get_bucket_info()

            # 计算已使用空间（遍历所有对象）
            used_space = 0
            object_count = 0

            for obj in oss2.ObjectIterator(self.bucket):
                used_space += obj.size
                object_count += 1

            return {
                "total_space": -1,  # OSS没有总空间限制
                "used_space": used_space,
                "free_space": -1,  # 无限制
                "object_count": object_count,
                "bucket_name": bucket_info.name,
                "creation_date": bucket_info.creation_date,
                "storage_class": bucket_info.storage_class,
            }

        except Exception as e:
            self.logger.error(f"获取配额信息失败: {e}")
            return {}

    # ========== 以下方法OSS不支持，提供警告实现 ==========

    def get_recycle_list(self, *args: Any, **kwargs: Any) -> List[DriveFile]:
        """获取回收站文件列表

        OSS不支持回收站功能
        """
        self.logger.warning("OSS不支持回收站功能")
        return []

    def restore(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """从回收站恢复文件

        OSS不支持回收站功能
        """
        self.logger.warning("OSS不支持回收站功能")
        return False

    def clear_recycle(self, *args: Any, **kwargs: Any) -> bool:
        """清空回收站

        OSS不支持回收站功能
        """
        self.logger.warning("OSS不支持回收站功能")
        return False

    def get_download_url(self, fid: str, *args: Any, **kwargs: Any) -> str:
        """获取文件下载链接

        Args:
            fid: 文件ID
        Returns:
            str: 下载链接
        """
        try:
            if not self.bucket:
                self.logger.error("未登录OSS服务")
                return ""

            if not self.exist(fid):
                self.logger.error(f"文件不存在: {fid}")
                return ""

            # 生成预签名URL，有效期1小时
            url = self.bucket.sign_url("GET", fid, 3600)
            return url

        except Exception as e:
            self.logger.error(f"获取下载链接失败: {e}")
            return ""

    def get_upload_url(
        self,
        fid: str,
        filename: str,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """获取文件上传链接

        Args:
            fid: 目标目录ID
            filename: 文件名
        Returns:
            str: 上传链接
        """
        try:
            if not self.bucket:
                self.logger.error("未登录OSS服务")
                return ""

            # 构建上传路径
            upload_path = os.path.join(fid, filename).replace("\\", "/")

            # 生成预签名上传URL，有效期1小时
            url = self.bucket.sign_url("PUT", upload_path, 3600)
            return url

        except Exception as e:
            self.logger.error(f"获取上传链接失败: {e}")
            return ""
