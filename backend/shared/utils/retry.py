#!/usr/bin/env python3
"""
异步重试工具
提供带指数退避与抖动的通用重试装饰/助手。

运行环境: Python 3.11+
依赖: asyncio, typing, random
"""

import asyncio
import random
from typing import Any, Awaitable, Callable, Iterable, Optional, Tuple, Type


async def retry_async(
    func: Callable[..., Awaitable[Any]],
    *,
    attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    jitter: float = 0.2,
    **kwargs: Any,
) -> Any:
    """对异步函数进行重试。

    参数:
        func: 需要执行的异步函数
        attempts: 最大重试次数（包含首次尝试）
        base_delay: 初始退避延时（秒）
        max_delay: 最大退避延时（秒）
        exceptions: 触发重试的异常类型元组
        jitter: 抖动比例（0-1），用于避免雪崩效应
        **kwargs: 传递给函数的关键字参数

    返回:
        func 的返回值

    异常:
        最后一次失败的异常会被抛出
    """
    last_exc: Optional[BaseException] = None
    for attempt in range(1, attempts + 1):
        try:
            return await func(**kwargs)
        except exceptions as e:
            last_exc = e
            if attempt >= attempts:
                break
            # 指数退避
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            # 叠加抖动
            if jitter > 0:
                jitter_amount = delay * random.uniform(0, jitter)
                delay += jitter_amount
            await asyncio.sleep(delay)
    # 重试仍失败，抛出最后一次异常
    assert last_exc is not None
    raise last_exc