import redis
import logging


class StorageRedis:

    def __init__(self, host="127.0.0.1", port=6379, retry_connection=3, timeout_connection=None):
        self.redis = redis.Redis(host=host, port=port, socket_timeout=timeout_connection)
        self.retry_connection = retry_connection

    def cache_get(self, key):
        try:
            result = self.retry_command(self.redis.get, key)
        except (ConnectionError, TimeoutError):
            return None
        return result.decode() if result else None

    def get(self, key):
        result = self.retry_command(self.redis.get, key)
        return result.decode() if result else None

    def cache_set(self, key, score, cached_time):
        try:
            return self.retry_command(self.redis.set, name=key, value=score, ex=cached_time)
        except (ConnectionError, TimeoutError):
            return None

    def set(self, key, value):
        return self.retry_command(self.redis.set, name=key, value=value)

    def remove(self, key):
        return self.retry_command(self.redis.delete, key)

    def retry_command(self, command, *args, **kwargs):
        retry_connection = self.retry_connection
        try:
            return command(*args, **kwargs)
        except (ConnectionError, TimeoutError) as e:
            while retry_connection > 0:
                logging.info(f"connection lost. {retry_connection} attempts left")
                try:
                    return command(*args, **kwargs)
                except (ConnectionError, TimeoutError):
                    retry_connection -= 1
            logging.error("connection failed")
            raise e
