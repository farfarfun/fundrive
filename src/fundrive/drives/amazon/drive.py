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
from funsecret import read_secret
from funutil import getLogger

# 项目内部导入
from fundrive.core import BaseDrive, DriveFile

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

            # 如果是目录，删除所有子对象
            if fid.endswith("/"):
                # 列出所有以该前缀开始的对象
                objects_to_delete = []
                paginator = self.s3_client.get_paginator("list_objects_v2")

                for page in paginator.paginate(Bucket=self.bucket_name, Prefix=fid):
                    if "Contents" in page:
                        for obj in page["Contents"]:
                            objects_to_delete.append({"Key": obj["Key"]})

                # 批量删除对象
                if objects_to_delete:
                    self.s3_client.delete_objects(
                        Bucket=self.bucket_name, Delete={"Objects": objects_to_delete}
                    )
                    logger.info(f"✅ 删除了 {len(objects_to_delete)} 个对象")
            else:
                # 删除单个对象
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=fid)
                logger.info(f"✅ 对象删除成功: {fid}")

            return True

        except Exception as e:
            logger.error(f"删除对象失败: {e}")
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
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

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

                        total_count += 1

                        try:
                            # 计算相对路径
                            relative_path = key[len(prefix) :] if prefix else key
                            local_path = os.path.join(filedir, relative_path)

                            # 创建目录
                            os.makedirs(os.path.dirname(local_path), exist_ok=True)

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

    def get_quota(self) -> Dict[str, Any]:
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
