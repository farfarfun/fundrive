import os
import subprocess
import tempfile
from typing import Any, List, Optional
from funinstall.install import OSSUtilInstall
from funsecret import read_secret
from funutil import getLogger
from fundrive.core import BaseDrive, DriveFile


logger = getLogger("fundrive-ossutil")


class OSSUtilDrive(BaseDrive):
    """基于ossutil命令行工具的阿里云OSS存储驱动实现

    基于阿里云OSS官方命令行工具ossutil 2.0实现的网盘驱动
    官方文档: https://help.aliyun.com/zh/oss/developer-reference/ossutil-overview/

    功能特点:
    - 基于官方ossutil命令行工具，稳定可靠
    - 支持文件和目录的基本操作
    - 支持大文件上传下载进度显示
    - 支持批量操作和递归处理
    - 自动下载和配置ossutil工具
    - 集成funsecret配置管理
    """

    def __init__(self, *args, **kwargs):
        """初始化OSSUtil驱动

        Args:
            *args: 可变位置参数
            **kwargs: 可变关键字参数
        """
        super(OSSUtilDrive, self).__init__(*args, **kwargs)

        self._ossutil_path = None
        self._config_file = None
        self._bucket_name = None
        self._endpoint = None
        self._access_key = None
        self._access_secret = None

    def _create_config_file(self) -> bool:
        """创建ossutil配置文件

        Returns:
            bool: 配置文件创建是否成功
        """
        try:
            # 创建配置目录
            config_dir = os.path.expanduser("~/.fundrive/ossutil")
            os.makedirs(config_dir, exist_ok=True)

            # 配置文件路径
            self._config_file = os.path.join(config_dir, "config")

            # 配置内容
            config_content = f"""[Credentials]
language=CH
accessKeyID={self._access_key}
accessKeySecret={self._access_secret}
endpoint={self._endpoint}
"""

            # 写入配置文件
            with open(self._config_file, "w", encoding="utf-8") as f:
                f.write(config_content)

            logger.info(f"ossutil配置文件创建成功: {self._config_file}")
            return True

        except Exception as e:
            logger.error(f"创建ossutil配置文件失败: {e}")
            return False

    def _run_ossutil_command(
        self, command: List[str], capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """执行ossutil命令

        Args:
            command: 命令参数列表
            capture_output: 是否捕获输出

        Returns:
            subprocess.CompletedProcess: 命令执行结果
        """
        if not self._ossutil_path:
            raise RuntimeError("ossutil工具未初始化")

        # 构建完整命令
        full_command = [self._ossutil_path] + command

        # 添加配置文件参数
        if self._config_file:
            full_command.extend(["-c", self._config_file])

        logger.info(f"执行ossutil命令: {' '.join(full_command)}")

        # 执行命令
        result = subprocess.run(
            full_command, capture_output=capture_output, text=True, encoding="utf-8"
        )

        if result.returncode != 0:
            logger.error(f"ossutil命令执行失败: {result.stderr}")

        return result

    def login(
        self,
        access_key: Optional[str] = None,
        access_secret: Optional[str] = None,
        bucket_name: Optional[str] = None,
        endpoint: Optional[str] = None,
        *args,
        **kwargs,
    ) -> bool:
        """登录OSS服务

        Args:
            access_key: 访问密钥ID
            access_secret: 访问密钥密码
            bucket_name: Bucket名称
            endpoint: 访问域名

        Returns:
            bool: 登录是否成功
        """
        try:
            # 读取配置信息
            self._access_key = access_key or read_secret(
                cate1="fundrive", cate2="ossutil", cate3="access_key"
            )
            self._access_secret = access_secret or read_secret(
                cate1="fundrive", cate2="ossutil", cate3="access_secret"
            )
            self._bucket_name = bucket_name or read_secret(
                cate1="fundrive", cate2="ossutil", cate3="bucket_name"
            )
            self._endpoint = endpoint or read_secret(
                cate1="fundrive", cate2="ossutil", cate3="endpoint"
            )

            if not all(
                [
                    self._access_key,
                    self._access_secret,
                    self._bucket_name,
                    self._endpoint,
                ]
            ):
                logger.error(
                    "OSS配置信息不完整，请检查access_key、access_secret、bucket_name、endpoint"
                )
                return False

            # 下载并设置ossutil
            installer = OSSUtilInstall()
            installer.install()
            self._ossutil_path = f"{installer.install_path}/ossutil"

            # 创建配置文件
            if not self._create_config_file():
                return False

            # 测试连接 - 列举bucket
            result = self._run_ossutil_command(["ls"])
            if result.returncode != 0:
                logger.error("ossutil连接测试失败")
                return False

            self._is_logged_in = True
            self._root_fid = f"oss://{self._bucket_name}/"

            logger.success(f"OSS登录成功，Bucket: {self._bucket_name}")
            return True

        except Exception as e:
            logger.error(f"OSS登录失败: {e}")
            return False

    def _parse_ls_output(self, output: str, prefix: str = "") -> List[DriveFile]:
        """解析ls命令输出

        Args:
            output: ls命令输出
            prefix: 路径前缀

        Returns:
            List[DriveFile]: 文件列表
        """
        files = []
        lines = output.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("Object Number") or line.startswith("Total"):
                continue

            # 解析ls输出格式
            # 示例: 2023-12-01 10:30:45    1024  oss://bucket/path/file.txt
            parts = line.split()
            if len(parts) >= 4:
                # 提取文件信息
                size_str = parts[2]
                path = parts[3]

                # 解析路径
                if path.startswith(f"oss://{self._bucket_name}/"):
                    relative_path = path[len(f"oss://{self._bucket_name}/") :]

                    # 判断是文件还是目录
                    is_dir = path.endswith("/")

                    # 计算文件名
                    name = os.path.basename(relative_path.rstrip("/"))

                    # 解析文件大小
                    try:
                        size = int(size_str) if not is_dir else 0
                    except ValueError:
                        size = 0

                    files.append(
                        DriveFile(
                            fid=relative_path.rstrip("/"),
                            name=name,
                            isfile=not is_dir,
                            path=relative_path,
                            size=size,
                        )
                    )

        return files

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """检查文件或目录是否存在

        Args:
            fid: 文件或目录ID

        Returns:
            bool: 是否存在
        """
        try:
            if not self._is_logged_in:
                logger.error("未登录OSS服务")
                return False

            # 构建完整路径
            oss_path = f"oss://{self._bucket_name}/{fid.lstrip('/')}"

            # 使用stat命令检查文件是否存在
            result = self._run_ossutil_command(["stat", oss_path])
            return result.returncode == 0

        except Exception as e:
            logger.error(f"检查文件存在失败: {e}")
            return False

    def mkdir(
        self,
        fid: str,
        name: str,
        return_if_exist: bool = True,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """创建目录

        Args:
            fid: 父目录ID
            name: 目录名
            return_if_exist: 如果目录存在是否返回

        Returns:
            str: 创建的目录路径
        """
        try:
            if not self._is_logged_in:
                logger.error("未登录OSS服务")
                return ""

            # 构建目录路径
            dir_path = os.path.join(fid, name).replace("\\", "/").strip("/")

            # 检查目录是否已存在
            if return_if_exist and self.exist(dir_path + "/"):
                logger.info(f"目录已存在: {dir_path}")
                return dir_path

            # 在OSS中创建目录（通过创建一个空对象）
            oss_path = f"oss://{self._bucket_name}/{dir_path}/"

            # 创建一个临时空文件来代表目录
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
                temp_file.write("")
                temp_file_path = temp_file.name

            try:
                # 上传空文件作为目录标记
                result = self._run_ossutil_command(["cp", temp_file_path, oss_path])
                if result.returncode == 0:
                    logger.success(f"创建目录成功: {dir_path}")
                    return dir_path
                else:
                    logger.error(f"创建目录失败: {result.stderr}")
                    return ""
            finally:
                # 清理临时文件
                os.unlink(temp_file_path)

        except Exception as e:
            logger.error(f"创建目录失败: {e}")
            return ""

    def delete(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """删除文件或目录

        Args:
            fid: 文件或目录ID

        Returns:
            bool: 是否删除成功
        """
        try:
            if not self._is_logged_in:
                logger.error("未登录OSS服务")
                return False

            if not self.exist(fid):
                logger.warning(f"文件或目录不存在: {fid}")
                return True

            # 构建完整路径
            oss_path = f"oss://{self._bucket_name}/{fid.lstrip('/')}"

            # 使用rm命令删除，-r参数用于递归删除目录
            result = self._run_ossutil_command(["rm", oss_path, "-r", "-f"])

            if result.returncode == 0:
                logger.success(f"删除成功: {fid}")
                return True
            else:
                logger.error(f"删除失败: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"删除失败: {e}")
            return False

    def get_file_list(self, fid: str, *args: Any, **kwargs: Any) -> List[DriveFile]:
        """获取目录下的文件列表

        Args:
            fid: 目录ID

        Returns:
            List[DriveFile]: 文件列表
        """
        try:
            if not self._is_logged_in:
                logger.error("未登录OSS服务")
                return []

            # 构建目录路径
            dir_path = fid.rstrip("/") + "/" if fid else ""
            oss_path = f"oss://{self._bucket_name}/{dir_path}"

            # 列举文件，不递归
            result = self._run_ossutil_command(["ls", oss_path])

            if result.returncode != 0:
                logger.error(f"获取文件列表失败: {result.stderr}")
                return []

            # 解析输出并过滤出文件
            all_items = self._parse_ls_output(result.stdout, dir_path)
            return [item for item in all_items if item.isfile]

        except Exception as e:
            logger.error(f"获取文件列表失败: {e}")
            return []

    def get_dir_list(self, fid: str, *args: Any, **kwargs: Any) -> List[DriveFile]:
        """获取目录下的子目录列表

        Args:
            fid: 目录ID

        Returns:
            List[DriveFile]: 目录列表
        """
        try:
            if not self._is_logged_in:
                logger.error("未登录OSS服务")
                return []

            # 构建目录路径
            dir_path = fid.rstrip("/") + "/" if fid else ""
            oss_path = f"oss://{self._bucket_name}/{dir_path}"

            # 列举目录，不递归
            result = self._run_ossutil_command(["ls", oss_path])

            if result.returncode != 0:
                logger.error(f"获取目录列表失败: {result.stderr}")
                return []

            # 解析输出并过滤出目录
            all_items = self._parse_ls_output(result.stdout, dir_path)
            return [item for item in all_items if not item.isfile]

        except Exception as e:
            logger.error(f"获取目录列表失败: {e}")
            return []

    def get_file_info(self, fid: str, *args: Any, **kwargs: Any) -> Optional[DriveFile]:
        """获取文件信息

        Args:
            fid: 文件ID

        Returns:
            Optional[DriveFile]: 文件信息对象
        """
        try:
            if not self._is_logged_in:
                logger.error("未登录OSS服务")
                return None

            # 构建完整路径
            oss_path = f"oss://{self._bucket_name}/{fid.lstrip('/')}"

            # 使用stat命令获取文件信息
            result = self._run_ossutil_command(["stat", oss_path])

            if result.returncode != 0:
                logger.warning(f"文件不存在: {fid}")
                return None

            # 解析stat输出获取文件信息
            lines = result.stdout.strip().split("\n")
            size = 0
            last_modified = ""
            content_type = ""

            for line in lines:
                if "Content-Length:" in line:
                    try:
                        size = int(line.split(":")[-1].strip())
                    except ValueError:
                        pass
                elif "Last-Modified:" in line:
                    last_modified = line.split(":", 1)[-1].strip()
                elif "Content-Type:" in line:
                    content_type = line.split(":", 1)[-1].strip()

            return DriveFile(
                fid=fid,
                name=os.path.basename(fid),
                isfile=True,
                path=fid,
                size=size,
                last_modified=last_modified,
                content_type=content_type,
            )

        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return None

    def get_dir_info(self, fid: str, *args: Any, **kwargs: Any) -> Optional[DriveFile]:
        """获取目录信息

        Args:
            fid: 目录ID

        Returns:
            Optional[DriveFile]: 目录信息对象
        """
        try:
            if not self._is_logged_in:
                logger.error("未登录OSS服务")
                return None

            # 检查目录是否存在
            if not self.exist(fid + "/" if not fid.endswith("/") else fid):
                logger.warning(f"目录不存在: {fid}")
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
            logger.error(f"获取目录信息失败: {e}")
            return None

    def download_file(
        self,
        fid: str,
        save_dir: Optional[str] = None,
        filename: Optional[str] = None,
        filepath: Optional[str] = None,
        overwrite: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """下载单个文件

        Args:
            fid: 文件ID
            save_dir: 文件保存目录
            filename: 文件名
            filepath: 完整的文件保存路径
            overwrite: 是否覆盖已存在的文件

        Returns:
            bool: 下载是否成功
        """
        try:
            if not self._is_logged_in:
                logger.error("未登录OSS服务")
                return False

            # 确定保存路径
            if filepath:
                save_path = filepath
            else:
                if not save_dir:
                    save_dir = os.getcwd()
                if not filename:
                    filename = os.path.basename(fid)
                save_path = os.path.join(save_dir, filename)

            # 创建保存目录
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # 检查文件是否已存在
            if not overwrite and os.path.exists(save_path):
                logger.info(f"文件已存在，跳过下载: {save_path}")
                return True

            # 构建OSS路径
            oss_path = f"oss://{self._bucket_name}/{fid.lstrip('/')}"

            # 使用cp命令下载文件
            result = self._run_ossutil_command(["cp", oss_path, save_path])

            if result.returncode == 0:
                logger.success(f"下载成功: {save_path}")
                return True
            else:
                logger.error(f"下载失败: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"下载文件失败: {e}")
            return False

    def upload_file(self, filepath: str, fid: str, *args: Any, **kwargs: Any) -> bool:
        """上传单个文件

        Args:
            filepath: 本地文件路径
            fid: 目标文件夹ID

        Returns:
            bool: 上传是否成功
        """
        try:
            if not self._is_logged_in:
                logger.error("未登录OSS服务")
                return False

            if not os.path.exists(filepath):
                logger.error(f"本地文件不存在: {filepath}")
                return False

            # 构建目标路径
            filename = os.path.basename(filepath)
            target_path = os.path.join(fid, filename).replace("\\", "/").lstrip("/")
            oss_path = f"oss://{self._bucket_name}/{target_path}"

            # 使用cp命令上传文件
            result = self._run_ossutil_command(["cp", filepath, oss_path])

            if result.returncode == 0:
                logger.success(f"上传成功: {oss_path}")
                return True
            else:
                logger.error(f"上传失败: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"上传文件失败: {e}")
            return False

    # ========== 以下是高级功能方法的实现 ==========

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
            if not self._is_logged_in:
                logger.error("未登录OSS服务")
                return []

            # 构建搜索路径
            search_path = fid.rstrip("/") + "/" if fid else ""
            oss_path = f"oss://{self._bucket_name}/{search_path}"

            # 使用ls命令递归列举所有文件
            result = self._run_ossutil_command(["ls", oss_path, "-r"])

            if result.returncode != 0:
                logger.error(f"搜索失败: {result.stderr}")
                return []

            # 解析输出并进行关键词匹配
            all_items = self._parse_ls_output(result.stdout, search_path)
            results = []

            for item in all_items:
                # 关键词匹配
                if keyword.lower() in item.name.lower():
                    # 文件类型筛选
                    if file_type and item.isfile:
                        file_ext = os.path.splitext(item.name)[1].lower().lstrip(".")
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
                            "docs": ["pdf", "doc", "docx", "txt", "rtf", "odt"],
                            "archive": ["zip", "rar", "7z", "tar", "gz", "bz2"],
                        }

                        if file_type in type_mapping:
                            if file_ext not in type_mapping[file_type]:
                                continue
                        elif file_ext != file_type:
                            continue

                    results.append(item)

            logger.info(f"搜索到 {len(results)} 个匹配的文件")
            return results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    def share(
        self,
        *fids: str,
        password: str = "",
        expire_days: int = 0,
        description: str = "",
    ) -> Any:
        """分享文件或目录

        注意: 通过ossutil生成预签名URL实现分享

        Args:
            fids: 要分享的文件或目录ID列表
            password: 分享密码（ossutil不支持）
            expire_days: 分享链接有效期(天)，0表示永久有效
            description: 分享描述

        Returns:
            dict: 分享链接信息
        """
        try:
            if not self._is_logged_in:
                logger.error("未登录OSS服务")
                return None

            if password:
                logger.warning("ossutil不支持密码保护的分享链接")

            share_links = []
            for fid in fids:
                if self.exist(fid):
                    # 构建OSS路径
                    oss_path = f"oss://{self._bucket_name}/{fid.lstrip('/')}"

                    # 使用sign命令生成预签名URL
                    if expire_days > 0:
                        expires = expire_days * 24 * 3600  # 转换为秒
                        result = self._run_ossutil_command(
                            ["sign", oss_path, "--timeout", str(expires)]
                        )
                    else:
                        # 默认1小时有效期
                        result = self._run_ossutil_command(["sign", oss_path])

                    if result.returncode == 0:
                        # 提取URL
                        url = result.stdout.strip()
                        share_links.append(
                            {
                                "fid": fid,
                                "url": url,
                                "expire_days": expire_days,
                                "description": description,
                            }
                        )
                    else:
                        logger.error(f"生成分享链接失败: {result.stderr}")
                else:
                    logger.warning(f"文件不存在，无法分享: {fid}")

            return {"links": share_links, "total": len(share_links)}

        except Exception as e:
            logger.error(f"分享失败: {e}")
            return None

    def get_quota(self, *args: Any, **kwargs: Any) -> dict:
        """获取网盘空间使用情况

        Returns:
            dict: 包含总空间、已用空间等信息的字典
        """
        try:
            if not self._is_logged_in:
                logger.error("未登录OSS服务")
                return {}

            # 使用du命令获取bucket使用情况
            oss_path = f"oss://{self._bucket_name}/"
            result = self._run_ossutil_command(["du", oss_path])

            if result.returncode != 0:
                logger.error(f"获取配额信息失败: {result.stderr}")
                return {}

            # 解析du输出
            lines = result.stdout.strip().split("\n")
            used_space = 0
            object_count = 0

            for line in lines:
                if "storage size:" in line.lower():
                    # 提取存储大小
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.lower() == "size:" and i + 1 < len(parts):
                            try:
                                used_space = int(parts[i + 1])
                            except ValueError:
                                pass
                elif "object count:" in line.lower():
                    # 提取对象数量
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.lower() == "count:" and i + 1 < len(parts):
                            try:
                                object_count = int(parts[i + 1])
                            except ValueError:
                                pass

            return {
                "total_space": -1,  # OSS没有总空间限制
                "used_space": used_space,
                "free_space": -1,  # 无限制
                "object_count": object_count,
                "bucket_name": self._bucket_name,
                "endpoint": self._endpoint,
            }

        except Exception as e:
            logger.error(f"获取配额信息失败: {e}")
            return {}

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
            if not self._is_logged_in:
                logger.error("未登录OSS服务")
                return False

            if not self.exist(source_fid):
                logger.error(f"源文件不存在: {source_fid}")
                return False

            # 构建源路径和目标路径
            source_oss_path = f"oss://{self._bucket_name}/{source_fid.lstrip('/')}"
            source_name = os.path.basename(source_fid.rstrip("/"))
            target_path = (
                os.path.join(target_fid, source_name).replace("\\", "/").lstrip("/")
            )
            target_oss_path = f"oss://{self._bucket_name}/{target_path}"

            # 使用cp命令复制，-r参数用于递归复制目录
            result = self._run_ossutil_command(
                ["cp", source_oss_path, target_oss_path, "-r"]
            )

            if result.returncode == 0:
                logger.success(f"复制成功: {source_fid} -> {target_path}")
                return True
            else:
                logger.error(f"复制失败: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"复制失败: {e}")
            return False

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
            # 先复制，再删除原文件
            if self.copy(source_fid, target_fid):
                return self.delete(source_fid)
            return False

        except Exception as e:
            logger.error(f"移动失败: {e}")
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
            if not self._is_logged_in:
                logger.error("未登录OSS服务")
                return False

            if not self.exist(fid):
                logger.error(f"文件或目录不存在: {fid}")
                return False

            # 构建新路径
            parent_dir = os.path.dirname(fid.rstrip("/"))
            new_path = os.path.join(parent_dir, new_name).replace("\\", "/")

            # 先复制到新位置，再删除原文件
            if self.copy(fid, parent_dir):
                # 删除原文件
                if self.delete(fid):
                    logger.success(f"重命名成功: {fid} -> {new_path}")
                    return True

            return False

        except Exception as e:
            logger.error(f"重命名失败: {e}")
            return False

    # ========== 以下方法ossutil不支持，提供警告实现 ==========

    def save_shared(
        self,
        shared_url: str,
        fid: str,
        password: Optional[str] = None,
    ) -> bool:
        """保存他人的分享内容到自己的网盘

        注意: ossutil不支持此功能

        Args:
            shared_url: 分享链接
            fid: 保存到的目标目录ID
            password: 分享密码

        Returns:
            bool: 保存是否成功
        """
        logger.warning("ossutil不支持保存分享内容功能")
        return False

    def get_recycle_list(self, *args: Any, **kwargs: Any) -> List[DriveFile]:
        """获取回收站文件列表

        ossutil不支持回收站功能
        """
        logger.warning("ossutil不支持回收站功能")
        return []

    def restore(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """从回收站恢复文件

        ossutil不支持回收站功能
        """
        logger.warning("ossutil不支持回收站功能")
        return False

    def clear_recycle(self, *args: Any, **kwargs: Any) -> bool:
        """清空回收站

        ossutil不支持回收站功能
        """
        logger.warning("ossutil不支持回收站功能")
        return False

    def get_download_url(self, fid: str, *args: Any, **kwargs: Any) -> str:
        """获取文件下载链接

        Args:
            fid: 文件ID

        Returns:
            str: 下载链接
        """
        try:
            if not self._is_logged_in:
                logger.error("未登录OSS服务")
                return ""

            if not self.exist(fid):
                logger.error(f"文件不存在: {fid}")
                return ""

            # 构建OSS路径
            oss_path = f"oss://{self._bucket_name}/{fid.lstrip('/')}"

            # 生成预签名URL，有效期1小时
            result = self._run_ossutil_command(["sign", oss_path])

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"获取下载链接失败: {result.stderr}")
                return ""

        except Exception as e:
            logger.error(f"获取下载链接失败: {e}")
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
            if not self._is_logged_in:
                logger.error("未登录OSS服务")
                return ""

            # 构建上传路径
            upload_path = os.path.join(fid, filename).replace("\\", "/").lstrip("/")
            oss_path = f"oss://{self._bucket_name}/{upload_path}"

            # 生成预签名上传URL，有效期1小时
            result = self._run_ossutil_command(["sign", oss_path, "--method", "PUT"])

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"获取上传链接失败: {result.stderr}")
                return ""

        except Exception as e:
            logger.error(f"获取上传链接失败: {e}")
            return ""
