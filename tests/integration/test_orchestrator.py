"""Integration tests for orchestrator with mocked Doprax API."""

from unittest.mock import MagicMock, patch

from orchestrator.api_client import DopraxClient
from orchestrator.config_generator import ConfigGenerator
from orchestrator.node_manager import Node, NodeManager
from orchestrator.subscription_manager import SubscriptionManager


MOCK_VMS = [
    {
        "vmCode": "vm-test-001",
        "sysName": "test-node",
        "ipv4": "10.0.0.1",
        "status": "running",
        "trafficUsed": 5.0,
        "country": "TR",
        "locationName": "Istanbul",
    },
    {
        "vmCode": "vm-de-001",
        "sysName": "germany-node",
        "ipv4": "10.0.0.2",
        "status": "running",
        "country": "Germany",
        "locationName": "Germany",
    },
    {
        "vmCode": "vm-fr-001",
        "sysName": "france-node",
        "ipv4": "10.0.0.3",
        "status": "running",
        "country": "FR",
        "locationName": "FR, Paris",
    },
]


@patch("orchestrator.node_manager.DopraxClient")
def test_node_manager_refresh(mock_client_cls):
    mock_client = MagicMock()
    mock_client.list_vms.return_value = MOCK_VMS
    mock_client_cls.return_value = mock_client

    mgr = NodeManager(mock_client)
    nodes = mgr.refresh()
    assert len(nodes) == 3
    assert nodes[0].ip == "10.0.0.1"
    assert nodes[0].name == "test-node"


@patch("orchestrator.node_manager.DopraxClient")
def test_location_exclusion_filter(mock_client_cls):
    mock_client = MagicMock()
    mock_client.list_vms.return_value = MOCK_VMS
    mock_client_cls.return_value = mock_client

    mgr = NodeManager(mock_client)
    mgr.refresh()
    active = mgr.list_nodes()
    all_nodes = mgr.list_all_nodes()
    assert len(all_nodes) == 3
    assert len(active) == 1
    assert active[0].vm_code == "vm-test-001"
    assert mgr.list_nodes()[0].is_excluded is False
    assert mgr.list_all_nodes()[1].is_excluded is True


@patch("orchestrator.node_manager.DopraxClient")
def test_provision_node_v2_metadata(mock_client_cls):
    mock_client = MagicMock()
    mock_client.create_vm.return_value = {
        "service_id": "svc-123",
        "status": "pending",
        "metadata": {"vm_code": "vm-new-001"},
        "name": "phoenix-test",
    }
    mock_client_cls.return_value = mock_client

    mgr = NodeManager(mock_client)
    node = mgr.provision_node(
        {
            "product_version_id": "abc-123",
            "name": "phoenix-test",
            "selections": {"location": {"code": "gcore_50"}},
        }
    )
    assert node.vm_code == "vm-new-001"
    assert node.status == "pending"
    mock_client.create_vm.assert_called_once()


def test_create_vm_routes_to_v2():
    client = DopraxClient(api_key="test-key")
    client._request = MagicMock(return_value={"data": {"status": "pending"}})
    client.create_vm({"product_version_id": "pv-1", "name": "n1"})
    assert client._request.call_count == 1
    args, kwargs = client._request.call_args
    assert args == ("POST", "/api/v2/services/instances/")
    assert kwargs["data"]["product_version_id"] == "pv-1"
    assert kwargs["data"]["name"] == "n1"
    assert "idempotency_key" in kwargs["data"]


@patch("orchestrator.node_manager.DopraxClient")
def test_enrich_node_ips(mock_client_cls):
    mock_client = MagicMock()
    mock_client.list_vms.return_value = [
        {"vmCode": "vm-1", "sysName": "n1", "status": "running"},
    ]
    mock_client.get_vm.return_value = {"ipv4": "203.0.113.1"}
    mock_client_cls.return_value = mock_client

    mgr = NodeManager(mock_client)
    mgr.refresh()
    node = mgr.list_all_nodes()[0]
    assert node.ip == ""
    mgr.enrich_node_ips(node)
    assert node.ip == "203.0.113.1"


@patch("orchestrator.node_manager.DopraxClient")
def test_enrich_node_ips_from_get_ips(mock_client_cls):
    mock_client = MagicMock()
    mock_client.list_vms.return_value = [
        {"vmCode": "vm-2", "sysName": "n2", "status": "running"},
    ]
    mock_client.get_vm.return_value = {}
    mock_client.get_ips.return_value = [{"version": 4, "address": "203.0.113.2"}]
    mock_client_cls.return_value = mock_client

    mgr = NodeManager(mock_client)
    mgr.refresh()
    node = mgr.list_all_nodes()[0]
    mgr.enrich_node_ips(node)
    assert node.ip == "203.0.113.2"


def test_config_generator_writes_files(tmp_path):
    gen = ConfigGenerator(output_dir=str(tmp_path))
    node = Node(vm_code="vm-test-001", name="test", ip="10.0.0.1", status="running")
    configs = gen.generate_for_node(node, protocols=["openvpn", "shadowsocks"])
    assert "openvpn" in configs
    assert "shadowsocks" in configs
    assert (tmp_path / "configs" / "openvpn" / "vm-test-001" / "config.json").exists()
    assert (tmp_path / "configs" / "openvpn" / "vm-test-001" / "server.conf").exists()
    assert (tmp_path / "configs" / "shadowsocks" / "vm-test-001" / "config.json").exists()


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
