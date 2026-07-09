"""Integration test for fallback chain simulation."""

from unittest.mock import MagicMock

from healer.fallback_manager import FallbackManager
from healer.heartbeat import Heartbeat
from orchestrator.node_manager import Node, NodeManager


def _make_manager_with_nodes():
    client = MagicMock()
    client.list_vms.return_value = [
        {"vmCode": "vm-1", "sysName": "node-1", "ip": "1.1.1.1", "status": "running"},
        {"vmCode": "vm-2", "sysName": "node-2", "ip": "2.2.2.2", "status": "running"},
    ]
    return NodeManager(client)


def test_fallback_protocol_chain():
    mgr = _make_manager_with_nodes()
    mgr.refresh()
    fb = FallbackManager(mgr)
    assert fb.current_protocol == "openvpn_http2"
    assert fb.switch_protocol() is True
    assert fb.current_protocol == "l2tp_websocket"


def test_fallback_legacy_mode():
    mgr = _make_manager_with_nodes()
    fb = FallbackManager(mgr, dbf_mode=False)
    assert fb.current_protocol == "xray"


def test_fallback_node_switch():
    mgr = _make_manager_with_nodes()
    mgr.refresh()
    fb = FallbackManager(mgr)
    assert fb.switch_node() is True


def test_emergency_mode():
    mgr = _make_manager_with_nodes()
    fb = FallbackManager(mgr)
    fb.emergency_mode()
    assert fb.emergency is True


def test_heartbeat_ping_without_network():
    hb = Heartbeat(interval=1)
    result = hb.ping()
    assert isinstance(result, bool)
