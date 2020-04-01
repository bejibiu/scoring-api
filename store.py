import redis
import logging
import functools


def retry_command(retry_connection=3):
    def decorator(f):
        @functools.wraps(f)
        def reconnector(*args, **kwargs):
            retry_connection_ = args[0].retry_connection if isinstance(args[0], StorageRedis) else retry_connection
            try:
                return f(*args, **kwargs)
            except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
                while retry_connection_ > 0:
                    logging.info(f"connection lost. {retry_connection_} attempts left")
                    try:
                        return f(*args, **kwargs)
                    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
                        retry_connection_ -= 1
                logging.error("connection failed")
                raise e
        return reconnector
    return decorator


class StorageRedis:

    def __init__(self, host="127.0.0.1", port=6379, retry_connection=3, timeout_connection=None):
        self.redis = redis.Redis(host=host, port=port, socket_timeout=timeout_connection)
        self.retry_connection = retry_connection

    def cache_get(self, key):
        try:
            return self.get(key)
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
            return None

    @retry_command()
    def get(self, key):
        result = self.redis.get(key)
        return result.decode() if result else None

    def cache_set(self, key, score, cached_time):
        try:
            return self.set(key, score, cached_time)
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
            return None

    @retry_command()
    def set(self, key, value, ex=None):
        return self.redis.set(name=key, value=value, ex=ex)

    @retry_command()
    def remove(self, key):
        return self.redis.delete(key)
