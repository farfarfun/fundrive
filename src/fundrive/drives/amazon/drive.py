#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Amazon S3驱动实现

Amazon S3是亚马逊提供的对象存储服务，提供高可用性、可扩展性和数据持久性。
本驱动基于boto3 SDK实现，支持完整的S3操作功能。

主要功能:
- 存储桶管理
- 对象上传下载
- 目录模拟
- 权限管理
- 版本控制

作者: FunDrive Team
"""

# 标准库导入
import mimetypes
import os
from typing import Any, Dict, List, Optional

# 第三方库导入
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from nltlog import getLogger
from funsecret import read_secret

# 项目内部导入
from fundrive.core import BaseDrive, DriveFile, ensure_parent_dir

logger = getLogger("fundrive")


class S3Drive(BaseDrive):
    """
    Amazon S3驱动

    基于boto3 SDK实现的Amazon S3云存储驱动，支持完整的S3操作功能。
    支持多种认证方式和存储桶操作。
    """

    def __init__(
        self,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        region_name: Optional[str] = None,
        bucket_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        **kwargs,
    ):
        """
        初始化Amazon S3驱动

        Args:
            access_key_id: AWS访问密钥ID
            secret_access_key: AWS秘密访问密钥
            region_name: AWS区域名称
            bucket_name: S3存储桶名称
            endpoint_url: 自定义端点URL（用于兼容S3的服务）
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)

        # 从配置或环境变量获取认证信息
        self.access_key_id = (
            access_key_id
            or read_secret("fundrive", "amazon", "access_key_id")
            or os.getenv("AWS_ACCESS_KEY_ID")
        )
        self.secret_access_key = (
            secret_access_key
            or read_secret("fundrive", "amazon", "secret_access_key")
            or os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        self.region_name = (
            region_name
            or read_secret("fundrive", "amazon", "region_name")
            or os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        )
        self.bucket_name = (
            bucket_name
            or read_secret("fundrive", "amazon", "bucket_name")
            or os.getenv("S3_BUCKET_NAME")
        )
        self.endpoint_url = (
            endpoint_url
            or read_secret("fundrive", "amazon", "endpoint_url")
            or os.getenv("S3_ENDPOINT_URL")
        )

        # 初始化S3客户端和资源
        self.s3_client = None
        self.s3_resource = None
        self.bucket = None

    def login(
        self,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        region_name: Optional[str] = None,
        bucket_name: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """
        登录Amazon S3

        Args:
            access_key_id: AWS访问密钥ID
            secret_access_key: AWS秘密访问密钥
            region_name: AWS区域名称
            bucket_name: S3存储桶名称

        Returns:
            登录是否成功
        """
        try:
            logger.info("正在连接Amazon S3...")

            # 更新认证信息
            if access_key_id:
                self.access_key_id = access_key_id
            if secret_access_key:
                self.secret_access_key = secret_access_key
            if region_name:
                self.region_name = region_name
            if bucket_name:
                self.bucket_name = bucket_name

            # 检查必需的认证信息
            if not self.access_key_id or not self.secret_access_key:
                logger.error("缺少AWS认证信息")
                return False

            if not self.bucket_name:
                logger.error("缺少S3存储桶名称")
                return False

            # 创建S3客户端配置
            session_config = {
                "aws_access_key_id": self.access_key_id,
                "aws_secret_access_key": self.secret_access_key,
                "region_name": self.region_name,
            }

            if self.endpoint_url:
                session_config["endpoint_url"] = self.endpoint_url

            # 创建boto3会话
            session = boto3.Session(
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=self.region_name,
            )

            # 创建S3客户端和资源
            client_config = {}
            if self.endpoint_url:
                client_config["endpoint_url"] = self.endpoint_url

            self.s3_client = session.client("s3", **client_config)
            self.s3_resource = session.resource("s3", **client_config)

            # 验证连接并获取存储桶
            try:
                self.bucket = self.s3_resource.Bucket(self.bucket_name)
                # 尝试列出对象来验证权限
                list(self.bucket.objects.limit(1))
                logger.info(f"✅ 成功连接到S3存储桶: {self.bucket_name}")
                return True

            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "NoSuchBucket":
                    logger.error(f"存储桶不存在: {self.bucket_name}")
                elif error_code == "AccessDenied":
                    logger.error(f"访问被拒绝: {self.bucket_name}")
                else:
                    logger.error(f"S3错误: {error_code}")
                return False

        except NoCredentialsError:
            logger.error("❌ AWS认证信息无效")
            return False
        except Exception as e:
            logger.error(f"❌ S3连接失败: {e}")
            return False

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        检查对象是否存在

        Args:
            fid: 对象键（路径）

        Returns:
            对象是否存在
        """
        try:
            # 尝试获取对象元数据
            self.s3_client.head_object(Bucket=self.bucket_name, Key=fid)
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                logger.error(f"检查对象存在性失败: {e}")
                return False
        except Exception as e:
            logger.error(f"检查对象存在性失败: {e}")
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
        创建目录（在S3中创建空对象作为目录标记）

        Args:
            fid: 父目录路径
            name: 目录名
            return_if_exist: 如果目录已存在，是否返回已存在目录的ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            创建的目录ID（S3对象键）
        """
        try:
            logger.info(f"正在创建目录: {fid}/{name}")

            # 构建目录键（以/结尾表示目录）
            dir_key = f"{fid.rstrip('/')}/{name}/" if fid else f"{name}/"

            # 检查目录是否已存在
            if return_if_exist and self.exist(dir_key):
                logger.info(f"目录已存在: {dir_key}")
                return dir_key

            # 创建空对象作为目录标记
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=dir_key,
                Body=b"",
                ContentType="application/x-directory",
            )

            logger.info(f"✅ 目录创建成功: {dir_key}")
            return dir_key

        except Exception as e:
            logger.error(f"创建目录失败: {e}")
            return ""

    def delete(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        删除对象或目录

        Args:
            fid: 对象键（路径）

        Returns:
            删除是否成功
        """
        try:
            logger.info(f"正在删除对象: {fid}")

            if not fid:
                logger.error("fid 不能为空")
                return False

            # 判断是单个对象还是前缀（目录）。
            #
            # 历史实现只用 fid.endswith("/") 判断，于是传 "a/b" 这种不带尾斜杠的
            # 目录时会走 delete_object 删一个不存在的 key —— S3 对此返回 204，
            # 代码于是打印"✅ 对象删除成功"并返回 True，实际什么都没删。
            is_prefix = fid.endswith("/")
            if not is_prefix and not self._object_exists(fid):
                # 不是对象，看看它是不是一个前缀
                probe = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name, Prefix=fid.rstrip("/") + "/", MaxKeys=1
                )
                if probe.get("KeyCount", 0) > 0:
                    fid = fid.rstrip("/") + "/"
                    is_prefix = True
                else:
                    logger.error(f"删除目标不存在: {fid}")
                    return False

            if is_prefix:
                deleted = self._delete_by_prefix(fid)
                if deleted == 0:
                    logger.error(f"删除目标不存在: {fid}")
                    return False
                logger.info(f"✅ 删除了 {deleted} 个对象")
            else:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=fid)
                logger.info(f"✅ 对象删除成功: {fid}")

            return True

        except Exception as e:
            logger.error(f"删除对象失败: {e}")
            return False

    def _object_exists(self, key: str) -> bool:
        """精确判断某个 key 是否存在（不把前缀算作存在）。"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
                return False
            raise

    def _delete_by_prefix(self, prefix: str) -> int:
        """删除某前缀下的全部对象，返回删除数量。

        S3 的 ``delete_objects`` 每次最多接受 1000 个 key，因此必须分批；
        同时按页删除，避免把整个 bucket 的 key 列表先攒在内存里。
        """
        batch: List[dict] = []
        deleted = 0
        paginator = self.s3_client.get_paginator("list_objects_v2")

        def flush() -> int:
            if not batch:
                return 0
            response = self.s3_client.delete_objects(
                Bucket=self.bucket_name, Delete={"Objects": batch}
            )
            for err in response.get("Errors", []):
                logger.error(f"删除失败 {err.get('Key')}: {err.get('Message')}")
            count = len(response.get("Deleted", []))
            batch.clear()
            return count

        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
            for obj in page.get("Contents", []):
                batch.append({"Key": obj["Key"]})
                if len(batch) == 1000:
                    deleted += flush()
        deleted += flush()
        return deleted

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

            # 构建前缀
            prefix = f"{fid.rstrip('/')}/" if fid else ""
            delimiter = "/"

            files = []
            paginator = self.s3_client.get_paginator("list_objects_v2")

            for page in paginator.paginate(
                Bucket=self.bucket_name, Prefix=prefix, Delimiter=delimiter
            ):
                # 处理文件对象
                if "Contents" in page:
                    for obj in page["Contents"]:
                        key = obj["Key"]

                        # 跳过目录标记和当前目录本身
                        if key.endswith("/") or key == prefix:
                            continue

                        # 只包含直接子文件，不包含子目录中的文件
                        relative_key = key[len(prefix) :] if prefix else key
                        if "/" not in relative_key:
                            drive_file = DriveFile(
                                fid=key,
                                name=os.path.basename(key),
                                size=obj["Size"],
                                ext={
                                    "type": "file",
                                    "last_modified": obj["LastModified"].isoformat(),
                                    "etag": obj["ETag"].strip('"'),
                                    "storage_class": obj.get(
                                        "StorageClass", "STANDARD"
                                    ),
                                    "key": key,
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

            # 构建前缀
            prefix = f"{fid.rstrip('/')}/" if fid else ""
            delimiter = "/"

            dirs = []
            paginator = self.s3_client.get_paginator("list_objects_v2")

            for page in paginator.paginate(
                Bucket=self.bucket_name, Prefix=prefix, Delimiter=delimiter
            ):
                # 处理公共前缀（目录）
                if "CommonPrefixes" in page:
                    for common_prefix in page["CommonPrefixes"]:
                        dir_prefix = common_prefix["Prefix"]
                        dir_name = dir_prefix.rstrip("/").split("/")[-1]

                        drive_file = DriveFile(
                            fid=dir_prefix,
                            name=dir_name,
                            size=0,
                            ext={"type": "folder", "prefix": dir_prefix},
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
            fid: 对象键（路径）

        Returns:
            文件信息
        """
        try:
            logger.info(f"正在获取文件信息: {fid}")

            # 获取对象元数据
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=fid)

            drive_file = DriveFile(
                fid=fid,
                name=os.path.basename(fid),
                size=response["ContentLength"],
                ext={
                    "type": "file",
                    "last_modified": response["LastModified"].isoformat(),
                    "etag": response["ETag"].strip('"'),
                    "content_type": response.get("ContentType", ""),
                    "storage_class": response.get("StorageClass", "STANDARD"),
                    "metadata": response.get("Metadata", {}),
                    "key": fid,
                },
            )

            return drive_file

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.warning(f"文件不存在: {fid}")
                return None
            else:
                logger.error(f"获取文件信息失败: {e}")
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
                    fid="", name="root", size=0, ext={"type": "folder", "prefix": ""}
                )

            # 确保目录路径以/结尾
            dir_prefix = f"{fid.rstrip('/')}/"

            # 检查目录是否存在（通过列出对象）
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=dir_prefix, MaxKeys=1
            )

            if "Contents" in response or "CommonPrefixes" in response:
                return DriveFile(
                    fid=dir_prefix,
                    name=os.path.basename(fid.rstrip("/")),
                    size=0,
                    ext={"type": "folder", "prefix": dir_prefix},
                )
            else:
                logger.warning(f"目录不存在: {fid}")
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
        上传文件到S3

        Args:
            filepath: 本地文件路径
            fid: 目标目录路径
            filename: 上传后的文件名
            callback: 进度回调函数

        Returns:
            上传是否成功
        """
        try:
            logger.info(f"正在上传文件: {filepath}")

            if not os.path.exists(filepath):
                logger.error(f"文件不存在: {filepath}")
                return False

            # 构建对象键
            filename = filename or os.path.basename(filepath)
            key = f"{fid.rstrip('/')}/{filename}" if fid else filename

            # 获取文件大小和MIME类型
            file_size = os.path.getsize(filepath)
            content_type, _ = mimetypes.guess_type(filepath)

            # 准备上传参数
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            # 添加自定义元数据
            if "metadata" in kwargs:
                extra_args["Metadata"] = kwargs["metadata"]

            # 进度回调
            if callback:

                def progress_callback(bytes_transferred):
                    callback(bytes_transferred, file_size)
            else:
                progress_callback = None

            # 上传文件
            if file_size > 100 * 1024 * 1024:  # 大于100MB使用分片上传
                logger.info("使用分片上传...")
                self.s3_client.upload_file(
                    filepath,
                    self.bucket_name,
                    key,
                    ExtraArgs=extra_args,
                    Callback=progress_callback,
                )
            else:
                # 小文件直接上传
                with open(filepath, "rb") as f:
                    self.s3_client.put_object(
                        Bucket=self.bucket_name, Key=key, Body=f, **extra_args
                    )

            logger.info(f"✅ 文件上传成功: {key}")
            return True

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
        从S3下载文件

        Args:
            fid: 对象键（路径）
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

            # 获取文件大小
            try:
                response = self.s3_client.head_object(Bucket=self.bucket_name, Key=fid)
                file_size = response["ContentLength"]
            except Exception as _ignore:
                file_size = 0

            # 进度回调
            if callback:

                def progress_callback(bytes_transferred):
                    callback(bytes_transferred, file_size)
            else:
                progress_callback = None

            # 下载文件
            self.s3_client.download_file(
                self.bucket_name, fid, local_path, Callback=progress_callback
            )

            logger.info(f"✅ 文件下载成功: {local_path}")
            return True

        except Exception as e:
            logger.error(f"下载文件失败: {e}")
            return False

    def download_dir(
        self,
        fid: str,
        save_dir: str = "./cache",
        recursion: bool = True,
        overwrite: bool = False,
        ignore_filter=None,
        *args,
        **kwargs,
    ) -> bool:
        """
        下载整个目录

        Args:
            fid: 目录路径
            save_dir: 本地保存目录
            recursion: 是否递归下载子目录
            overwrite: 是否覆盖已存在的文件
            ignore_filter: 返回 True 表示跳过该文件的过滤函数

        Returns:
            下载是否成功
        """
        try:
            logger.info(f"正在下载目录: {fid}")

            # 构建前缀
            prefix = f"{fid.rstrip('/')}/" if fid else ""

            success_count = 0
            total_count = 0

            # 列出所有对象
            paginator = self.s3_client.get_paginator("list_objects_v2")

            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                if "Contents" in page:
                    for obj in page["Contents"]:
                        key = obj["Key"]

                        # 跳过目录标记
                        if key.endswith("/"):
                            continue

                        relative_key = key[len(prefix) :] if prefix else key
                        # recursion=False 时只取当前层，不进子目录
                        if not recursion and "/" in relative_key:
                            continue
                        if ignore_filter and ignore_filter(os.path.basename(key)):
                            continue

                        total_count += 1

                        try:
                            # 计算相对路径
                            relative_path = key[len(prefix) :] if prefix else key
                            local_path = os.path.join(save_dir, relative_path)

                            # 创建目录
                            ensure_parent_dir(local_path)

                            # 检查是否需要覆盖
                            if os.path.exists(local_path) and not overwrite:
                                logger.info(f"跳过已存在文件: {local_path}")
                                success_count += 1
                                continue

                            # 下载文件
                            self.s3_client.download_file(
                                self.bucket_name, key, local_path
                            )

                            success_count += 1
                            logger.info(f"下载进度: {success_count}/{total_count}")

                        except Exception as e:
                            logger.error(f"下载文件失败 {key}: {e}")

            logger.info(f"✅ 目录下载完成: {success_count}/{total_count} 个文件成功")
            return success_count > 0 or total_count == 0

        except Exception as e:
            logger.error(f"下载目录失败: {e}")
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

            # 构建前缀
            prefix = f"{fid.rstrip('/')}/" if fid else ""

            results = []
            paginator = self.s3_client.get_paginator("list_objects_v2")

            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                if "Contents" in page:
                    for obj in page["Contents"]:
                        key = obj["Key"]
                        filename = os.path.basename(key)

                        # 跳过目录标记
                        if key.endswith("/"):
                            continue

                        # 检查文件名是否包含关键词
                        if keyword.lower() in filename.lower():
                            drive_file = DriveFile(
                                fid=key,
                                name=filename,
                                size=obj["Size"],
                                ext={
                                    "type": "file",
                                    "last_modified": obj["LastModified"].isoformat(),
                                    "etag": obj["ETag"].strip('"'),
                                    "storage_class": obj.get(
                                        "StorageClass", "STANDARD"
                                    ),
                                    "key": key,
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
        获取存储配额信息（S3没有配额限制，返回存储桶统计）

        Returns:
            配额信息
        """
        try:
            # 计算存储桶使用情况
            total_size = 0
            object_count = 0

            paginator = self.s3_client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket_name):
                if "Contents" in page:
                    for obj in page["Contents"]:
                        if not obj["Key"].endswith("/"):  # 跳过目录标记
                            total_size += obj["Size"]
                            object_count += 1

            return {
                "bucket_name": self.bucket_name,
                "total_size": total_size,
                "total_size_gb": round(total_size / (1024**3), 2),
                "object_count": object_count,
                "region": self.region_name,
                "unlimited": True,  # S3没有硬性配额限制
            }

        except Exception as e:
            logger.error(f"获取配额信息失败: {e}")
            return {}

    def share(
        self,
        *fids: str,
        password: str = "",
        expire_days: int = 0,
        description: str = "",
        **kwargs: Any,
    ) -> dict:
        """生成预签名分享链接（BaseDrive 契约）。

        S3 预签名 URL 不支持独立密码；有效期用 ``expire_days`` 换算成秒，
        为 0 时用 :meth:`create_share_link` 的默认值。
        """
        if password:
            logger.warning("S3 预签名链接不支持独立密码，已忽略 password")
        extra = {}
        if expire_days:
            extra["expire_seconds"] = expire_days * 24 * 3600
        links = [self.create_share_link(fid, **extra) for fid in fids]
        return {
            "links": [link for link in links if link],
            "total": len([link for link in links if link]),
            "description": description,
        }

    def create_share_link(self, fid: str, expire_seconds: int = 3600) -> str:
        """
        创建预签名URL分享链接

        Args:
            fid: 对象键（路径）
            expire_seconds: 过期时间（秒）

        Returns:
            分享链接URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": fid},
                ExpiresIn=expire_seconds,
            )
            logger.info(f"生成分享链接: {fid}")
            return url

        except Exception as e:
            logger.error(f"生成分享链接失败: {e}")
            return ""

    def copy(self, source_fid: str, target_fid: str, *args: Any, **kwargs: Any) -> bool:
        """复制对象到目标**目录**（BaseDrive 契约）。

        注意与 :meth:`copy_object` 的区别：契约里 ``target_fid`` 是目录，
        源文件名会被拼接上去；``copy_object`` 的 ``target_fid`` 是完整的
        对象 key。两者语义不同，所以不能互相替代。
        """
        target_key = (
            f"{target_fid.rstrip('/')}/{os.path.basename(source_fid.rstrip('/'))}"
        )
        return self.copy_object(source_fid, target_key.lstrip("/"))

    def move(self, source_fid: str, target_fid: str, *args: Any, **kwargs: Any) -> bool:
        """移动对象到目标**目录**（BaseDrive 契约）。"""
        target_key = (
            f"{target_fid.rstrip('/')}/{os.path.basename(source_fid.rstrip('/'))}"
        )
        return self.move_object(source_fid, target_key.lstrip("/"))

    def copy_object(self, source_fid: str, target_fid: str) -> bool:
        """
        复制对象

        Args:
            source_fid: 源对象键
            target_fid: 目标对象键

        Returns:
            复制是否成功
        """
        try:
            copy_source = {"Bucket": self.bucket_name, "Key": source_fid}
            self.s3_client.copy_object(
                CopySource=copy_source, Bucket=self.bucket_name, Key=target_fid
            )
            logger.info(f"对象复制成功: {source_fid} -> {target_fid}")
            return True

        except Exception as e:
            logger.error(f"复制对象失败: {e}")
            return False

    def move_object(self, source_fid: str, target_fid: str) -> bool:
        """
        移动对象

        Args:
            source_fid: 源对象键
            target_fid: 目标对象键

        Returns:
            移动是否成功
        """
        try:
            # 先复制后删除
            if self.copy_object(source_fid, target_fid):
                if self.delete(source_fid):
                    logger.info(f"对象移动成功: {source_fid} -> {target_fid}")
                    return True
            return False

        except Exception as e:
            logger.error(f"移动对象失败: {e}")
            return False


# 向后兼容的别名
AmazonS3Drive = S3Drive
