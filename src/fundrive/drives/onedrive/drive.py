# 标准库导入
import os
from typing import List, Optional, Dict, Any

import requests
from funsecret import read_secret
from funutil import getLogger

from fundrive.core import BaseDrive, DriveFile

logger = getLogger("fundrive")


class OneDrive(BaseDrive):
    """
    OneDrive 网盘驱动实现

    基于 Microsoft Graph API 实现的网盘驱动
    官方文档: https://docs.microsoft.com/en-us/graph/api/resources/onedrive

    功能特点:
    - 支持文件和目录的基本操作
    - 支持大文件上传下载
    - 支持搜索和分享功能
    - 集成funsecret配置管理
    - 支持OAuth2认证流程
    """

    # Microsoft Graph API 基础URL
    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

    # OAuth2 授权端点
    OAUTH_BASE = "https://login.microsoftonline.com/common/oauth2/v2.0"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """
        初始化OneDrive驱动

        Args:
            client_id: OAuth2 客户端ID
            client_secret: OAuth2 客户端密钥
            access_token: 访问令牌
            refresh_token: 刷新令牌
        """
        super().__init__(*args, **kwargs)

        # 配置管理 - 优先使用传入参数，然后尝试从配置读取
        self.client_id = client_id or read_secret("fundrive", "onedrive", "client_id")
        self.client_secret = client_secret or read_secret(
            "fundrive", "onedrive", "client_secret"
        )
        self.access_token = access_token or read_secret(
            "fundrive", "onedrive", "access_token"
        )
        self.refresh_token = refresh_token or read_secret(
            "fundrive", "onedrive", "refresh_token"
        )

        self.session = requests.Session()
        self._user_info = None

        if not self.client_id or not self.client_secret:
            logger.warning("未找到 OneDrive 客户端凭据，请配置后使用")

    def login(self, *args, **kwargs) -> bool:
        """
        登录OneDrive服务

        Returns:
            bool: 登录是否成功
        """
        try:
            logger.info("开始OneDrive登录验证...")

            if not self.client_id or not self.client_secret:
                logger.error("缺少客户端凭据")
                return False

            # 如果有访问令牌，尝试验证
            if self.access_token:
                if self._validate_token():
                    logger.info("使用现有访问令牌登录成功")
                    return True

                # 尝试刷新令牌
                if self.refresh_token and self._refresh_access_token():
                    logger.info("令牌刷新成功")
                    return True

            # 需要重新授权
            logger.warning("需要重新进行OAuth2授权")
            logger.info("请访问以下URL进行授权:")
            auth_url = self._get_auth_url()
            logger.info(f"授权URL: {auth_url}")

            return False

        except Exception as e:
            logger.error(f"OneDrive登录失败: {e}")
            return False

    def _validate_token(self) -> bool:
        """验证访问令牌是否有效"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(f"{self.GRAPH_API_BASE}/me", headers=headers)

            if response.status_code == 200:
                self._user_info = response.json()
                return True
            return False
        except Exception:
            return False

    def _get_auth_url(self) -> str:
        """获取OAuth2授权URL"""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": "http://localhost:8080/callback",
            "scope": "Files.ReadWrite.All offline_access",
            "response_mode": "query",
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.OAUTH_BASE}/authorize?{query_string}"

    def _refresh_access_token(self) -> bool:
        """刷新访问令牌"""
        try:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            }

            response = self.session.post(f"{self.OAUTH_BASE}/token", data=data)

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                if "refresh_token" in token_data:
                    self.refresh_token = token_data["refresh_token"]
                return True
            return False
        except Exception:
            return False

    def exist(self, fid: str, *args, **kwargs) -> bool:
        """检查文件或目录是否存在"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}

            if fid == "root":
                url = f"{self.GRAPH_API_BASE}/me/drive/root"
            else:
                url = f"{self.GRAPH_API_BASE}/me/drive/items/{fid}"

            response = self.session.get(url, headers=headers)
            return response.status_code == 200

        except Exception as e:
            logger.error(f"检查文件存在性失败: {e}")
            return False

    def mkdir(self, parent_id: str, dirname: str, *args, **kwargs) -> str:
        """创建目录"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            data = {
                "name": dirname,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "rename",
            }

            if parent_id == "root":
                url = f"{self.GRAPH_API_BASE}/me/drive/root/children"
            else:
                url = f"{self.GRAPH_API_BASE}/me/drive/items/{parent_id}/children"

            response = self.session.post(url, headers=headers, json=data)

            if response.status_code == 201:
                result = response.json()
                logger.info(f"目录创建成功: {dirname}")
                return result["id"]
            else:
                logger.error(f"目录创建失败: {response.text}")
                return ""

        except Exception as e:
            logger.error(f"创建目录失败: {e}")
            return ""

    def delete(self, fid: str, *args, **kwargs) -> bool:
        """删除文件或目录"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            url = f"{self.GRAPH_API_BASE}/me/drive/items/{fid}"

            response = self.session.delete(url, headers=headers)

            if response.status_code == 204:
                logger.info("文件/目录删除成功")
                return True
            else:
                logger.error(f"删除失败: {response.text}")
                return False

        except Exception as e:
            logger.error(f"删除文件/目录失败: {e}")
            return False

    def get_file_list(self, fid: str = "root", *args, **kwargs) -> List[DriveFile]:
        """获取文件列表"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}

            if fid == "root":
                url = f"{self.GRAPH_API_BASE}/me/drive/root/children"
            else:
                url = f"{self.GRAPH_API_BASE}/me/drive/items/{fid}/children"

            response = self.session.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                files = []

                for item in data.get("value", []):
                    if "file" in item:  # 只返回文件，不包括文件夹
                        drive_file = DriveFile(
                            fid=item["id"],
                            name=item["name"],
                            size=item.get("size", 0),
                            ext={
                                "type": "file",
                                "create_time": item.get("createdDateTime", ""),
                                "update_time": item.get("lastModifiedDateTime", ""),
                            },
                        )
                        files.append(drive_file)

                return files
            else:
                logger.error(f"获取文件列表失败: {response.text}")
                return []

        except Exception as e:
            logger.error(f"获取文件列表失败: {e}")
            return []

    def get_dir_list(self, fid: str = "root", *args, **kwargs) -> List[DriveFile]:
        """获取目录列表"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}

            if fid == "root":
                url = f"{self.GRAPH_API_BASE}/me/drive/root/children"
            else:
                url = f"{self.GRAPH_API_BASE}/me/drive/items/{fid}/children"

            response = self.session.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                dirs = []

                for item in data.get("value", []):
                    if "folder" in item:  # 只返回文件夹
                        drive_file = DriveFile(
                            fid=item["id"],
                            name=item["name"],
                            size=item.get("size", 0),
                            ext={
                                "type": "dir",
                                "create_time": item.get("createdDateTime", ""),
                                "update_time": item.get("lastModifiedDateTime", ""),
                            },
                        )
                        dirs.append(drive_file)

                return dirs
            else:
                logger.error(f"获取目录列表失败: {response.text}")
                return []

        except Exception as e:
            logger.error(f"获取目录列表失败: {e}")
            return []

    def get_file_info(self, fid: str, *args, **kwargs) -> Optional[DriveFile]:
        """获取文件信息"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            url = f"{self.GRAPH_API_BASE}/me/drive/items/{fid}"

            response = self.session.get(url, headers=headers)

            if response.status_code == 200:
                item = response.json()

                if "file" in item:
                    return DriveFile(
                        fid=item["id"],
                        name=item["name"],
                        size=item.get("size", 0),
                        ext={
                            "type": "file",
                            "create_time": item.get("createdDateTime", ""),
                            "update_time": item.get("lastModifiedDateTime", ""),
                        },
                    )

            return None

        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return None

    def get_dir_info(self, fid: str, *args, **kwargs) -> Optional[DriveFile]:
        """获取目录信息"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            url = f"{self.GRAPH_API_BASE}/me/drive/items/{fid}"

            response = self.session.get(url, headers=headers)

            if response.status_code == 200:
                item = response.json()

                if "folder" in item:
                    return DriveFile(
                        fid=item["id"],
                        name=item["name"],
                        size=item.get("size", 0),
                        ext={
                            "type": "dir",
                            "create_time": item.get("createdDateTime", ""),
                            "update_time": item.get("lastModifiedDateTime", ""),
                        },
                    )

            return None

        except Exception as e:
            logger.error(f"获取目录信息失败: {e}")
            return None

    def upload_file(
        self,
        local_path: str,
        parent_id: str = "root",
        filename: Optional[str] = None,
        *args,
        **kwargs,
    ) -> bool:
        """上传文件"""
        try:
            if not os.path.exists(local_path):
                logger.error(f"本地文件不存在: {local_path}")
                return False

            filename = filename or os.path.basename(local_path)
            file_size = os.path.getsize(local_path)

            headers = {"Authorization": f"Bearer {self.access_token}"}

            # 小文件直接上传（< 4MB）
            if file_size < 4 * 1024 * 1024:
                return self._upload_small_file(local_path, parent_id, filename, headers)
            else:
                return self._upload_large_file(local_path, parent_id, filename, headers)

        except Exception as e:
            logger.error(f"上传文件失败: {e}")
            return False

    def _upload_small_file(
        self, local_path: str, parent_id: str, filename: str, headers: dict
    ) -> bool:
        """上传小文件"""
        try:
            if parent_id == "root":
                url = f"{self.GRAPH_API_BASE}/me/drive/root:/{filename}:/content"
            else:
                url = f"{self.GRAPH_API_BASE}/me/drive/items/{parent_id}:/{filename}:/content"

            with open(local_path, "rb") as f:
                response = self.session.put(url, headers=headers, data=f)

            if response.status_code in [200, 201]:
                logger.info(f"文件上传成功: {filename}")
                return True
            else:
                logger.error(f"文件上传失败: {response.text}")
                return False

        except Exception as e:
            logger.error(f"小文件上传失败: {e}")
            return False

    def _upload_large_file(
        self, local_path: str, parent_id: str, filename: str, headers: dict
    ) -> bool:
        """上传大文件（分块上传）"""
        try:
            # 创建上传会话
            if parent_id == "root":
                url = f"{self.GRAPH_API_BASE}/me/drive/root:/{filename}:/createUploadSession"
            else:
                url = f"{self.GRAPH_API_BASE}/me/drive/items/{parent_id}:/{filename}:/createUploadSession"

            session_data = {
                "item": {
                    "@microsoft.graph.conflictBehavior": "replace",
                    "name": filename,
                }
            }

            response = self.session.post(url, headers=headers, json=session_data)

            if response.status_code != 200:
                logger.error(f"创建上传会话失败: {response.text}")
                return False

            upload_url = response.json()["uploadUrl"]

            # 分块上传
            chunk_size = 320 * 1024  # 320KB chunks
            file_size = os.path.getsize(local_path)

            with open(local_path, "rb") as f:
                offset = 0
                while offset < file_size:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    chunk_headers = {
                        "Content-Length": str(len(chunk)),
                        "Content-Range": f"bytes {offset}-{offset + len(chunk) - 1}/{file_size}",
                    }

                    response = self.session.put(
                        upload_url, headers=chunk_headers, data=chunk
                    )

                    if response.status_code not in [202, 200, 201]:
                        logger.error(f"分块上传失败: {response.text}")
                        return False

                    offset += len(chunk)
                    progress = (offset / file_size) * 100
                    logger.info(f"上传进度: {progress:.1f}%")

            logger.info(f"大文件上传成功: {filename}")
            return True

        except Exception as e:
            logger.error(f"大文件上传失败: {e}")
            return False

    def download_file(
        self,
        fid: str,
        filedir: str = ".",
        filename: Optional[str] = None,
        *args,
        **kwargs,
    ) -> bool:
        """下载文件"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}

            # 获取文件信息
            file_info = self.get_file_info(fid)
            if not file_info:
                logger.error("获取文件信息失败")
                return False

            filename = filename or file_info.name
            local_path = os.path.join(filedir, filename)

            # 确保目录存在
            os.makedirs(filedir, exist_ok=True)

            # 获取下载URL
            url = f"{self.GRAPH_API_BASE}/me/drive/items/{fid}/content"

            response = self.session.get(url, headers=headers, stream=True)

            if response.status_code == 200:
                with open(local_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                logger.info(f"文件下载成功: {local_path}")
                return True
            else:
                logger.error(f"文件下载失败: {response.text}")
                return False

        except Exception as e:
            logger.error(f"下载文件失败: {e}")
            return False

    # 高级功能实现
    def search(self, keyword: str, fid: str = "root", **kwargs) -> List[DriveFile]:
        """搜索文件"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            url = f"{self.GRAPH_API_BASE}/me/drive/root/search(q='{keyword}')"

            response = self.session.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                results = []

                for item in data.get("value", []):
                    drive_file = DriveFile(
                        fid=item["id"],
                        name=item["name"],
                        size=item.get("size", 0),
                        ext={
                            "type": "file" if "file" in item else "dir",
                            "create_time": item.get("createdDateTime", ""),
                            "update_time": item.get("lastModifiedDateTime", ""),
                        },
                    )
                    results.append(drive_file)

                logger.info(f"搜索完成，找到 {len(results)} 个结果")
                return results
            else:
                logger.error(f"搜索失败: {response.text}")
                return []

        except Exception as e:
            logger.error(f"搜索文件失败: {e}")
            return []

    def share(self, fid: str, **kwargs) -> Optional[str]:
        """创建分享链接"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }

            data = {"type": "view", "scope": "anonymous"}

            url = f"{self.GRAPH_API_BASE}/me/drive/items/{fid}/createLink"

            response = self.session.post(url, headers=headers, json=data)

            if response.status_code == 200:
                result = response.json()
                share_url = result.get("link", {}).get("webUrl")
                logger.info("分享链接创建成功")
                return share_url
            else:
                logger.error(f"创建分享链接失败: {response.text}")
                return None

        except Exception as e:
            logger.error(f"创建分享链接失败: {e}")
            return None

    def get_quota(self, *args, **kwargs) -> Optional[Dict[str, Any]]:
        """获取存储配额信息"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            url = f"{self.GRAPH_API_BASE}/me/drive"

            response = self.session.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                quota = data.get("quota", {})

                total = quota.get("total", 0)
                used = quota.get("used", 0)
                available = total - used
                usage_percentage = (used / total * 100) if total > 0 else 0

                return {
                    "total": total,
                    "used": used,
                    "available": available,
                    "usage_percentage": usage_percentage,
                }
            else:
                logger.error(f"获取配额信息失败: {response.text}")
                return None

        except Exception as e:
            logger.error(f"获取存储配额失败: {e}")
            return None

    # 不支持的功能
    def get_recycle_list(self, *args, **kwargs):
        """获取回收站文件列表 - OneDrive API限制"""
        logger.warning("OneDrive 不支持通过API访问回收站功能")
        return []

    def restore(self, fid, *args, **kwargs):
        """恢复文件 - OneDrive API限制"""
        logger.warning("OneDrive 不支持通过API恢复文件功能")
        return False

    def clear_recycle(self, *args, **kwargs):
        """清空回收站 - OneDrive API限制"""
        logger.warning("OneDrive 不支持通过API清空回收站功能")
        return False

    def save_shared(self, shared_url, fid, *args, **kwargs):
        """保存分享文件 - 需要特殊权限"""
        logger.warning("OneDrive 保存分享文件功能需要特殊权限配置")
        return False
