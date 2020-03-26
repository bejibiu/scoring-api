import redis
import logging


class StorageRedis:

    def __init__(self, host='localhost'):
        self.redis = redis.Redis(host=host)
        self.retry_connection = 3

    def cache_get(self, key):
        return self.retry_command(self.redis.get, key).decode()

    def get(self, key):
        return self.retry_command(self.redis.get, key).decode()

    def cache_set(self, key, score, cached_time):
        return self.retry_command(self.redis.set, name=key, value=score)

    def retry_command(self, command, *args, **kwargs):
        retry_connection = self.retry_connection
        try:
            return command(*args, **kwargs)
        except (ConnectionError, TimeoutError) as e:
            while retry_connection > 0:
                logging.info(f"connection lost. {retry_connection} attempt reconnect of {self.retry_connection}")
                try:
                    return command(*args, **kwargs)
                except (ConnectionError, TimeoutError):
                    retry_connection -= 1
            logging.error("connectrion failed")
            raise e
