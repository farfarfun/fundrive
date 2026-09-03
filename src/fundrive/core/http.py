"""共享 HTTP 会话工厂

各驱动此前的 HTTP 用法有四种方言：模块级 ``requests.get`` / 裸
``requests.Session()`` / 每个调用点手写 ``timeout=10`` / 什么都不写。
结果是 88 个请求里 81 个没有超时（一个挂住的 TCP 连接会永久挂死调用方），
没有任何驱动配置连接池或重试。

本模块提供一个统一入口：

>>> from fundrive.core.http import new_session
>>> session = new_session()          # 带默认超时 + 重试 + 连接池
>>> session.get("https://example.com")   # 无需每次写 timeout

``TimeoutSession`` 在 :meth:`request` 层注入默认超时，因此**忘记写
timeout 也是安全的**——这比依赖每个调用点的自觉要可靠得多。
"""

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .constants import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_POOL_SIZE,
    DEFAULT_RETRY_DELAY,
    DEFAULT_TIMEOUT,
)

# 幂等方法才自动重试；POST/PATCH 不重试，避免重复提交
_RETRY_METHODS = frozenset(["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"])

# 值得重试的状态码：限流 + 网关类瞬时故障
_RETRY_STATUS = (429, 500, 502, 503, 504)


class TimeoutSession(requests.Session):
    """会话级默认超时的 :class:`requests.Session`。

    调用点显式传 ``timeout`` 时以调用点为准；不传则用 ``self.timeout``。
    """

    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
        super().__init__()
        self.timeout = timeout

    def request(self, method: str, url: str, **kwargs: Any):  # type: ignore[override]
        kwargs.setdefault("timeout", self.timeout)
        return super().request(method, url, **kwargs)


def new_session(
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_MAX_RETRIES,
    backoff_factor: float = DEFAULT_RETRY_DELAY,
    pool_size: int = DEFAULT_POOL_SIZE,
    headers: dict | None = None,
) -> TimeoutSession:
    """构造一个带默认超时、自动重试和连接池的会话。

    Args:
        timeout: 默认超时（秒），调用点可覆盖。
        retries: 幂等请求的重试次数；0 表示不重试。
        backoff_factor: 重试退避因子。
        pool_size: 连接池大小。
        headers: 需要附加到每个请求的默认 header。

    Returns:
        TimeoutSession: 配置好的会话对象。记得用完 ``close()``，
        或直接当上下文管理器使用。

    Note:
        ``read=False`` 是刻意的：**读超时不重试**。如果重试读超时，
        ``timeout=30`` 加 3 次重试会变成最长 30×4 秒再加退避睡眠，
        实际把"超时"拖成两分钟，与设置超时的初衷相反。读超时因此立即
        抛出，且保持 :class:`requests.exceptions.Timeout` 类型；
        连接失败和 429/5xx 仍然会重试（各次重试自带完整超时）。
    """
    session = TimeoutSession(timeout=timeout)

    retry = Retry(
        total=retries,
        connect=retries,
        read=False,  # 见上方 Note：读超时立即抛出，不做重试放大
        status=retries,
        backoff_factor=backoff_factor,
        status_forcelist=_RETRY_STATUS,
        allowed_methods=_RETRY_METHODS,
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=pool_size,
        pool_maxsize=pool_size,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    if headers:
        session.headers.update(headers)
    return session


__all__ = ["TimeoutSession", "new_session", "DEFAULT_TIMEOUT"]
