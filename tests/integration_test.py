import logging

import pytest

from scoring import get_score, get_interests


def test_storage_cache_set_redis(storage_redis):
    assert storage_redis.cache_set("123", "123", 30) is True


def test_storage_get_from_redis(storage_set_name_value):
    storage_redis, name, value = storage_set_name_value
    assert storage_redis.get(name) == value
    assert storage_redis.cache_get(name) == value


def test_get_command_reconnect_if_connection_lost(storage_redis, storage_redis_offline_mock):
    with pytest.raises(ConnectionError):
        storage_redis.get("123")


def test_cached_set_reconnect_if_connection_lost(storage_redis, storage_redis_offline_mock):
    assert storage_redis.cache_get("123") is None


def test_cached_get_reconnect_if_connection_lost(storage_redis, storage_redis_offline_mock):
    with pytest.raises(ConnectionError):
        storage_redis.cache_set("123", "123", 30)


def test_cached_get_reconnect_if_reconnection_success(storage_redis, mock_set_with_success_reconnect, caplog):
    caplog.set_level(logging.INFO)
    storage_redis.cache_set("123", "123", 30)
    assert any("connection lost" in record.message for record in caplog.records)
    assert storage_redis.get("123") == "123"


def test_get_score_if_redis_offline(storage_redis, storage_redis_offline_mock):
    score = get_score(storage_redis, phone="799944433221", email="temp@mail.com")
    assert score == 3.0


def test_get_interests_if_redis_offline(storage_redis, storage_redis_offline_mock):
    with pytest.raises(ConnectionError):
        get_interests(storage_redis, 1)
