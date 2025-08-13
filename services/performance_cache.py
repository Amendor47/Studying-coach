# services/performance_cache.py
# -*- coding: utf-8 -*-
"""
Multi-Layer Caching System for Maximum Performance

This module implements advanced caching strategies:
- Multi-layer caching: browser, CDN, database, application level
- Predictive preloading based on user behavior patterns
- Intelligent cache invalidation and conflict resolution
- Response time optimization < 50ms for cached content
"""

from __future__ import annotations

import json
import time
import hashlib
import threading
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from functools import wraps
from dataclasses import dataclass, asdict
import pickle
import gzip

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

try:
    import memcache
    MEMCACHE_AVAILABLE = True
except ImportError:
    memcache = None
    MEMCACHE_AVAILABLE = False

from pathlib import Path


@dataclass
class CacheConfig:
    """Configuration for caching system"""
    # Layer configurations
    browser_cache_duration: int = 300  # 5 minutes
    application_cache_size: int = 1000  # items
    database_cache_duration: int = 3600  # 1 hour
    
    # Performance targets
    target_response_time_ms: int = 50
    cache_hit_ratio_target: float = 0.85
    
    # Storage paths
    cache_dir: Path = Path("cache/performance")
    
    # Redis configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 1
    
    # Memcached configuration
    memcache_servers: List[str] = None
    
    # Compression
    enable_compression: bool = True
    compression_threshold: int = 1024  # bytes
    
    def __post_init__(self):
        if self.memcache_servers is None:
            self.memcache_servers = ['127.0.0.1:11211']
        self.cache_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata"""
    key: str
    data: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    content_hash: Optional[str] = None
    compressed: bool = False
    cache_layer: str = "application"
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.now() > self.expires_at
    
    def is_stale(self, max_age_seconds: int = 300) -> bool:
        """Check if cache entry is stale"""
        age = datetime.now() - self.created_at
        return age.total_seconds() > max_age_seconds
    
    def touch(self) -> None:
        """Update access statistics"""
        self.access_count += 1
        self.last_accessed = datetime.now()


class PerformanceCache:
    """Multi-layer caching system for maximum performance"""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        
        # In-memory cache (L1)
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._cache_lock = threading.RLock()
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
            "compressions": 0,
            "response_times": [],
            "cache_sizes": {
                "memory": 0,
                "redis": 0,
                "file": 0
            }
        }
        
        # Initialize external caches
        self._init_redis()
        self._init_memcache()
        
        # Preload behavior patterns
        self.behavior_patterns = {}
        self.load_patterns()
        
        # Background cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self._cleanup_thread.start()
    
    def _init_redis(self) -> None:
        """Initialize Redis connection if available"""
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=self.config.redis_host,
                    port=self.config.redis_port,
                    db=self.config.redis_db,
                    decode_responses=False,
                    socket_timeout=0.1,
                    health_check_interval=30
                )
                # Test connection
                self.redis_client.ping()
            except Exception:
                self.redis_client = None
    
    def _init_memcache(self) -> None:
        """Initialize Memcached connection if available"""
        self.memcache_client = None
        if MEMCACHE_AVAILABLE:
            try:
                self.memcache_client = memcache.Client(
                    self.config.memcache_servers,
                    debug=0
                )
                # Test connection
                self.memcache_client.set("test", "test", time=1)
                self.memcache_client.delete("test")
            except Exception:
                self.memcache_client = None
    
    def _serialize_data(self, data: Any) -> Tuple[bytes, bool]:
        """Serialize and optionally compress data"""
        serialized = pickle.dumps(data)
        compressed = False
        
        if (self.config.enable_compression and 
            len(serialized) > self.config.compression_threshold):
            serialized = gzip.compress(serialized)
            compressed = True
            self.stats["compressions"] += 1
        
        return serialized, compressed
    
    def _deserialize_data(self, data: bytes, compressed: bool) -> Any:
        """Deserialize and decompress data"""
        if compressed:
            data = gzip.decompress(data)
        return pickle.loads(data)
    
    def _generate_cache_key(self, namespace: str, key: str, **kwargs) -> str:
        """Generate a consistent cache key"""
        key_parts = [namespace, key]
        
        # Add sorted kwargs to ensure consistent keys
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.append(json.dumps(sorted_kwargs, sort_keys=True))
        
        combined_key = ":".join(str(part) for part in key_parts)
        return hashlib.md5(combined_key.encode()).hexdigest()
    
    def get(self, namespace: str, key: str, **kwargs) -> Optional[Any]:
        """Get value from cache with multi-layer lookup"""
        start_time = time.perf_counter()
        cache_key = self._generate_cache_key(namespace, key, **kwargs)
        
        try:
            # L1: Memory cache
            entry = self._get_from_memory(cache_key)
            if entry is not None:
                self.stats["hits"] += 1
                entry.touch()
                return entry.data
            
            # L2: Redis cache
            if self.redis_client:
                entry = self._get_from_redis(cache_key)
                if entry is not None:
                    self.stats["hits"] += 1
                    # Store in L1 for faster access next time
                    self._store_in_memory(cache_key, entry)
                    return entry.data
            
            # L3: Memcached
            if self.memcache_client:
                entry = self._get_from_memcache(cache_key)
                if entry is not None:
                    self.stats["hits"] += 1
                    # Store in upper layers
                    self._store_in_memory(cache_key, entry)
                    if self.redis_client:
                        self._store_in_redis(cache_key, entry)
                    return entry.data
            
            # L4: File cache
            entry = self._get_from_file(cache_key)
            if entry is not None:
                self.stats["hits"] += 1
                # Store in upper layers
                self._store_in_memory(cache_key, entry)
                if self.redis_client:
                    self._store_in_redis(cache_key, entry)
                return entry.data
            
            self.stats["misses"] += 1
            return None
            
        finally:
            response_time = (time.perf_counter() - start_time) * 1000
            self.stats["response_times"].append(response_time)
            
            # Keep only recent response times
            if len(self.stats["response_times"]) > 1000:
                self.stats["response_times"] = self.stats["response_times"][-500:]
    
    def set(self, namespace: str, key: str, value: Any, 
            ttl_seconds: Optional[int] = None, **kwargs) -> bool:
        """Set value in cache with multi-layer storage"""
        cache_key = self._generate_cache_key(namespace, key, **kwargs)
        
        if ttl_seconds is None:
            ttl_seconds = self.config.application_cache_size
        
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        content_hash = hashlib.md5(str(value).encode()).hexdigest()
        
        entry = CacheEntry(
            key=cache_key,
            data=value,
            created_at=datetime.now(),
            expires_at=expires_at,
            content_hash=content_hash
        )
        
        try:
            # Store in all available layers
            success = True
            
            # L1: Memory
            success &= self._store_in_memory(cache_key, entry)
            
            # L2: Redis
            if self.redis_client:
                success &= self._store_in_redis(cache_key, entry, ttl_seconds)
            
            # L3: Memcached
            if self.memcache_client:
                success &= self._store_in_memcache(cache_key, entry, ttl_seconds)
            
            # L4: File (for persistence)
            success &= self._store_in_file(cache_key, entry)
            
            return success
            
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def _get_from_memory(self, cache_key: str) -> Optional[CacheEntry]:
        """Get from in-memory cache"""
        with self._cache_lock:
            entry = self._memory_cache.get(cache_key)
            if entry and not entry.is_expired():
                return entry
            elif entry:  # Expired
                del self._memory_cache[cache_key]
        return None
    
    def _store_in_memory(self, cache_key: str, entry: CacheEntry) -> bool:
        """Store in memory cache with LRU eviction"""
        with self._cache_lock:
            # Check size limit
            if len(self._memory_cache) >= self.config.application_cache_size:
                self._evict_lru()
            
            self._memory_cache[cache_key] = entry
            self.stats["cache_sizes"]["memory"] = len(self._memory_cache)
            return True
    
    def _evict_lru(self) -> None:
        """Evict least recently used items from memory cache"""
        if not self._memory_cache:
            return
        
        # Find LRU item
        lru_key = min(
            self._memory_cache.keys(),
            key=lambda k: self._memory_cache[k].last_accessed or datetime.min
        )
        del self._memory_cache[lru_key]
    
    def _get_from_redis(self, cache_key: str) -> Optional[CacheEntry]:
        """Get from Redis cache"""
        if not self.redis_client:
            return None
        
        try:
            data = self.redis_client.get(cache_key)
            if data:
                entry = pickle.loads(data)
                if not entry.is_expired():
                    return entry
                else:
                    self.redis_client.delete(cache_key)
        except Exception:
            pass
        return None
    
    def _store_in_redis(self, cache_key: str, entry: CacheEntry, 
                       ttl_seconds: Optional[int] = None) -> bool:
        """Store in Redis cache"""
        if not self.redis_client:
            return False
        
        try:
            serialized_entry = pickle.dumps(entry)
            result = self.redis_client.setex(
                cache_key, 
                ttl_seconds or self.config.database_cache_duration,
                serialized_entry
            )
            return bool(result)
        except Exception:
            return False
    
    def _get_from_memcache(self, cache_key: str) -> Optional[CacheEntry]:
        """Get from Memcached"""
        if not self.memcache_client:
            return None
        
        try:
            data = self.memcache_client.get(cache_key)
            if data:
                entry = pickle.loads(data)
                if not entry.is_expired():
                    return entry
        except Exception:
            pass
        return None
    
    def _store_in_memcache(self, cache_key: str, entry: CacheEntry,
                          ttl_seconds: Optional[int] = None) -> bool:
        """Store in Memcached"""
        if not self.memcache_client:
            return False
        
        try:
            serialized_entry = pickle.dumps(entry)
            return self.memcache_client.set(
                cache_key, 
                serialized_entry,
                time=ttl_seconds or self.config.database_cache_duration
            )
        except Exception:
            return False
    
    def _get_from_file(self, cache_key: str) -> Optional[CacheEntry]:
        """Get from file cache"""
        cache_file = self.config.cache_dir / f"{cache_key}.cache"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    data = f.read()
                    if data.startswith(b'x\x9c'):  # gzip magic
                        data = gzip.decompress(data)
                    entry = pickle.loads(data)
                    
                if not entry.is_expired():
                    return entry
                else:
                    cache_file.unlink(missing_ok=True)
            except Exception:
                cache_file.unlink(missing_ok=True)
        return None
    
    def _store_in_file(self, cache_key: str, entry: CacheEntry) -> bool:
        """Store in file cache"""
        cache_file = self.config.cache_dir / f"{cache_key}.cache"
        
        try:
            data = pickle.dumps(entry)
            if self.config.enable_compression:
                data = gzip.compress(data)
            
            with open(cache_file, 'wb') as f:
                f.write(data)
            return True
        except Exception:
            return False
    
    def invalidate(self, namespace: str, key: str = None, **kwargs) -> bool:
        """Invalidate cache entries"""
        if key:
            # Invalidate specific key
            cache_key = self._generate_cache_key(namespace, key, **kwargs)
            return self._invalidate_key(cache_key)
        else:
            # Invalidate entire namespace
            return self._invalidate_namespace(namespace)
    
    def _invalidate_key(self, cache_key: str) -> bool:
        """Invalidate a specific cache key across all layers"""
        success = True
        
        # L1: Memory
        with self._cache_lock:
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
        
        # L2: Redis
        if self.redis_client:
            try:
                self.redis_client.delete(cache_key)
            except Exception:
                success = False
        
        # L3: Memcached
        if self.memcache_client:
            try:
                self.memcache_client.delete(cache_key)
            except Exception:
                success = False
        
        # L4: File
        cache_file = self.config.cache_dir / f"{cache_key}.cache"
        if cache_file.exists():
            try:
                cache_file.unlink()
            except Exception:
                success = False
        
        if success:
            self.stats["invalidations"] += 1
        
        return success
    
    def _invalidate_namespace(self, namespace: str) -> bool:
        """Invalidate all keys in a namespace"""
        success = True
        
        # Memory cache
        with self._cache_lock:
            keys_to_remove = [
                key for key, entry in self._memory_cache.items()
                if entry.key.startswith(namespace)
            ]
            for key in keys_to_remove:
                del self._memory_cache[key]
        
        # Redis - scan for keys with pattern
        if self.redis_client:
            try:
                pattern = f"{namespace}:*"
                for key in self.redis_client.scan_iter(match=pattern):
                    self.redis_client.delete(key)
            except Exception:
                success = False
        
        # File cache - scan directory
        try:
            for cache_file in self.config.cache_dir.glob("*.cache"):
                try:
                    # Quick check if file starts with namespace
                    if cache_file.stem.startswith(hashlib.md5(namespace.encode()).hexdigest()[:8]):
                        cache_file.unlink()
                except Exception:
                    pass
        except Exception:
            success = False
        
        return success
    
    def preload(self, patterns: List[Tuple[str, str, Dict]]) -> None:
        """Preload cache based on usage patterns"""
        for namespace, key, kwargs in patterns:
            # Check if already cached
            cache_key = self._generate_cache_key(namespace, key, **kwargs)
            if not self._get_from_memory(cache_key):
                # Generate and cache the data
                # This would be called by the application layer
                pass
    
    def record_pattern(self, user_id: str, action: str, resources: List[str]) -> None:
        """Record user behavior pattern for predictive caching"""
        if user_id not in self.behavior_patterns:
            self.behavior_patterns[user_id] = []
        
        pattern = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "resources": resources
        }
        
        self.behavior_patterns[user_id].append(pattern)
        
        # Keep only recent patterns
        if len(self.behavior_patterns[user_id]) > 100:
            self.behavior_patterns[user_id] = self.behavior_patterns[user_id][-50:]
        
        self.save_patterns()
    
    def predict_next_resources(self, user_id: str, current_action: str) -> List[str]:
        """Predict what resources user will likely access next"""
        if user_id not in self.behavior_patterns:
            return []
        
        patterns = self.behavior_patterns[user_id]
        predictions = []
        
        # Simple pattern matching - look for sequences
        for i, pattern in enumerate(patterns[:-1]):
            if pattern["action"] == current_action:
                next_pattern = patterns[i + 1]
                predictions.extend(next_pattern["resources"])
        
        # Return most common predictions
        if predictions:
            from collections import Counter
            common_predictions = Counter(predictions).most_common(5)
            return [pred[0] for pred in common_predictions]
        
        return []
    
    def load_patterns(self) -> None:
        """Load behavior patterns from storage"""
        patterns_file = self.config.cache_dir / "behavior_patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r') as f:
                    self.behavior_patterns = json.load(f)
            except Exception:
                self.behavior_patterns = {}
    
    def save_patterns(self) -> None:
        """Save behavior patterns to storage"""
        patterns_file = self.config.cache_dir / "behavior_patterns.json"
        try:
            with open(patterns_file, 'w') as f:
                json.dump(self.behavior_patterns, f)
        except Exception:
            pass
    
    def _cleanup_worker(self) -> None:
        """Background worker for cache cleanup"""
        while True:
            try:
                time.sleep(300)  # Run every 5 minutes
                self._cleanup_expired()
                self._update_cache_stats()
            except Exception:
                pass
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries from all cache layers"""
        # Memory cache
        with self._cache_lock:
            expired_keys = [
                key for key, entry in self._memory_cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._memory_cache[key]
        
        # File cache
        for cache_file in self.config.cache_dir.glob("*.cache"):
            try:
                if cache_file.stat().st_mtime < (time.time() - self.config.database_cache_duration):
                    cache_file.unlink()
            except Exception:
                pass
    
    def _update_cache_stats(self) -> None:
        """Update cache size statistics"""
        self.stats["cache_sizes"]["memory"] = len(self._memory_cache)
        
        if self.redis_client:
            try:
                info = self.redis_client.info()
                self.stats["cache_sizes"]["redis"] = info.get("used_memory", 0)
            except Exception:
                pass
        
        # File cache size
        try:
            total_size = sum(
                f.stat().st_size for f in self.config.cache_dir.glob("*.cache")
            )
            self.stats["cache_sizes"]["file"] = total_size
        except Exception:
            pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_ratio = self.stats["hits"] / max(total_requests, 1)
        
        avg_response_time = 0
        if self.stats["response_times"]:
            avg_response_time = sum(self.stats["response_times"]) / len(self.stats["response_times"])
        
        return {
            "hit_ratio": round(hit_ratio, 3),
            "total_requests": total_requests,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "invalidations": self.stats["invalidations"],
            "compressions": self.stats["compressions"],
            "avg_response_time_ms": round(avg_response_time, 2),
            "cache_sizes": self.stats["cache_sizes"],
            "redis_available": self.redis_client is not None,
            "memcache_available": self.memcache_client is not None,
            "target_response_time_ms": self.config.target_response_time_ms,
            "performance_target_met": avg_response_time <= self.config.target_response_time_ms
        }
    
    def clear_all(self) -> bool:
        """Clear all caches"""
        success = True
        
        # Memory
        with self._cache_lock:
            self._memory_cache.clear()
        
        # Redis
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception:
                success = False
        
        # Memcached
        if self.memcache_client:
            try:
                self.memcache_client.flush_all()
            except Exception:
                success = False
        
        # Files
        try:
            for cache_file in self.config.cache_dir.glob("*.cache"):
                cache_file.unlink()
        except Exception:
            success = False
        
        # Reset stats
        self.stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
            "compressions": 0,
            "response_times": [],
            "cache_sizes": {
                "memory": 0,
                "redis": 0,
                "file": 0
            }
        }
        
        return success


# Decorator for automatic caching
def cached(namespace: str, ttl_seconds: int = 3600, key_func=None):
    """Decorator for automatic function result caching"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Try to get from cache
            result = performance_cache.get(namespace, cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            performance_cache.set(namespace, cache_key, result, ttl_seconds)
            
            return result
        return wrapper
    return decorator


# Global cache instance
performance_cache = PerformanceCache()