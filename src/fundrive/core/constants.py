#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FunDrive项目常量定义模块

统一管理项目中使用的各种常量，包括：
- 默认配置值
- API端点URL
- 文件大小限制
- 超时设置
- 错误代码等

作者: FunDrive Team
"""

# 标准库导入
from typing import Dict, Any

# 通用配置常量
DEFAULT_TIMEOUT = 30  # 默认请求超时时间（秒）
DEFAULT_CHUNK_SIZE = 8192  # 默认分块大小（字节）
DEFAULT_MAX_RETRIES = 3  # 默认最大重试次数
DEFAULT_RETRY_DELAY = 1.0  # 默认重试延迟（秒）

# 文件大小限制常量
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 最大文件大小 10GB
MIN_FILE_SIZE = 1  # 最小文件大小 1字节
LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 大文件阈值 100MB

# 分块上传/下载常量
DEFAULT_UPLOAD_CHUNK_SIZE = 4 * 1024 * 1024  # 默认上传分块大小 4MB
DEFAULT_DOWNLOAD_CHUNK_SIZE = 1024 * 1024  # 默认下载分块大小 1MB
MAX_CONCURRENT_UPLOADS = 5  # 最大并发上传数
MAX_CONCURRENT_DOWNLOADS = 10  # 最大并发下载数

# 缓存配置常量
DEFAULT_CACHE_SIZE = 1000  # 默认缓存大小
DEFAULT_CACHE_TTL = 3600  # 默认缓存过期时间（秒）
DEFAULT_CACHE_CLEANUP_INTERVAL = 300  # 缓存清理间隔（秒）

# 连接池配置常量
DEFAULT_POOL_SIZE = 10  # 默认连接池大小
DEFAULT_POOL_MAX_SIZE = 20  # 连接池最大大小
DEFAULT_POOL_TIMEOUT = 30  # 连接池超时时间

# 速率限制常量
DEFAULT_RATE_LIMIT = 100  # 默认速率限制（请求/分钟）
DEFAULT_RATE_WINDOW = 60  # 速率限制时间窗口（秒）

# 日志配置常量
DEFAULT_LOG_LEVEL = "INFO"  # 默认日志级别
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 最大日志文件大小 10MB

# 文件名和路径常量
MAX_FILENAME_LENGTH = 255  # 最大文件名长度
MAX_PATH_LENGTH = 4096  # 最大路径长度
INVALID_FILENAME_CHARS = '<>:"/\\|?*'  # 无效文件名字符

# 支持的文件类型常量
SUPPORTED_FILE_TYPES = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
    "video": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
    "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"],
    "document": [".pdf", ".docs", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"],
    "archive": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".go", ".rs"],
}

# API端点常量
API_ENDPOINTS = {
    "baidu": "https://pan.baidu.com/api/",
    "alipan": "https://api.alipan.com/",
    "google": "https://www.googleapis.com/drive/v3/",
    "onedrive": "https://graph.microsoft.com/v1.0/",
    "dropbox": "https://api.dropboxapi.com/2/",
    "github": "https://api.github.com/",
    "gitee": "https://gitee.com/api/v5/",
}

# 环境变量常量
ENV_VARS = {
    "FUNDRIVE_LOG_LEVEL": "FUNDRIVE_LOG_LEVEL",
    "FUNDRIVE_CACHE_DIR": "FUNDRIVE_CACHE_DIR",
    "FUNDRIVE_CONFIG_DIR": "FUNDRIVE_CONFIG_DIR",
    "FUNDRIVE_TIMEOUT": "FUNDRIVE_TIMEOUT",
    "FUNDRIVE_MAX_RETRIES": "FUNDRIVE_MAX_RETRIES",
    "BAIDU_ACCESS_TOKEN": "BAIDU_ACCESS_TOKEN",
    "GOOGLE_CREDENTIALS": "GOOGLE_CREDENTIALS",
    "ONEDRIVE_CLIENT_ID": "ONEDRIVE_CLIENT_ID",
    "DROPBOX_ACCESS_TOKEN": "DROPBOX_ACCESS_TOKEN",
    "GITHUB_TOKEN": "GITHUB_TOKEN",
    "GITEE_TOKEN": "GITEE_TOKEN",
}

# HTTP状态码常量
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_NO_CONTENT = 204
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409
HTTP_TOO_MANY_REQUESTS = 429
HTTP_INTERNAL_SERVER_ERROR = 500

# 错误代码常量
ERROR_CODES = {
    "AUTHENTICATION_FAILED": "E001",
    "AUTHORIZATION_FAILED": "E002",
    "NETWORK_ERROR": "E003",
    "RATE_LIMIT_EXCEEDED": "E004",
    "FILE_NOT_FOUND": "E005",
    "FILE_EXISTS": "E006",
    "INSUFFICIENT_STORAGE": "E007",
    "INVALID_PARAMETER": "E008",
    "OPERATION_NOT_SUPPORTED": "E009",
    "UPLOAD_FAILED": "E010",
    "DOWNLOAD_FAILED": "E011",
}

# 驱动类型常量
DRIVE_TYPES = {
    # 全球主流服务
    "GOOGLE": "google",
    "ONEDRIVE": "onedrive",
    "DROPBOX": "dropbox",
    "AMAZON_S3": "amazon",
    # 代码托管平台
    "GITHUB": "github",
    "GITEE": "gitee",
    # 国内主流服务
    "BAIDU": "baidu",
    "ALIPAN": "alipan",
    "ALIPAN_OPEN": "alipan_open",
    "OSS": "oss",
    # 通用协议和工具
    "WEBDAV": "webdav",
    "PCLOUD": "pcloud",
    "MEDIAFIRE": "mediafire",
    "LANZOU": "lanzou",
    "LOCAL": "local",
    # 学术和专业服务
    "ZENODO": "zenodo",
    "TSINGHUA": "tsinghua",
    "OPENXLAB": "openxlab",
    "TIANCHI": "tianchi",
    "WENSHUSHU": "wenshushu",
}

# API端点配置
API_ENDPOINTS = {
    "mediafire": {
        "base_url": "https://www.mediafire.com/api/1.5/",
        "upload": "upload/upload.php",
        "download": "file/get_info.php",
        "folder_create": "folder/create.php",
        "folder_content": "folder/get_content.php",
    },
    "github": {
        "base_url": "https://api.github.com",
        "repos": "/repos/{owner}/{repo}",
        "contents": "/repos/{owner}/{repo}/contents/{path}",
    },
    "wenshushu": {
        "base_url": "https://www.wenshushu.cn",
        "login": "/ap/login/anonymous",
        "storage": "/ap/user/storage",
        "userinfo": "/ap/user/userinfo",
        "upload": "/ap/uploadv2/getupid",
    },
}

# 默认配置模板
DEFAULT_CONFIG: Dict[str, Any] = {
    "timeout": DEFAULT_TIMEOUT,
    "chunk_size": DEFAULT_CHUNK_SIZE,
    "max_retries": DEFAULT_MAX_RETRIES,
    "retry_delay": DEFAULT_RETRY_DELAY,
    "cache_size": DEFAULT_CACHE_SIZE,
    "cache_ttl": DEFAULT_CACHE_TTL,
    "pool_size": DEFAULT_POOL_SIZE,
    "rate_limit": DEFAULT_RATE_LIMIT,
    "log_level": DEFAULT_LOG_LEVEL,
}

# 文件类型映射
FILE_TYPE_MAPPING = {
    # 文档类型
    ".pdf": "document",
    ".docs": "document",
    ".docx": "document",
    ".txt": "document",
    ".md": "document",
    # 图片类型
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".gif": "image",
    ".bmp": "image",
    ".svg": "image",
    # 视频类型
    ".mp4": "video",
    ".avi": "video",
    ".mkv": "video",
    ".mov": "video",
    ".wmv": "video",
    # 音频类型
    ".mp3": "audio",
    ".wav": "audio",
    ".flac": "audio",
    ".aac": "audio",
    # 压缩文件
    ".zip": "archive",
    ".rar": "archive",
    ".7z": "archive",
    ".tar": "archive",
    ".gz": "archive",
    # 代码文件
    ".py": "code",
    ".js": "code",
    ".html": "code",
    ".css": "code",
    ".java": "code",
    ".cpp": "code",
    ".c": "code",
}

# 环境变量名称常量
ENV_VARS = {
    "AWS_ACCESS_KEY_ID": "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY": "AWS_SECRET_ACCESS_KEY",
    "AWS_DEFAULT_REGION": "AWS_DEFAULT_REGION",
    "GITHUB_TOKEN": "GITHUB_TOKEN",
    "GOOGLE_APPLICATION_CREDENTIALS": "GOOGLE_APPLICATION_CREDENTIALS",
    "FUNDRIVE_LOG_LEVEL": "FUNDRIVE_LOG_LEVEL",
    "FUNDRIVE_CACHE_DIR": "FUNDRIVE_CACHE_DIR",
}
