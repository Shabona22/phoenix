"""Integration tests for orchestrator with mocked Doprax API."""

from unittest.mock import MagicMock, patch

from orchestrator.config_generator import ConfigGenerator
from orchestrator.node_manager import Node, NodeManager
from orchestrator.subscription_manager import SubscriptionManager


MOCK_VMS = [
    {
        "vmCode": "vm-test-001",
        "sysName": "test-node",
        "ip": "10.0.0.1",
        "status": "running",
        "trafficUsed": 5.0,
    }
]


@patch("orchestrator.node_manager.DopraxClient")
def test_node_manager_refresh(mock_client_cls):
    mock_client = MagicMock()
    mock_client.list_vms.return_value = MOCK_VMS
    mock_client_cls.return_value = mock_client

    mgr = NodeManager(mock_client)
    nodes = mgr.refresh()
    assert len(nodes) == 1
    assert nodes[0].ip == "10.0.0.1"
    assert nodes[0].name == "test-node"


def test_config_generator_writes_files(tmp_path):
    gen = ConfigGenerator(output_dir=str(tmp_path))
    node = Node(vm_code="vm-test-001", name="test", ip="10.0.0.1", status="running")
    configs = gen.generate_for_node(node, protocols=["openvpn", "shadowsocks"])
    assert "openvpn" in configs
    assert "shadowsocks" in configs
    assert (tmp_path / "configs" / "openvpn" / "vm-test-001" / "config.json").exists()


def test_subscription_export(tmp_path):
    sub = SubscriptionManager(output_dir=str(tmp_path))
    configs = {
        "shadowsocks": {
            "config": {
                "cipher": "aes-256-gcm",
                "password": "testpass",
                "server": {"ip": "1.2.3.4", "port": 8388},
            }
        }
    }
    path = sub.export_json("node1", configs)
    assert path.exists()
    b64_path = sub.export_base64_uri_list("node1", configs)
    assert b64_path.exists()
