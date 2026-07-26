"""Unit tests for app.live module."""

import asyncio
import json

import pytest

from app.live import LiveScanner, _parse_targets


class TestParseTargets:
    def test_default_targets(self, monkeypatch):
        monkeypatch.delenv("SCAN_TARGETS", raising=False)
        targets = _parse_targets()
        assert len(targets) == 5
        assert ("localhost", 8443) in targets
        assert ("localhost", 2222) in targets

    def test_custom_targets(self, monkeypatch):
        monkeypatch.setenv("SCAN_TARGETS", "example.com:443,10.0.0.1:8080")
        targets = _parse_targets()
        assert targets == [("example.com", 443), ("10.0.0.1", 8080)]

    def test_host_only_defaults_to_443(self, monkeypatch):
        monkeypatch.setenv("SCAN_TARGETS", "example.com")
        targets = _parse_targets()
        assert targets == [("example.com", 443)]

    def test_empty_string_gives_defaults(self, monkeypatch):
        monkeypatch.setenv("SCAN_TARGETS", "")
        targets = _parse_targets()
        assert len(targets) == 5


class TestLiveScanner:
    def test_subscribe_returns_queue(self):
        scanner = LiveScanner()
        q = scanner.subscribe()
        assert isinstance(q, asyncio.Queue)

    def test_unsubscribe_removes_queue(self):
        scanner = LiveScanner()
        q = scanner.subscribe()
        uid = scanner._counter
        scanner.unsubscribe(uid)
        assert uid not in scanner._subscribers

    def test_latest_connections_initially_empty(self):
        scanner = LiveScanner()
        assert scanner.latest_connections == []

    def test_scan_target_with_unknown_port_returns_result(self):
        scanner = LiveScanner()
        result = scanner._scan_target("localhost", 99999)
        assert "endpoint" in result
        assert result["endpoint"] == "localhost:99999"
        assert "state" in result

    def test_broadcast_sends_to_subscribers(self):
        scanner = LiveScanner()
        q1 = scanner.subscribe()
        q2 = scanner.subscribe()
        scanner._broadcast('{"test": true}')
        assert q1.get_nowait() == '{"test": true}'
        assert q2.get_nowait() == '{"test": true}'

    def test_unsubscribe_stops_broadcast(self):
        scanner = LiveScanner()
        q = scanner.subscribe()
        uid = scanner._counter
        scanner.unsubscribe(uid)
        scanner._broadcast('{"test": true}')
        assert q.empty()
