"""
FunDrive 工具类模块

提供缓存、连接池、性能优化等工具功能
"""

import functools
import hashlib
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Union
from collections import OrderedDict
from funutil import getLogger

logger = getLogger("fundrive.utils")


class LRUCache:
    """
    线程安全的LRU缓存实现

    用于缓存API响应、文件信息等数据，提高性能
    """

    def __init__(self, max_size: int = 1000, ttl: Optional[int] = None):
        """
        初始化LRU缓存

        Args:
            max_size (int): 最大缓存条目数
            ttl (Optional[int]): 缓存生存时间（秒），None表示永不过期
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache = OrderedDict()
        self._timestamps = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Any:
        """
        获取缓存值

        Args:
            key (str): 缓存键

        Returns:
            Any: 缓存值，不存在或已过期返回None
        """
        with self._lock:
            if key not in self._cache:
                return None

            # 检查TTL
            if self.ttl and key in self._timestamps:
                if time.time() - self._timestamps[key] > self.ttl:
                    self._remove(key)
                    return None

            # 移动到末尾（最近使用）
            value = self._cache.pop(key)
            self._cache[key] = value
            return value

    def put(self, key: str, value: Any) -> None:
        """
        设置缓存值

        Args:
            key (str): 缓存键
            value (Any): 缓存值
        """
        with self._lock:
            if key in self._cache:
                # 更新现有值
                self._cache.pop(key)
            elif len(self._cache) >= self.max_size:
                # 移除最久未使用的项
                oldest_key = next(iter(self._cache))
                self._remove(oldest_key)

            self._cache[key] = value
            if self.ttl:
                self._timestamps[key] = time.time()

    def _remove(self, key: str) -> None:
        """移除缓存项"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()

    def size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)

    def stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            expired_count = 0
            if self.ttl:
                current_time = time.time()
                expired_count = sum(
                    1
                    for timestamp in self._timestamps.values()
                    if current_time - timestamp > self.ttl
                )

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "expired_count": expired_count,
                "ttl": self.ttl,
            }


def cache_result(
    max_size: int = 100, ttl: Optional[int] = 300, key_func: Optional[Callable] = None
) -> Callable:
    """
    结果缓存装饰器

    Args:
        max_size (int): 最大缓存条目数
        ttl (Optional[int]): 缓存生存时间（秒）
        key_func (Optional[Callable]): 自定义键生成函数

    Returns:
        Callable: 装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        cache = LRUCache(max_size=max_size, ttl=ttl)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认键生成策略
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()

            # 尝试从缓存获取
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"缓存命中: {func.__name__}")
                return result

            # 执行函数并缓存结果
            logger.debug(f"缓存未命中，执行函数: {func.__name__}")
            result = func(*args, **kwargs)
            cache.put(cache_key, result)
            return result

        # 添加缓存管理方法
        wrapper.cache_clear = cache.clear
        wrapper.cache_stats = cache.stats
        wrapper.cache_size = cache.size

        return wrapper

    return decorator


class ConnectionPool:
    """
    简单的连接池实现

    用于管理HTTP连接、数据库连接等资源
    """

    def __init__(self, factory: Callable, max_size: int = 10, timeout: float = 30.0):
        """
        初始化连接池

        Args:
            factory (Callable): 连接创建工厂函数
            max_size (int): 最大连接数
            timeout (float): 连接超时时间（秒）
        """
        self.factory = factory
        self.max_size = max_size
        self.timeout = timeout
        self._pool = []
        self._in_use = set()
        self._lock = threading.RLock()
        self._created_count = 0

    def get_connection(self):
        """
        获取连接

        Returns:
            Any: 连接对象
        """
        with self._lock:
            # 尝试从池中获取空闲连接
            if self._pool:
                conn = self._pool.pop()
                self._in_use.add(conn)
                logger.debug(f"从连接池获取连接，池中剩余: {len(self._pool)}")
                return conn

            # 如果池为空且未达到最大连接数，创建新连接
            if self._created_count < self.max_size:
                conn = self.factory()
                self._in_use.add(conn)
                self._created_count += 1
                logger.debug(f"创建新连接，总连接数: {self._created_count}")
                return conn

            # 连接池已满，等待或抛出异常
            raise RuntimeError(f"连接池已满，最大连接数: {self.max_size}")

    def return_connection(self, conn) -> None:
        """
        归还连接到池中

        Args:
            conn: 连接对象
        """
        with self._lock:
            if conn in self._in_use:
                self._in_use.remove(conn)
                self._pool.append(conn)
                logger.debug(f"连接归还到池中，池中连接数: {len(self._pool)}")

    def close_all(self) -> None:
        """关闭所有连接"""
        with self._lock:
            # 关闭池中的连接
            for conn in self._pool:
                if hasattr(conn, "close"):
                    try:
                        conn.close()
                    except Exception as e:
                        logger.warning(f"关闭连接时出错: {e}")

            # 清空池
            self._pool.clear()
            self._in_use.clear()
            self._created_count = 0
            logger.info("所有连接已关闭")

    def stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        with self._lock:
            return {
                "pool_size": len(self._pool),
                "in_use": len(self._in_use),
                "total_created": self._created_count,
                "max_size": self.max_size,
            }


class RateLimiter:
    """
    速率限制器

    用于控制API调用频率，避免触发服务端限制
    """

    def __init__(self, max_calls: int, time_window: float = 60.0):
        """
        初始化速率限制器

        Args:
            max_calls (int): 时间窗口内最大调用次数
            time_window (float): 时间窗口大小（秒）
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self._calls = []
        self._lock = threading.RLock()

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        获取调用许可

        Args:
            timeout (Optional[float]): 超时时间（秒），None表示无限等待

        Returns:
            bool: 是否成功获取许可
        """
        start_time = time.time()

        while True:
            with self._lock:
                current_time = time.time()

                # 清理过期的调用记录
                self._calls = [
                    call_time
                    for call_time in self._calls
                    if current_time - call_time < self.time_window
                ]

                # 检查是否可以调用
                if len(self._calls) < self.max_calls:
                    self._calls.append(current_time)
                    return True

                # 检查超时
                if timeout is not None and current_time - start_time >= timeout:
                    return False

            # 等待一小段时间后重试
            time.sleep(0.1)

    def stats(self) -> Dict[str, Any]:
        """获取速率限制器统计信息"""
        with self._lock:
            current_time = time.time()
            active_calls = [
                call_time
                for call_time in self._calls
                if current_time - call_time < self.time_window
            ]

            return {
                "active_calls": len(active_calls),
                "max_calls": self.max_calls,
                "time_window": self.time_window,
                "remaining": max(0, self.max_calls - len(active_calls)),
            }


def rate_limit(max_calls: int, time_window: float = 60.0) -> Callable:
    """
    速率限制装饰器

    Args:
        max_calls (int): 时间窗口内最大调用次数
        time_window (float): 时间窗口大小（秒）

    Returns:
        Callable: 装饰器函数
    """
    limiter = RateLimiter(max_calls, time_window)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not limiter.acquire(timeout=30.0):
                from .exceptions import RateLimitError

                raise RateLimitError(f"函数 {func.__name__} 调用频率超限")

            return func(*args, **kwargs)

        # 添加速率限制器管理方法
        wrapper.rate_limiter = limiter
        wrapper.rate_stats = limiter.stats

        return wrapper

    return decorator


def format_size(size_bytes: Union[int, float]) -> str:
    """
    格式化文件大小

    Args:
        size_bytes (Union[int, float]): 文件大小（字节）

    Returns:
        str: 格式化后的大小字符串
    """
    if size_bytes is None:
        return "未知"

    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"


def parse_size(size_str: str) -> int:
    """
    解析大小字符串为字节数

    Args:
        size_str (str): 大小字符串，如 "1.5GB"

    Returns:
        int: 字节数

    Raises:
        ValueError: 无效的大小格式
    """
    size_str = size_str.strip().upper()

    units = {
        "B": 1,
        "KB": 1024,
        "MB": 1024**2,
        "GB": 1024**3,
        "TB": 1024**4,
        "PB": 1024**5,
    }

    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            try:
                number = float(size_str[: -len(unit)])
                return int(number * multiplier)
            except ValueError:
                break

    # 尝试解析纯数字
    try:
        return int(float(size_str))
    except ValueError:
        raise ValueError(f"无效的大小格式: {size_str}")


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除或替换非法字符

    Args:
        filename (str): 原始文件名

    Returns:
        str: 清理后的文件名
    """
    import re

    # 移除或替换非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    filename = re.sub(illegal_chars, "_", filename)

    # 移除控制字符
    filename = "".join(char for char in filename if ord(char) >= 32)

    # 移除首尾空格和点
    filename = filename.strip(" .")

    # 确保文件名不为空
    if not filename:
        filename = "unnamed_file"

    # 限制长度
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        max_name_len = 255 - len(ext) - 1 if ext else 255
        filename = name[:max_name_len] + ("." + ext if ext else "")

    return filename


def get_file_hash(
    file_path: str, algorithm: str = "md5", chunk_size: int = 8192
) -> str:
    """
    计算文件哈希值

    Args:
        file_path (str): 文件路径
        algorithm (str): 哈希算法（md5, sha1, sha256等）
        chunk_size (int): 读取块大小

    Returns:
        str: 文件哈希值

    Raises:
        ValueError: 不支持的哈希算法
        FileNotFoundError: 文件不存在
    """
    try:
        hasher = hashlib.new(algorithm)
    except ValueError:
        raise ValueError(f"不支持的哈希算法: {algorithm}")

    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"文件不存在: {file_path}")


class ProgressTracker:
    """
    进度跟踪器

    用于跟踪文件上传/下载进度
    """

    def __init__(self, total: int, description: str = "处理中"):
        """
        初始化进度跟踪器

        Args:
            total (int): 总大小或总数量
            description (str): 进度描述
        """
        self.total = total
        self.description = description
        self.current = 0
        self.start_time = time.time()
        self._callbacks = []

    def update(self, increment: int = 1) -> None:
        """
        更新进度

        Args:
            increment (int): 增量
        """
        self.current = min(self.current + increment, self.total)

        # 调用回调函数
        for callback in self._callbacks:
            try:
                callback(self)
            except Exception as e:
                logger.warning(f"进度回调函数出错: {e}")

    def add_callback(self, callback: Callable) -> None:
        """
        添加进度回调函数

        Args:
            callback (Callable): 回调函数，接收ProgressTracker实例作为参数
        """
        self._callbacks.append(callback)

    @property
    def percentage(self) -> float:
        """获取完成百分比"""
        if self.total == 0:
            return 100.0
        return (self.current / self.total) * 100.0

    @property
    def elapsed_time(self) -> float:
        """获取已用时间（秒）"""
        return time.time() - self.start_time

    @property
    def estimated_remaining(self) -> Optional[float]:
        """估算剩余时间（秒）"""
        if self.current == 0:
            return None

        elapsed = self.elapsed_time
        rate = self.current / elapsed
        remaining = (self.total - self.current) / rate
        return remaining

    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"{self.description}: {self.current}/{self.total} ({self.percentage:.1f}%)"
        )


def handle_drive_errors(
    default_return=None,
    log_error: bool = True,
    error_message: Optional[str] = None,
    reraise_exceptions: Optional[tuple] = None,
) -> Callable:
    """
    通用驱动错误处理装饰器

    减少重复的 try-catch 代码，统一错误处理逻辑

    Args:
        default_return: 发生错误时的默认返回值
        log_error (bool): 是否记录错误日志
        error_message (Optional[str]): 自定义错误消息前缀
        reraise_exceptions (Optional[tuple]): 需要重新抛出的异常类型

    Returns:
        Callable: 装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 检查是否需要重新抛出特定异常
                if reraise_exceptions and isinstance(e, reraise_exceptions):
                    raise

                # 记录错误日志
                if log_error:
                    method_name = func.__name__
                    class_name = args[0].__class__.__name__ if args else "Unknown"

                    if error_message:
                        log_msg = f"{error_message}: {e}"
                    else:
                        log_msg = f"{class_name}.{method_name} 执行失败: {e}"

                    logger.error(log_msg)

                return default_return

        return wrapper

    return decorator


def validate_fid(allow_empty: bool = False) -> Callable:
    """
    文件ID验证装饰器

    Args:
        allow_empty (bool): 是否允许空的fid

    Returns:
        Callable: 装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 假设第二个参数是fid (self, fid, ...)
            if len(args) >= 2:
                fid = args[1]
                if not allow_empty and (not fid or fid.strip() == ""):
                    logger.error(f"{func.__name__}: fid 不能为空")
                    # 根据函数返回类型返回合适的默认值
                    if func.__annotations__.get("return") is bool:
                        return False
                    elif func.__annotations__.get("return") is str:
                        return ""
                    elif "List" in str(func.__annotations__.get("return", "")):
                        return []
                    else:
                        return None

            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_method_call(log_level: str = "info", include_args: bool = False) -> Callable:
    """
    方法调用日志装饰器

    Args:
        log_level (str): 日志级别 (debug, info, warning, error)
        include_args (bool): 是否包含参数信息

    Returns:
        Callable: 装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            class_name = args[0].__class__.__name__ if args else "Unknown"
            method_name = func.__name__

            # 构建日志消息
            if include_args and len(args) > 1:
                # 只显示前几个关键参数，避免日志过长
                key_args = []
                if len(args) >= 2:  # fid参数
                    key_args.append(f"fid={args[1]}")
                if len(args) >= 3:  # 第三个参数
                    key_args.append(f"arg2={args[2]}")

                arg_str = f"({', '.join(key_args)})" if key_args else ""
                log_msg = f"调用 {class_name}.{method_name}{arg_str}"
            else:
                log_msg = f"调用 {class_name}.{method_name}"

            # 记录日志
            log_func = getattr(logger, log_level, logger.info)
            log_func(log_msg)

            return func(*args, **kwargs)

        return wrapper

    return decorator


# 标准化日志记录工具函数
def log_operation_start(operation: str, target: str = "") -> None:
    """
    记录操作开始的标准日志

    Args:
        logger: 日志记录器
        operation: 操作名称（如：上传文件、下载文件、创建目录等）
        target: 操作目标（如：文件路径、目录名等）
    """
    if target:
        logger.info(f"🚀 开始{operation}: {target}")
    else:
        logger.info(f"🚀 开始{operation}")


def log_operation_success(operation: str, target: str = "", details: str = "") -> None:
    """
    记录操作成功的标准日志

    Args:
        operation: 操作名称
        target: 操作目标
        details: 额外详情信息
    """
    message = f"✅ {operation}成功"
    if target:
        message += f": {target}"
    if details:
        message += f" ({details})"
    logger.info(message)


def log_operation_error(operation: str, error: Exception, target: str = "") -> None:
    """
    记录操作失败的标准日志

    Args:
        operation: 操作名称
        error: 异常对象
        target: 操作目标
    """
    message = f"❌ {operation}失败"
    if target:
        message += f": {target}"
    message += f" - {str(error)}"
    logger.error(message)


def log_operation_warning(operation: str, message: str, target: str = "") -> None:
    """
    记录操作警告的标准日志

    Args:

        operation: 操作名称
        message: 警告消息
        target: 操作目标
    """
    warning_msg = f"⚠️ {operation}"
    if target:
        warning_msg += f"({target})"
    warning_msg += f": {message}"
    logger.warning(warning_msg)


def log_progress_info(
    operation: str, current: int, total: int, item_name: str = "项"
) -> None:
    """
    记录进度信息的标准日志

    Args:
        operation: 操作名称
        current: 当前进度
        total: 总数
        item_name: 项目名称（如：文件、目录等）
    """
    percentage = (current / total * 100) if total > 0 else 0
    logger.info(
        f"📊 {operation}进度: {current}/{total} {item_name} ({percentage:.1f}%)"
    )


def log_storage_info(used_space: str, free_space: str, total_space: str) -> None:
    """
    记录存储空间信息的标准日志

    Args:
        used_space: 已用空间
        free_space: 剩余空间
        total_space: 总空间
    """
    logger.info(
        f"💾 存储空间: 已用 {used_space}, 剩余 {free_space}, 总计 {total_space}"
    )


# 文档字符串标准化工具函数
def format_docstring_template(
    description: str,
    detailed_description: str = "",
    args: Dict[str, str] = None,
    returns: str = "",
    raises: Dict[str, str] = None,
    examples: List[str] = None,
) -> str:
    """
    生成标准化的文档字符串模板

    Args:
        description: 简短描述
        detailed_description: 详细描述
        args: 参数说明字典，键为参数名，值为说明
        returns: 返回值说明
        raises: 异常说明字典，键为异常类型，值为说明
        examples: 示例代码列表

    Returns:
        str: 格式化的文档字符串
    """
    lines = ['        """', f"        {description}"]

    if detailed_description:
        lines.extend(["        ", f"        {detailed_description}"])

    if args:
        lines.extend(["        ", "        Args:"])
        for arg_name, arg_desc in args.items():
            lines.append(f"            {arg_name}: {arg_desc}")

    if returns:
        lines.extend(["        ", "        Returns:", f"            {returns}"])

    if raises:
        lines.extend(["        ", "        Raises:"])
        for exc_type, exc_desc in raises.items():
            lines.append(f"            {exc_type}: {exc_desc}")

    if examples:
        lines.extend(["        ", "        Examples:"])
        for example in examples:
            lines.extend(["            >>> " + line for line in example.split("\n")])

    lines.append('        """')
    return "\n".join(lines)
