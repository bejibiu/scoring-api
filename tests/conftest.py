from store import StorageRedis
from pytest import fixture
from redis import Redis


@fixture
def storage_redis():
    return StorageRedis(host='192.168.80.147')


@fixture
def storage_set_name_value(storage_redis):
    storage_redis.redis.set(name='name', value='value')
    yield storage_redis, 'name', 'value'
    storage_redis.redis.delete('name')


@fixture
def storage_redis_offline_mock(monkeypatch):
    def mock_get_and_set_to_redis(*args, **kwargs):
        raise ConnectionError
    monkeypatch.setattr(Redis, 'get', mock_get_and_set_to_redis)
    monkeypatch.setattr(Redis, 'set', mock_get_and_set_to_redis)


@fixture
def mock_get_with_success_reconnect(monkeypatch):

    ones_raise_completed = False

    def mock_get_to_redis(*args, **kwargs):
        nonlocal ones_raise_completed
        if ones_raise_completed:
            monkeypatch.undo()
            return Redis.set(*args, **kwargs)
        ones_raise_completed = True
        raise ConnectionError

    monkeypatch.setattr(Redis, 'get', mock_get_to_redis)


@fixture
def mock_set_with_success_reconnect(monkeypatch):

    ones_raise_completed = False

    def mock_set_to_redis(*args, **kwargs):
        nonlocal ones_raise_completed
        if ones_raise_completed:
            monkeypatch.undo()
            return Redis.set(*args, **kwargs)
        ones_raise_completed = True
        raise ConnectionError

    monkeypatch.setattr(Redis, 'set', mock_set_to_redis)

