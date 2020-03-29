import logging

import pytest


def test_storage_cache_set_redis(storage_redis):
    assert storage_redis.cache_set("123", "123", 30) is True


def test_storage_get_from_redis(storage_set_name_value):
    storage_redis, name, value = storage_set_name_value
    assert storage_redis.get(name) == value
    assert storage_redis.cache_get(name) == value


def test_get_command_reconnect_if_connection_lost(storage_redis, storage_set_name_value_to_offline):
    with pytest.raises(ConnectionError):
        storage_redis.get("123")


def test_cached_set_reconnect_if_connection_lost(storage_redis, storage_set_name_value_to_offline):
    assert storage_redis.cache_get("123") is None


def test_cached_get_reconnect_if_connection_lost(storage_redis, storage_set_name_value_to_offline):
    with pytest.raises(ConnectionError):
        storage_redis.cache_set("123", "123", 30)


def test_cached_get_reconnect_if_reconnection_success(storage_redis, mock_set_with_success_reconnect, caplog):
    caplog.set_level(logging.INFO)
    storage_redis.cache_set("123", "123", 30)
    assert any("connection lost" in record.message for record in caplog.records)
    assert storage_redis.get("123") == "123"
