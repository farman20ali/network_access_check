import time
import functools
from typing import Callable, TypeVar, Any, Tuple, Optional

T = TypeVar('T')

def with_retry(
    retries: int = 1,
    delay: float = 1.0,
    backoff: float = 1.0,
    exceptions: Tuple[type, ...] = (Exception,)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to retry a function on exception with optional exponential backoff."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return retry_call(
                func,
                args=args,
                kwargs=kwargs,
                retries=retries,
                delay=delay,
                backoff=backoff,
                exceptions=exceptions
            )
        return wrapper
    return decorator

def retry_call(
    func: Callable[..., T],
    args: Tuple[Any, ...] = (),
    kwargs: Optional[dict] = None,
    retries: int = 1,
    delay: float = 1.0,
    backoff: float = 1.0,
    exceptions: Tuple[type, ...] = (Exception,)
) -> T:
    """Helper function to execute a callable with retries."""
    if kwargs is None:
        kwargs = {}
    
    current_delay = delay
    last_exception = None
    
    for attempt in range(1, retries + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt < retries:
                time.sleep(current_delay)
                current_delay *= backoff
            
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry loop exited unexpectedly")
