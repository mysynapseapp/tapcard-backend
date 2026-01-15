"""
Simple HTTP response caching for FastAPI.

Usage:
```python
from fastapi import FastAPI
from cache import cache_response

app = FastAPI()

@app.get("/profile/{user_id}")
@cache_response(expire=60)  # Cache for 60 seconds
def get_profile(user_id: str):
    # ... your logic
    return {"profile": data}
```

🔹 Benefits:
- Public profiles load instantly from cache
- Reduces database load
- Backend still refreshes silently
"""

import time
from functools import wraps
from typing import Callable, Optional
import threading

# In-memory cache storage
_cache_store = {}
_cache_lock = threading.Lock()


def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a unique cache key from function arguments"""
    key_parts = [prefix]
    for arg in args:
        key_parts.append(str(arg))
    # Sort kwargs for consistent ordering
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}:{v}")
    return ":".join(key_parts)


def cache_response(expire: int = 60, prefix: str = "cache"):
    """
    Decorator to cache HTTP responses in memory.
    
    Args:
        expire: Cache expiration time in seconds (default: 60)
        prefix: Cache key prefix (default: "cache")
    
    Example:
        @app.get("/profile/{id}")
        @cache_response(expire=60)
        def get_profile(id: str):
            return {"id": id, "data": ...}
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = get_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            with _cache_lock:
                if cache_key in _cache_store:
                    cached_data, timestamp = _cache_store[cache_key]
                    if time.time() - timestamp < expire:
                        return cached_data
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            with _cache_lock:
                _cache_store[cache_key] = (result, time.time())
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = get_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            with _cache_lock:
                if cache_key in _cache_store:
                    cached_data, timestamp = _cache_store[cache_key]
                    if time.time() - timestamp < expire:
                        return cached_data
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            with _cache_lock:
                _cache_store[cache_key] = (result, time.time())
            
            return result
        
        # Choose wrapper based on whether function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def clear_cache(prefix: Optional[str] = None):
    """
    Clear cache entries.
    
    Args:
        prefix: If provided, only clear entries with this prefix
                If None, clear all entries
    """
    with _cache_lock:
        if prefix is None:
            _cache_store.clear()
        else:
            keys_to_remove = [k for k in _cache_store.keys() if k.startswith(prefix)]
            for k in keys_to_remove:
                del _cache_store[k]


def get_cache_stats() -> dict:
    """Get cache statistics"""
    with _cache_lock:
        return {
            "entries": len(_cache_store),
            "keys": list(_cache_store.keys())[:10],  # First 10 keys
        }

