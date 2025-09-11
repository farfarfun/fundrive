import os
import json
from typing import List, Optional, Any, Dict
from pathlib import Path

import requests

from fundrive.core import BaseDrive, DriveFile
from funget import simple_download
from funsecret import read_secret
from funutil import getLogger
from funutil.cache import cache

logger = getLogger("fundrive")


class ZenodoClient:
    """
    Zenodo API 客户端类

    基于 Zenodo REST API v1.0.0 实现的客户端
    API 文档: https://developers.zenodo.org/#rest-api

    支持的主要功能:
    - 存储库管理 (depositions)
    - 文件上传下载
    - 记录检索和搜索
    - 版本管理
    """

    code_list = {
        200: {
            "code": 200,
            "name": "OK",
            "desc": "Request succeeded. Response included. Usually sent for GET/PUT/PATCH requests.",
        },
        201: {
            "code": 201,
            "name": "Created",
            "desc": "Request succeeded. Response included. Usually sent for POST requests.",
        },
        202: {
            "code": 202,
            "name": "Accepted",
            "desc": "Request succeeded. Response included. Usually sent for POST requests, where background processing is needed to fulfill the request.",
        },
        204: {
            "code": 204,
            "name": "No Content",
            "desc": "Request succeeded. No response included. Usually sent for DELETE requests.",
        },
        400: {
            "code": 400,
            "name": "Bad Request",
            "desc": "Request failed. Error response included.",
        },
        401: {
            "code": 401,
            "name": "Unauthorized",
            "desc": "Request failed, due to an invalid access token. Error response included.",
        },
        403: {
            "code": 403,
            "name": "Forbidden",
            "desc": "Request failed, due to missing authorization (e.g. deleting an already submitted upload or missing scopes for your access token). Error response included.",
        },
        404: {
            "code": 404,
            "name": "Not Found",
            "desc": "Request failed, due to the resource not being found. Error response included.",
        },
        405: {
            "code": 405,
            "name": "Method Not Allowed",
            "desc": "Request failed, due to unsupported HTTP method. Error response included.",
        },
        409: {
            "code": 409,
            "name": "Conflict",
            "desc": "Request failed, due to the current state of the resource (e.g. edit a deopsition which is not fully integrated). Error response included.",
        },
        415: {
            "code": 415,
            "name": "Unsupported Media Type",
            "desc": "Request failed, due to missing or invalid request header Content-Type. Error response included.",
        },
        429: {
            "code": 429,
            "name": "Too Many Requests",
            "desc": "Request failed, due to rate limiting. Error response included.",
        },
        500: {
            "code": 500,
            "name": "Internal Server Error",
            "desc": "Request failed, due to an internal server error. Error response NOT included. Don’t worry, Zenodo admins have been notified and will be dealing with the problem ASAP.",
        },
    }

    def __init__(self, access_token: str, sandbox: bool = False):
        """
        初始化 Zenodo API 客户端

        Args:
            access_token (str): Zenodo API 访问令牌
            sandbox (bool): 是否使用沙盒环境，默认 False
        """
        if not access_token:
            raise ValueError("访问令牌不能为空")

        self.access_token = access_token
        self.base_url = (
            "https://sandbox.zenodo.org" if sandbox else "https://zenodo.org"
        )
        self.session = requests.Session()
        self.session.params = {"access_token": self.access_token}

    def _make_request(
        self, method: str, endpoint: str, params: Optional[Dict] = None, **kwargs
    ) -> requests.Response:
        """
        发起 API 请求

        Args:
            method (str): HTTP 方法
            endpoint (str): API 端点
            params (Optional[Dict]): 请求参数
            **kwargs: 其他请求参数

        Returns:
            requests.Response: HTTP 响应对象
        """
        url = (
            endpoint
            if endpoint.startswith("http")
            else f"{self.base_url}/api/{endpoint.lstrip('/')}"
        )

        # 合并参数
        request_params = {"access_token": self.access_token}
        if params:
            request_params.update(params)

        try:
            response = self.session.request(
                method, url, params=request_params, **kwargs
            )
            return response
        except requests.RequestException as e:
            logger.error(f"API 请求失败: {e}")
            raise

    def _check_response(
        self, response: requests.Response, expected_status: int, operation: str = ""
    ) -> bool:
        """
        检查 API 响应状态

        Args:
            response (requests.Response): HTTP 响应对象
            expected_status (int): 期望的状态码
            operation (str): 操作描述

        Returns:
            bool: 响应是否成功
        """
        if response.status_code == expected_status:
            return True

        error_info = self.code_list.get(
            response.status_code, {"name": "未知错误", "desc": "未知错误"}
        )

        try:
            error_msg = response.json().get("message", "无详细错误信息")
        except (ValueError, AttributeError):
            error_msg = response.text or "无错误信息"

        logger.error(
            f"{operation} 操作失败 - 状态码: {response.status_code} ({error_info['name']}) - "
            f"URL: {response.url} - 错误: {error_msg}"
        )
        return False

    def list_depositions(
        self,
        q: Optional[str] = None,
        status: Optional[str] = None,
        sort: Optional[str] = None,
        page: Optional[int] = None,
        size: Optional[int] = None,
        all_versions: Optional[bool] = None,
    ) -> tuple[bool, Dict[str, Any]]:
        """
        获取存储库列表

        Args:
            q (Optional[str]): 搜索查询（使用 Elasticsearch 查询语法）
            status (Optional[str]): 根据存储库状态过滤（draft 或 published）
            sort (Optional[str]): 排序方式（bestmatch 或 mostrecent）
            page (Optional[int]): 分页页码
            size (Optional[int]): 每页返回的结果数量
            all_versions (Optional[bool]): 是否显示所有版本

        Returns:
            tuple[bool, Dict[str, Any]]: (是否成功, 响应数据)
        """
        params = {}
        if q is not None:
            params["q"] = q
        if status is not None:
            params["status"] = status
        if sort is not None:
            params["sort"] = sort
        if page is not None:
            params["page"] = page
        if size is not None:
            params["size"] = size
        if all_versions is not None:
            params["all_versions"] = "1" if all_versions else "0"

        response = self._make_request("GET", "deposit/depositions", params=params)
        success = self._check_response(response, 200, "获取存储库列表")

        try:
            return success, response.json() if success else {}
        except ValueError:
            logger.error("解析响应 JSON 失败")
            return False, {}

    def create_deposition(
        self, metadata: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Dict[str, Any]]:
        """
        创建新的存储库

        Args:
            metadata (Optional[Dict[str, Any]]): 存储库元数据

        Returns:
            tuple[bool, Dict[str, Any]]: (是否成功, 响应数据)
        """
        data = {"metadata": metadata or {}}
        headers = {"Content-Type": "application/json"}

        response = self._make_request(
            "POST", "deposit/depositions", data=json.dumps(data), headers=headers
        )
        success = self._check_response(response, 201, "创建存储库")

        try:
            return success, response.json() if success else {}
        except ValueError:
            logger.error("解析响应 JSON 失败")
            return False, {}

    def get_deposition(self, deposition_id: str) -> tuple[bool, Dict[str, Any]]:
        """
        获取指定存储库信息

        Args:
            deposition_id (str): 存储库 ID

        Returns:
            tuple[bool, Dict[str, Any]]: (是否成功, 响应数据)
        """
        if not deposition_id:
            raise ValueError("存储库 ID 不能为空")

        response = self._make_request("GET", f"deposit/depositions/{deposition_id}")
        success = self._check_response(response, 200, "获取存储库信息")

        try:
            return success, response.json() if success else {}
        except ValueError:
            logger.error("解析响应 JSON 失败")
            return False, {}

    def update_deposition(
        self,
        deposition_id: str,
        title: str,
        description: str,
        upload_type: str = "dataset",
        creators: Optional[List[Dict[str, str]]] = None,
    ) -> tuple[bool, Dict[str, Any]]:
        """
        更新存储库元数据

        Args:
            deposition_id (str): 存储库 ID
            title (str): 标题
            description (str): 描述
            upload_type (str): 上传类型，默认为 "dataset"
            creators (Optional[List[Dict[str, str]]]): 创建者列表

        Returns:
            tuple[bool, Dict[str, Any]]: (是否成功, 响应数据)
        """
        if not deposition_id:
            raise ValueError("存储库 ID 不能为空")
        if not title:
            raise ValueError("标题不能为空")
        if not description:
            raise ValueError("描述不能为空")

        data = {
            "metadata": {
                "title": title,
                "upload_type": upload_type,
                "description": description,
                "creators": creators
                or [{"name": "fundrive", "affiliation": "fundrive"}],
            }
        }

        headers = {"Content-Type": "application/json"}
        response = self._make_request(
            "PUT",
            f"deposit/depositions/{deposition_id}",
            data=json.dumps(data),
            headers=headers,
        )
        success = self._check_response(response, 200, "更新存储库元数据")

        try:
            return success, response.json() if success else {}
        except ValueError:
            logger.error("解析响应 JSON 失败")
            return False, {}

    def delete_deposition(self, deposition_id: str) -> tuple[bool, Dict[str, Any]]:
        """
        删除存储库

        Args:
            deposition_id (str): 存储库 ID

        Returns:
            tuple[bool, Dict[str, Any]]: (是否成功, 响应数据)
        """
        if not deposition_id:
            raise ValueError("存储库 ID 不能为空")

        response = self._make_request("DELETE", f"deposit/depositions/{deposition_id}")
        success = self._check_response(response, 204, "删除存储库")

        try:
            return success, response.json() if success and response.text else {}
        except ValueError:
            return success, {}

    def list_deposition_files(
        self, deposition_id: str
    ) -> tuple[bool, List[Dict[str, Any]]]:
        """
        获取存储库文件列表

        Args:
            deposition_id (str): 存储库 ID

        Returns:
            tuple[bool, List[Dict[str, Any]]]: (是否成功, 文件列表)
        """
        if not deposition_id:
            raise ValueError("存储库 ID 不能为空")

        response = self._make_request(
            "GET", f"deposit/depositions/{deposition_id}/files"
        )
        success = self._check_response(response, 200, "获取存储库文件列表")

        try:
            return success, response.json() if success else []
        except ValueError:
            logger.error("解析响应 JSON 失败")
            return False, []

    def upload_file_to_deposition(
        self, deposition_id: str, file_path: str, filename: Optional[str] = None
    ) -> tuple[bool, Dict[str, Any]]:
        """
        上传文件到存储库

        Args:
            deposition_id (str): 存储库 ID
            file_path (str): 本地文件路径
            filename (Optional[str]): 文件名，默认使用本地文件名

        Returns:
            tuple[bool, Dict[str, Any]]: (是否成功, 响应数据)
        """
        if not deposition_id:
            raise ValueError("存储库 ID 不能为空")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        filename = filename or os.path.basename(file_path)

        # 获取存储库信息以获取 bucket URL
        success, deposition_info = self.get_deposition(deposition_id)
        if not success:
            logger.error(f"获取存储库信息失败: {deposition_id}")
            return False, {}

        bucket_url = deposition_info.get("links", {}).get("bucket")
        if not bucket_url:
            logger.error("未找到 bucket URL")
            return False, {}

        # 使用 bucket API 上传文件
        try:
            with open(file_path, "rb") as file_obj:
                response = self._make_request(
                    "PUT", f"{bucket_url}/{filename}", data=file_obj
                )
                success = self._check_response(response, 200, f"上传文件 {filename}")

                if success:
                    logger.info(f"文件上传成功: {filename} -> 存储库 {deposition_id}")

                try:
                    return success, response.json() if success else {}
                except ValueError:
                    return success, {}

        except Exception as e:
            logger.error(f"上传文件失败: {e}")
            return False, {}

    def delete_deposition_file(
        self, deposition_id: str, file_id: str
    ) -> tuple[bool, Dict[str, Any]]:
        """
        删除存储库中的文件

        Args:
            deposition_id (str): 存储库 ID
            file_id (str): 文件 ID

        Returns:
            tuple[bool, Dict[str, Any]]: (是否成功, 响应数据)
        """
        if not deposition_id:
            raise ValueError("存储库 ID 不能为空")
        if not file_id:
            raise ValueError("文件 ID 不能为空")

        response = self._make_request(
            "DELETE", f"deposit/depositions/{deposition_id}/files/{file_id}"
        )
        success = self._check_response(response, 204, "删除文件")

        try:
            return success, response.json() if success and response.text else {}
        except ValueError:
            return success, {}

    def publish_deposition(self, deposition_id: str) -> tuple[bool, Dict[str, Any]]:
        """
        发布存储库

        Args:
            deposition_id (str): 存储库 ID

        Returns:
            tuple[bool, Dict[str, Any]]: (是否成功, 响应数据)
        """
        if not deposition_id:
            raise ValueError("存储库 ID 不能为空")

        response = self._make_request(
            "POST", f"deposit/depositions/{deposition_id}/actions/publish"
        )
        success = self._check_response(response, 202, "发布存储库")

        try:
            return success, response.json() if success else {}
        except ValueError:
            logger.error("解析响应 JSON 失败")
            return False, {}

    def create_new_version(self, deposition_id: str) -> tuple[bool, Dict[str, Any]]:
        """
        为存储库创建新版本

        Args:
            deposition_id (str): 存储库 ID

        Returns:
            tuple[bool, Dict[str, Any]]: (是否成功, 新版本信息)
        """
        if not deposition_id:
            raise ValueError("存储库 ID 不能为空")

        response = self._make_request(
            "POST", f"deposit/depositions/{deposition_id}/actions/newversion"
        )
        success = self._check_response(response, 201, "创建新版本")

        try:
            return success, response.json() if success else {}
        except ValueError:
            logger.error("解析响应 JSON 失败")
            return False, {}

    def search_records(
        self,
        q: Optional[str] = None,
        status: Optional[str] = None,
        sort: Optional[str] = None,
        page: Optional[int] = None,
        size: Optional[int] = None,
        all_versions: Optional[bool] = None,
        communities: Optional[str] = None,
        type_filter: Optional[str] = None,
        subtype: Optional[str] = None,
    ) -> tuple[bool, Dict[str, Any]]:
        """
        搜索已发布的记录

        Args:
            q (Optional[str]): 搜索查询
            status (Optional[str]): 状态过滤
            sort (Optional[str]): 排序方式
            page (Optional[int]): 分页页码
            size (Optional[int]): 每页结果数
            all_versions (Optional[bool]): 是否显示所有版本
            communities (Optional[str]): 社区过滤
            type_filter (Optional[str]): 类型过滤
            subtype (Optional[str]): 子类型过滤

        Returns:
            tuple[bool, Dict[str, Any]]: (是否成功, 搜索结果)
        """
        params = {}
        if q is not None:
            params["q"] = q
        if status is not None:
            params["status"] = status
        if sort is not None:
            params["sort"] = sort
        if page is not None:
            params["page"] = page
        if size is not None:
            params["size"] = size
        if all_versions is not None:
            params["all_versions"] = "1" if all_versions else "0"
        if communities is not None:
            params["communities"] = communities
        if type_filter is not None:
            params["type"] = type_filter
        if subtype is not None:
            params["subtype"] = subtype

        response = self._make_request("GET", "records", params=params)
        success = self._check_response(response, 200, "搜索记录")

        try:
            return success, response.json() if success else {}
        except ValueError:
            logger.error("解析响应 JSON 失败")
            return False, {}

    def get_record(self, record_id: str) -> tuple[bool, Dict[str, Any]]:
        """
        获取已发布记录的详细信息

        Args:
            record_id (str): 记录 ID

        Returns:
            tuple[bool, Dict[str, Any]]: (是否成功, 记录信息)
        """
        if not record_id:
            raise ValueError("记录 ID 不能为空")

        response = self._make_request("GET", f"records/{record_id}")
        success = self._check_response(response, 200, "获取记录信息")

        try:
            return success, response.json() if success else {}
        except ValueError:
            logger.error("解析响应 JSON 失败")
            return False, {}

    def get_file_download_url(self, record_id: str, filename: str) -> Optional[str]:
        """
        获取文件下载链接

        Args:
            record_id (str): 记录 ID
            filename (str): 文件名

        Returns:
            Optional[str]: 下载链接，失败返回 None
        """
        success, record_info = self.get_record(record_id)
        if not success:
            return None

        files = record_info.get("files", [])
        for file_info in files:
            if file_info.get("key") == filename:
                return file_info.get("links", {}).get("self")

        logger.warning(f"在记录 {record_id} 中未找到文件 {filename}")
        return None


class ZenodoDrive(BaseDrive):
    """
    Zenodo 网盘驱动类

    基于 Zenodo REST API 实现的网盘操作类
    API 文档: https://developers.zenodo.org/#rest-api

    支持的主要功能:
    - 存储库管理 (创建、更新、删除、发布)
    - 文件上传下载
    - 记录搜索和检索
    - 版本管理
    """

    def __init__(self, sandbox: bool = False, *args: Any, **kwargs: Any):
        """
        初始化 Zenodo 驱动

        Args:
            sandbox (bool): 是否使用沙盒环境，默认 False
            *args: 位置参数
            **kwargs: 关键字参数
        """
        super().__init__(*args, **kwargs)
        self.access_token: Optional[str] = None
        self.sandbox = sandbox
        self.client: Optional[ZenodoClient] = None
        self._root_fid = "root"  # Zenodo 没有传统的目录结构，使用虚拟根目录

    def _ensure_client(self) -> bool:
        """
        确保客户端已初始化

        Returns:
            bool: 客户端是否可用
        """
        if not self.client:
            logger.error("客户端未初始化，请先调用 login() 方法")
            return False
        return True

    def login(
        self, access_token: Optional[str] = None, *args: Any, **kwargs: Any
    ) -> bool:
        """
        登录 Zenodo

        Args:
            access_token (Optional[str]): Zenodo API 访问令牌
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 登录是否成功
        """
        try:
            # 获取访问令牌
            self.access_token = access_token or read_secret(
                "fundrive", "zenodo", "access_token"
            )

            if not self.access_token:
                logger.error("未提供 Zenodo 访问令牌")
                return False

            # 初始化客户端
            self.client = ZenodoClient(self.access_token, sandbox=self.sandbox)

            # 测试连接
            success, _ = self.client.list_depositions(size=1)
            if success:
                self._is_logged_in = True
                logger.info("Zenodo 登录成功")
                return True
            else:
                logger.error("Zenodo 登录失败：API 测试请求失败")
                return False

        except Exception as e:
            logger.error(f"Zenodo 登录失败: {e}")
            return False

    def search(
        self,
        keyword: str,
        fid: Optional[str] = None,
        file_type: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> List[DriveFile]:
        """
        搜索文件或记录

        Args:
            keyword (str): 搜索关键词
            fid (Optional[str]): 搜索的起始目录ID（Zenodo中忽略此参数）
            file_type (Optional[str]): 文件类型筛选
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            List[DriveFile]: 符合条件的文件列表
        """
        if not self._ensure_client():
            return []

        try:
            # 构建搜索查询
            query = keyword
            if file_type:
                query += f" AND type:{file_type}"

            success, response = self.client.search_records(q=query, **kwargs)
            if not success:
                return []

            results = []
            hits = response.get("hits", {}).get("hits", [])

            for record in hits:
                # 为每个记录创建 DriveFile 对象
                record_id = str(record.get("id", ""))
                title = record.get("metadata", {}).get("title", "未知标题")

                results.append(
                    DriveFile(
                        fid=record_id,
                        name=title,
                        size=None,  # Zenodo 记录没有直接的大小信息
                        ext={
                            "record_type": "zenodo_record",
                            "doi": record.get("doi"),
                            "created": record.get("created"),
                            "modified": record.get("modified"),
                            "metadata": record.get("metadata", {}),
                        },
                    )
                )

            return results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    def get_dir_list(self, fid: str, *args: Any, **kwargs: Any) -> List[DriveFile]:
        """
        获取目录下的子目录列表

        注意：Zenodo 没有传统的目录结构，此方法返回用户的存储库列表

        Args:
            fid (str): 目录ID（对于根目录使用 "root"）
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            List[DriveFile]: 存储库列表
        """
        if not self._ensure_client():
            return []

        try:
            success, response = self.client.list_depositions(**kwargs)
            if not success:
                return []

            results = []
            for deposition in response:
                deposition_id = str(deposition.get("id", ""))
                title = deposition.get("title") or deposition.get("metadata", {}).get(
                    "title", "未命名存储库"
                )

                results.append(
                    DriveFile(
                        fid=deposition_id,
                        name=title,
                        size=None,
                        ext={
                            "record_type": "zenodo_deposition",
                            "state": deposition.get("state"),
                            "submitted": deposition.get("submitted"),
                            "created": deposition.get("created"),
                            "modified": deposition.get("modified"),
                        },
                    )
                )

            return results

        except Exception as e:
            logger.error(f"获取存储库列表失败: {e}")
            return []

    def get_file_info(self, fid: str, *args: Any, **kwargs: Any) -> Optional[DriveFile]:
        """
        获取文件详细信息

        Args:
            fid (str): 文件ID（格式：record_id/filename 或 deposition_id）
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Optional[DriveFile]: 文件信息对象
        """
        if not self._ensure_client():
            return None

        try:
            # 如果 fid 包含 "/"，则认为是 record_id/filename 格式
            if "/" in fid:
                record_id, filename = fid.split("/", 1)
                success, record_info = self.client.get_record(record_id)
                if not success:
                    return None

                files = record_info.get("files", [])
                for file_info in files:
                    if file_info.get("key") == filename:
                        return DriveFile(
                            fid=fid,
                            name=filename,
                            size=file_info.get("size"),
                            ext={
                                "record_type": "zenodo_file",
                                "checksum": file_info.get("checksum"),
                                "download_url": file_info.get("links", {}).get("self"),
                            },
                        )
            else:
                # 假设是存储库 ID
                success, deposition_info = self.client.get_deposition(fid)
                if success:
                    title = deposition_info.get("title") or deposition_info.get(
                        "metadata", {}
                    ).get("title", "未命名存储库")
                    return DriveFile(
                        fid=fid,
                        name=title,
                        size=None,
                        ext={
                            "record_type": "zenodo_deposition",
                            "state": deposition_info.get("state"),
                            "doi": deposition_info.get("doi"),
                        },
                    )

            return None

        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return None

    def get_file_list(self, fid: str, *args: Any, **kwargs: Any) -> List[DriveFile]:
        """
        获取目录下的文件列表

        Args:
            fid (str): 目录ID（存储库ID或记录ID）
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            List[DriveFile]: 文件列表
        """
        if not self._ensure_client():
            return []

        try:
            # 首先尝试作为已发布记录获取文件列表
            success, record_info = self.client.get_record(fid)
            if success:
                files = record_info.get("files", [])
                results = []

                for file_info in files:
                    filename = file_info.get("key", "")
                    file_fid = f"{fid}/{filename}"

                    results.append(
                        DriveFile(
                            fid=file_fid,
                            name=filename,
                            size=file_info.get("size"),
                            ext={
                                "record_type": "zenodo_file",
                                "checksum": file_info.get("checksum"),
                                "download_url": file_info.get("links", {}).get("self"),
                                "file_id": file_info.get("id"),
                            },
                        )
                    )

                return results

            # 如果不是已发布记录，尝试作为存储库获取文件列表
            success, files = self.client.list_deposition_files(fid)
            if success:
                results = []

                for file_info in files:
                    filename = file_info.get("filename", "")
                    file_fid = f"{fid}/{filename}"

                    results.append(
                        DriveFile(
                            fid=file_fid,
                            name=filename,
                            size=file_info.get("filesize"),
                            ext={
                                "record_type": "zenodo_deposition_file",
                                "file_id": file_info.get("id"),
                                "checksum": file_info.get("checksum"),
                            },
                        )
                    )

                return results

            return []

        except Exception as e:
            logger.error(f"获取文件列表失败: {e}")
            return []

    def download_file(
        self,
        fid: str,
        filedir: Optional[str] = None,
        filename: Optional[str] = None,
        filepath: Optional[str] = None,
        overwrite: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        下载单个文件

        Args:
            fid (str): 文件ID（格式：record_id/filename）
            filedir (Optional[str]): 文件保存目录
            filename (Optional[str]): 文件名
            filepath (Optional[str]): 完整的文件保存路径
            overwrite (bool): 是否覆盖已存在的文件
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 下载是否成功
        """
        if not self._ensure_client():
            return False

        try:
            # 解析文件ID
            if "/" not in fid:
                logger.error("文件ID格式错误，应为 record_id/filename")
                return False

            record_id, file_name = fid.split("/", 1)

            # 获取下载链接
            download_url = self.client.get_file_download_url(record_id, file_name)
            if not download_url:
                logger.error(f"无法获取文件下载链接: {fid}")
                return False

            # 确定保存路径
            if filepath:
                save_path = filepath
            elif filedir and filename:
                save_path = os.path.join(filedir, filename)
            elif filedir:
                save_path = os.path.join(filedir, file_name)
            else:
                save_path = file_name

            # 检查文件是否已存在
            if os.path.exists(save_path) and not overwrite:
                logger.warning(f"文件已存在且未设置覆盖: {save_path}")
                return False

            # 创建目录
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # 下载文件
            simple_download(url=download_url, filepath=save_path)
            logger.info(f"文件下载成功: {fid} -> {save_path}")
            return True

        except Exception as e:
            logger.error(f"下载文件失败: {e}")
            return False

    def download_dir(
        self,
        fid: str,
        filedir: str,
        recursion: bool = True,
        overwrite: bool = False,
        ignore_filter: Optional[Any] = None,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        下载目录（存储库或记录的所有文件）

        Args:
            fid (str): 目录ID（存储库ID或记录ID）
            filedir (str): 本地保存目录
            recursion (bool): 是否递归下载（Zenodo中忽略此参数）
            overwrite (bool): 是否覆盖已存在的文件
            ignore_filter: 忽略文件的过滤函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 下载是否成功
        """
        if not self._ensure_client():
            return False

        try:
            # 获取文件列表
            files = self.get_file_list(fid)
            if not files:
                logger.warning(f"目录中没有文件: {fid}")
                return True

            # 创建保存目录
            os.makedirs(filedir, exist_ok=True)

            success_count = 0
            for file_obj in files:
                if ignore_filter and ignore_filter(file_obj.name):
                    continue

                success = self.download_file(
                    fid=file_obj.fid,
                    filedir=filedir,
                    filename=file_obj.name,
                    overwrite=overwrite,
                    *args,
                    **kwargs,
                )

                if success:
                    success_count += 1

            logger.info(f"目录下载完成: {success_count}/{len(files)} 个文件成功")
            return success_count > 0

        except Exception as e:
            logger.error(f"下载目录失败: {e}")
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
        创建目录（在Zenodo中创建新的存储库）

        Args:
            fid (str): 父目录ID（Zenodo中忽略此参数）
            name (str): 目录名称（存储库标题）
            return_if_exist (bool): 如果目录已存在，是否返回已存在目录的ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            str: 创建的存储库ID
        """
        if not self._ensure_client():
            raise RuntimeError("客户端未初始化")

        try:
            # 创建新的存储库
            metadata = {
                "title": name,
                "upload_type": "dataset",
                "description": f"通过 fundrive 创建的存储库: {name}",
                "creators": [{"name": "fundrive", "affiliation": "fundrive"}],
            }

            success, response = self.client.create_deposition(metadata)
            if success:
                deposition_id = str(response.get("id", ""))
                logger.info(f"存储库创建成功: {name} (ID: {deposition_id})")
                return deposition_id
            else:
                raise RuntimeError("创建存储库失败")

        except Exception as e:
            logger.error(f"创建目录失败: {e}")
            raise

    def upload_dir(
        self,
        filedir: str,
        fid: str,
        recursion: bool = True,
        overwrite: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        上传目录到存储库

        Args:
            filedir (str): 本地目录路径
            fid (str): 目标存储库ID
            recursion (bool): 是否递归上传子目录
            overwrite (bool): 是否覆盖已存在的文件
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 上传是否成功
        """
        if not self._ensure_client():
            return False

        if not os.path.exists(filedir):
            logger.error(f"本地目录不存在: {filedir}")
            return False

        try:
            success_count = 0
            total_count = 0

            for root, dirs, files in os.walk(filedir):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    total_count += 1

                    # 计算相对路径作为上传后的文件名
                    rel_path = os.path.relpath(file_path, filedir)
                    upload_filename = rel_path.replace(os.sep, "/")  # 使用 / 作为分隔符

                    success = self.upload_file(file_path, fid, filename=upload_filename)
                    if success:
                        success_count += 1

                # 如果不递归，只处理第一层
                if not recursion:
                    break

            logger.info(f"目录上传完成: {success_count}/{total_count} 个文件成功")
            return success_count > 0

        except Exception as e:
            logger.error(f"上传目录失败: {e}")
            return False

    def upload_file(
        self,
        filedir: str,
        fid: str,
        filename: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        上传单个文件到存储库

        Args:
            filedir (str): 本地文件路径
            fid (str): 目标存储库ID
            filename (Optional[str]): 上传后的文件名，默认使用本地文件名
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 上传是否成功
        """
        if not self._ensure_client():
            return False

        if not os.path.exists(filedir):
            logger.error(f"本地文件不存在: {filedir}")
            return False

        try:
            upload_filename = filename or os.path.basename(filedir)
            success, _ = self.client.upload_file_to_deposition(
                fid, filedir, upload_filename
            )

            if success:
                logger.info(f"文件上传成功: {filedir} -> 存储库 {fid}")
            else:
                logger.error(f"文件上传失败: {filedir}")

            return success

        except Exception as e:
            logger.error(f"上传文件失败: {e}")
            return False

    def exist(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        检查文件或目录是否存在

        Args:
            fid (str): 文件或目录ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 是否存在
        """
        if not self._ensure_client():
            return False

        try:
            # 如果包含 "/"，认为是文件ID
            if "/" in fid:
                record_id, filename = fid.split("/", 1)
                success, record_info = self.client.get_record(record_id)
                if not success:
                    return False

                files = record_info.get("files", [])
                return any(f.get("key") == filename for f in files)
            else:
                # 检查是否为存储库或记录
                success, _ = self.client.get_deposition(fid)
                if success:
                    return True

                success, _ = self.client.get_record(fid)
                return success

        except Exception as e:
            logger.error(f"检查文件存在性失败: {e}")
            return False

    def delete(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """
        删除文件或目录

        Args:
            fid (str): 文件或目录ID
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 删除是否成功
        """
        if not self._ensure_client():
            return False

        try:
            # 如果包含 "/"，认为是文件ID
            if "/" in fid:
                deposition_id, filename = fid.split("/", 1)

                # 获取存储库文件列表找到文件ID
                success, files = self.client.list_deposition_files(deposition_id)
                if not success:
                    return False

                file_id = None
                for file_info in files:
                    if file_info.get("filename") == filename:
                        file_id = file_info.get("id")
                        break

                if not file_id:
                    logger.error(f"未找到文件: {filename}")
                    return False

                success, _ = self.client.delete_deposition_file(deposition_id, file_id)
                if success:
                    logger.info(f"文件删除成功: {fid}")
                return success
            else:
                # 删除存储库
                success, _ = self.client.delete_deposition(fid)
                if success:
                    logger.info(f"存储库删除成功: {fid}")
                return success

        except Exception as e:
            logger.error(f"删除失败: {e}")
            return False

    def get_quota(self, *args: Any, **kwargs: Any) -> dict:
        """
        获取网盘空间使用情况

        注意：Zenodo API 不提供配额信息，返回空字典

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            dict: 空字典（Zenodo 不支持配额查询）
        """
        logger.warning("Zenodo API 不支持配额查询")
        return {}

    def rename(self, fid: str, new_name: str, *args: Any, **kwargs: Any) -> bool:
        """
        重命名文件或目录

        注意：Zenodo 不支持直接重命名文件，只能更新存储库元数据

        Args:
            fid (str): 文件/目录ID
            new_name (str): 新名称
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            bool: 重命名是否成功
        """
        if not self._ensure_client():
            return False

        try:
            # 只支持重命名存储库（更新标题）
            if "/" in fid:
                logger.error("Zenodo 不支持重命名单个文件")
                return False

            # 获取当前存储库信息
            success, deposition_info = self.client.get_deposition(fid)
            if not success:
                return False

            current_metadata = deposition_info.get("metadata", {})
            description = current_metadata.get("description", "")
            upload_type = current_metadata.get("upload_type", "dataset")
            creators = current_metadata.get("creators", [])

            # 更新标题
            success, _ = self.client.update_deposition(
                fid, new_name, description, upload_type, creators
            )

            if success:
                logger.info(f"存储库重命名成功: {fid} -> {new_name}")
            return success

        except Exception as e:
            logger.error(f"重命名失败: {e}")
            return False

    def publish_deposition(
        self,
        deposition_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        """
        发布存储库

        Args:
            deposition_id (str): 存储库ID
            title (Optional[str]): 标题
            description (Optional[str]): 描述

        Returns:
            bool: 发布是否成功
        """
        if not self._ensure_client():
            return False

        try:
            # 如果提供了元数据，先更新
            if title or description:
                success, deposition_info = self.client.get_deposition(deposition_id)
                if not success:
                    return False

                current_metadata = deposition_info.get("metadata", {})
                final_title = title or current_metadata.get("title", "未命名存储库")
                final_description = description or current_metadata.get(
                    "description", "无描述"
                )
                upload_type = current_metadata.get("upload_type", "dataset")
                creators = current_metadata.get("creators", [])

                success, _ = self.client.update_deposition(
                    deposition_id, final_title, final_description, upload_type, creators
                )
                if not success:
                    logger.error("更新存储库元数据失败")
                    return False

            # 发布存储库
            success, response = self.client.publish_deposition(deposition_id)
            if success:
                doi = response.get("doi", "")
                logger.info(f"存储库发布成功: {deposition_id} (DOI: {doi})")
            return success

        except Exception as e:
            logger.error(f"发布存储库失败: {e}")
            return False

    # 以下方法在 Zenodo 中不适用，提供空实现
    def move(self, source_fid: str, target_fid: str, *args: Any, **kwargs: Any) -> bool:
        """Zenodo 不支持移动操作"""
        logger.warning("Zenodo 不支持移动操作")
        return False

    def copy(self, source_fid: str, target_fid: str, *args: Any, **kwargs: Any) -> bool:
        """Zenodo 不支持复制操作"""
        logger.warning("Zenodo 不支持复制操作")
        return False

    def share(
        self,
        *fids: str,
        password: str = "",
        expire_days: int = 0,
        description: str = "",
    ) -> Any:
        """Zenodo 记录发布后自动公开分享"""
        logger.info("Zenodo 记录发布后自动获得 DOI 和公开访问链接")
        return None

    def get_download_url(self, fid: str, *args: Any, **kwargs: Any) -> str:
        """
        获取文件下载链接

        Args:
            fid (str): 文件ID（格式：record_id/filename）

        Returns:
            str: 下载链接
        """
        if not self._ensure_client():
            return ""

        if "/" not in fid:
            logger.error("文件ID格式错误，应为 record_id/filename")
            return ""

        record_id, filename = fid.split("/", 1)
        download_url = self.client.get_file_download_url(record_id, filename)
        return download_url or ""

    def get_upload_url(self, fid: str, filename: str, *args: Any, **kwargs: Any) -> str:
        """Zenodo 使用 bucket API 上传，不提供预签名URL"""
        logger.warning("Zenodo 不支持预签名上传URL")
        return ""

    def get_dir_info(self, fid: str, *args: Any, **kwargs: Any) -> Optional[DriveFile]:
        """获取目录信息（等同于获取存储库信息）"""
        return self.get_file_info(fid, *args, **kwargs)

    def get_recycle_list(self, *args: Any, **kwargs: Any) -> List[DriveFile]:
        """Zenodo 不支持回收站功能"""
        logger.warning("Zenodo 不支持回收站功能")
        return []

    def restore(self, fid: str, *args: Any, **kwargs: Any) -> bool:
        """Zenodo 不支持回收站恢复功能"""
        logger.warning("Zenodo 不支持回收站恢复功能")
        return False

    def clear_recycle(self, *args: Any, **kwargs: Any) -> bool:
        """Zenodo 不支持回收站清空功能"""
        logger.warning("Zenodo 不支持回收站清空功能")
        return False

    def save_shared(
        self, shared_url: str, fid: str, password: Optional[str] = None
    ) -> bool:
        """Zenodo 不支持保存分享内容功能"""
        logger.warning("Zenodo 不支持保存分享内容功能")
        return False
