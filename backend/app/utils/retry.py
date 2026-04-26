import asyncio
import functools
import logging
import random
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)


def async_retry(
	retries: int = 3,
	base_delay: float = 1.0,
	max_delay: float = 10.0,
	exceptions: tuple[type[Exception], ...] = (Exception,),
	backoff_factor: float = 2.0,
	jitter: bool = True,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
	"""
	Decorator for retrying an asynchronous function with exponential backoff.

	Args:
		retries: Maximum number of retry attempts.
		base_delay: Initial delay between retries in seconds.
		max_delay: Maximum delay between retries in seconds.
		exceptions: Tuple of exception types to catch and retry.
		backoff_factor: Multiplier for the delay after each retry.
		jitter: Whether to add random jitter to the delay.
	"""

	def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
		@functools.wraps(func)
		async def wrapper(*args: Any, **kwargs: Any) -> Any:
			delay = base_delay
			last_exception = None

			for attempt in range(retries + 1):
				try:
					return await func(*args, **kwargs)
				except exceptions as e:
					last_exception = e
					if attempt >= retries:
						logger.error(f"Final attempt failed for {func.__name__} after {retries} retries: {e}")
						raise

					actual_delay = delay
					if jitter:
						actual_delay *= random.uniform(0.5, 1.5)

					actual_delay = min(actual_delay, max_delay)

					logger.warning(
						f"Attempt {attempt + 1}/{retries + 1} failed for {func.__name__}: {e}. " f"Retrying in {actual_delay:.2f}s..."
					)

					await asyncio.sleep(actual_delay)
					delay *= backoff_factor

			# Should not reach here due to raise in loop
			if last_exception:
				raise last_exception

		return wrapper

	return decorator
