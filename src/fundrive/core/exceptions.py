"""
FunDrive 统一异常处理模块

提供标准化的异常类和错误处理装饰器
"""

import functools
import time
from typing import Callable, Optional
from funutil import getLogger

logger = getLogger("fundrive.exceptions")


class FunDriveError(Exception):
    """FunDrive 基础异常类"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        """
        初始化异常

        Args:
            message (str): 错误消息
            error_code (Optional[str]): 错误代码
            details (Optional[dict]): 错误详情
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class AuthenticationError(FunDriveError):
    """认证失败异常"""

    def __init__(self, message: str = "认证失败", **kwargs):
        super().__init__(message, error_code="AUTH_FAILED", **kwargs)


class AuthorizationError(FunDriveError):
    """授权失败异常"""

    def __init__(self, message: str = "权限不足", **kwargs):
        super().__init__(message, error_code="AUTH_INSUFFICIENT", **kwargs)


class NetworkError(FunDriveError):
    """网络连接异常"""

    def __init__(self, message: str = "网络连接失败", **kwargs):
        super().__init__(message, error_code="NETWORK_ERROR", **kwargs)


class RateLimitError(FunDriveError):
    """API调用频率限制异常"""

    def __init__(
        self,
        message: str = "API调用频率超限",
        retry_after: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(message, error_code="RATE_LIMITED", **kwargs)
        self.retry_after = retry_after


class FileNotFoundError(FunDriveError):
    """文件未找到异常"""

    def __init__(
        self, message: str = "文件不存在", file_path: Optional[str] = None, **kwargs
    ):
        super().__init__(message, error_code="FILE_NOT_FOUND", **kwargs)
        self.file_path = file_path


class FileExistsError(FunDriveError):
    """文件已存在异常"""

    def __init__(
        self, message: str = "文件已存在", file_path: Optional[str] = None, **kwargs
    ):
        super().__init__(message, error_code="FILE_EXISTS", **kwargs)
        self.file_path = file_path


class InsufficientStorageError(FunDriveError):
    """存储空间不足异常"""

    def __init__(self, message: str = "存储空间不足", **kwargs):
        super().__init__(message, error_code="INSUFFICIENT_STORAGE", **kwargs)


class InvalidParameterError(FunDriveError):
    """参数无效异常"""

    def __init__(
        self, message: str = "参数无效", parameter: Optional[str] = None, **kwargs
    ):
        super().__init__(message, error_code="INVALID_PARAMETER", **kwargs)
        self.parameter = parameter


class OperationNotSupportedError(FunDriveError):
    """操作不支持异常"""

    def __init__(
        self, message: str = "操作不支持", operation: Optional[str] = None, **kwargs
    ):
        super().__init__(message, error_code="OPERATION_NOT_SUPPORTED", **kwargs)
        self.operation = operation


class UploadError(FunDriveError):
    """文件上传异常"""

    def __init__(self, message: str = "文件上传失败", **kwargs):
        super().__init__(message, error_code="UPLOAD_FAILED", **kwargs)


class DownloadError(FunDriveError):
    """文件下载异常"""

    def __init__(self, message: str = "文件下载失败", **kwargs):
        super().__init__(message, error_code="DOWNLOAD_FAILED", **kwargs)


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (NetworkError, RateLimitError),
) -> Callable:
    """
    重试装饰器，在遇到指定异常时自动重试

    Args:
        max_retries (int): 最大重试次数
        delay (float): 初始延迟时间（秒）
        backoff_factor (float): 退避因子
        exceptions (tuple): 需要重试的异常类型

    Returns:
        Callable: 装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"函数 {func.__name__} 重试 {max_retries} 次后仍然失败: {e}"
                        )
                        raise

                    # 处理速率限制的特殊情况
                    if isinstance(e, RateLimitError) and e.retry_after:
                        current_delay = e.retry_after

                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次调用失败: {e}，{current_delay:.1f}秒后重试"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
                except Exception as e:
                    # 非指定异常类型，直接抛出
                    logger.error(f"函数 {func.__name__} 遇到非重试异常: {e}")
                    raise

            # 理论上不会到达这里
            raise last_exception

        return wrapper

    return decorator


def handle_api_errors(func: Callable) -> Callable:
    """
    API错误处理装饰器，将常见的HTTP错误转换为FunDrive异常

    Args:
        func (Callable): 被装饰的函数

    Returns:
        Callable: 装饰后的函数
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 根据异常类型和消息转换为FunDrive异常
            error_message = str(e).lower()

            if "401" in error_message or "unauthorized" in error_message:
                raise AuthenticationError(f"认证失败: {e}") from e
            elif "403" in error_message or "forbidden" in error_message:
                raise AuthorizationError(f"权限不足: {e}") from e
            elif "404" in error_message or "not found" in error_message:
                raise FileNotFoundError(f"资源不存在: {e}") from e
            elif "409" in error_message or "conflict" in error_message:
                raise FileExistsError(f"资源冲突: {e}") from e
            elif "429" in error_message or "rate limit" in error_message:
                raise RateLimitError(f"请求频率过高: {e}") from e
            elif "507" in error_message or "insufficient storage" in error_message:
                raise InsufficientStorageError(f"存储空间不足: {e}") from e
            elif any(
                net_err in error_message
                for net_err in ["connection", "timeout", "network"]
            ):
                raise NetworkError(f"网络连接失败: {e}") from e
            else:
                # 其他异常包装为通用FunDrive异常
                raise FunDriveError(f"操作失败: {e}") from e

    return wrapper


def log_operation(operation_name: str) -> Callable:
    """
    操作日志装饰器，记录函数调用的开始和结束

    Args:
        operation_name (str): 操作名称

    Returns:
        Callable: 装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger.info(f"开始执行 {operation_name}")

            try:
                result = func(*args, **kwargs)
                elapsed_time = time.time() - start_time
                logger.info(f"{operation_name} 执行成功，耗时 {elapsed_time:.2f} 秒")
                return result
            except Exception as e:
                elapsed_time = time.time() - start_time
                logger.error(
                    f"{operation_name} 执行失败，耗时 {elapsed_time:.2f} 秒: {e}"
                )
                raise

        return wrapper

    return decorator


def validate_parameters(**validators) -> Callable:
    """
    参数验证装饰器

    Args:
        **validators: 参数名到验证函数的映射

    Returns:
        Callable: 装饰器函数

    Examples:
        @validate_parameters(
            file_path=lambda x: x and isinstance(x, str),
            size=lambda x: x is None or (isinstance(x, int) and x >= 0)
        )
        def upload_file(self, file_path, size=None):
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取函数签名
            import inspect

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # 验证参数
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise InvalidParameterError(
                            f"参数 {param_name} 验证失败",
                            parameter=param_name,
                            details={"value": value},
                        )

            return func(*args, **kwargs)

        return wrapper

    return decorator
