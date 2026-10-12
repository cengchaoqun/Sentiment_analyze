import asyncio
from functools import wraps
from typing import Callable

from loguru import logger

from dataclasses import dataclass


@dataclass(slots=True)
class RetryConfig:
    init_delay: float = 1.0
    max_delay: float = 60.0
    max_retries: int = 3
    backoff_factor: float = 2.0  # 参与重试的延迟因子

    def get_retry_delay(self, func_name: str, exc: Exception, attempt: int) -> float | None:
        """
        职责：
        1. 判断是否能重试
        2. 如果能重试，根据重试的次数返回重试的延迟
        3. 如果不能重试，直接返回None
        :param func_name:
        :param exc:
        :param attempt:
        :return:
        """
        # 1. 判断是否能重试
        if not self._is_retriable(exc):
            return None
        # 2. 根据重试的次数返回重试的延迟
        delay = self._compute_retry_delay(attempt)

        # 3. 日志输出
        logger.warning(f"函数{func_name}失败，失败原因{exc}，开始第{attempt + 1}次尝试")

        # 4. 返回
        return delay

    def _is_retriable(self, exc: Exception) -> bool:
        """
        职责：返回是否可以重试
        逻辑：从异常对象中获取状态码
        客户端的4xx状态码中：401、403不能进行重试，429可以进行重试（服务端限流）
        服务端的500状态码：500（不是我们自己服务器内部抛出来的500，而是第三方服务抛出的500，可以重试）
        :param exc:
        :return:
        """
        # 1.根据异常对象获取服务端的响应状态码
        status_code = self._extract_status_code(exc)

        # 2.排除客户端的429状态码，不能进行重试
        if isinstance(status_code, int) and 400 <= status_code < 500 and status_code != 429:
            return False

        # 3.其他状态码都可以进行重试，包括None
        return True

    def _extract_status_code(self, exc: Exception) -> int | None:
        """
        职责：从异常对象中获取状态码
        :param exc:
        :return:
        """
        # 1.先从Exception对象中提取status_code属性
        status_code = getattr(exc, "status_code", None)

        if status_code is not None:
            return status_code

        # 2.再继续从Exception对象中获取response属性
        response = getattr(exc, "response", None)

        # 3.尝试从response中获取status_code
        return getattr(response, "status_code", None)

    def _compute_retry_delay(self, attempt: int) -> float:
        """
        职责：根据重试次数计算重试延迟
        :param attempt:
        :return:
        """
        return min(self.init_delay * (self.backoff_factor ** attempt), self.max_delay)


retry_config = RetryConfig()


def with_retry(func: Callable):
    """
    装饰器函数
    需要完成重试的逻辑
    装饰逻辑：在执行目标方法期间，如果出现了异常，且异常在可重试的范围内，则继续重试
    :param func:
    :return:
    """
    # 1.判断目标方法是不是协程对象
    if not asyncio.iscoroutinefunction(func):
        raise TypeError("重试器只能装饰异步函数，不能装饰同步函数")

    # 2.定义装饰器函数
    @wraps(func)  # 获取目标函数的元信息
    async def wrapper(*args, **kwargs):
        """
        职责：
        1. 执行目标方法
        2. 判断是否出现异常，如果异常在可重试范围内，则继续重试
        :param args:
        :param kwargs:
        :return:
        """
        for attempt in range(retry_config.max_retries):
            try:
                await func(*args, **kwargs)  # 执行目标方法（解包还原）
            except Exception as exc:
                delay = retry_config.get_retry_delay(func.__name__, exc, attempt)
                if delay is None:
                    break
                await asyncio.sleep(delay)
        return wrapper
