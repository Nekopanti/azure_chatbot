# import redis


# class RedisCache:
#     def __init__(self, redis_url="redis://localhost:6379/0"):
#         self.client = redis.Redis.from_url(redis_url)

#     def get(self, key):
#         val = self.client.get(key)
#         if val is None:
#             return None
#         return val.decode("utf-8")

#     def set(self, key, value):
#         self.client.set(key, value)

#     def clear(self):
#         self.client.flushdb()
