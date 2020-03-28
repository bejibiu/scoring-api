from store import StorageRedis
from pytest import fixture
from redis import Redis


@fixture
def storage_redis():
    return StorageRedis()


@fixture
def storage_set_name_value(storage_redis):
    storage_redis.redis.set(name='name', value='value')
    yield storage_redis, 'name', 'value'
    storage_redis.redis.delete('name')


@fixture
def storage_set_name_value_to_offline(monkeypatch):
    def mock_get_and_set_to_redis(*args, **kwargs):
        raise ConnectionError
    monkeypatch.setattr(Redis, 'get', mock_get_and_set_to_redis)
    monkeypatch.setattr(Redis, 'set', mock_get_and_set_to_redis)


@fixture
def storage_set_name_value_to_success_reconnect(monkeypatch):

    def mock_get_to_redis(*args, **kwargs):
        monkeypatch.setattr(Redis, 'get', Redis.get)
        return ConnectionError

    def mock_set_to_redis(*args, **kwargs):
        monkeypatch.setattr(Redis, 'set', Redis.set)
        return ConnectionError

    monkeypatch.setattr(Redis, 'get', mock_get_to_redis)
    monkeypatch.setattr(Redis, 'set', mock_set_to_redis)
