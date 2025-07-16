import os


class CacheManager:
    def __init__(self):
        REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
        REDIS_URL = os.getenv("REDIS_URL")
        if REDIS_ENABLED:
            from cache.redis_cache import RedisCache

            self.cache = RedisCache(redis_url=REDIS_URL)
        else:
            from cache.memory_cache import MemoryCache

            self.cache = MemoryCache()

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache.set(key, value)

    def clear(self):
        self.cache.clear()
