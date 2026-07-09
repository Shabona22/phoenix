"""Unit tests for MikroTik deploy orchestration."""

from __future__ import annotations

from unittest.mock import MagicMock

from mikrotik.advanced_config_generator import SCRIPT_ORDER
from mikrotik.deploy_winbox import deploy_via_api


def test_deploy_via_api_all_scripts(tmp_path):
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector.upload_script.return_value = True
    mock_connector.run_script.return_value = "[]"

    results = deploy_via_api(
        "192.168.88.1",
        "admin",
        "pass",
        connector=mock_connector,
    )

    assert len(results) == len(SCRIPT_ORDER)
    for name in SCRIPT_ORDER:
        assert results[name]["uploaded"] is True
        assert results[name]["run"] is True
    assert mock_connector.upload_script.call_count == len(SCRIPT_ORDER)
    mock_connector.close.assert_not_called()


def test_deploy_connection_failure():
    mock_connector = MagicMock()
    mock_connector.connect.return_value = False

    results = deploy_via_api("192.168.88.1", "admin", "pass", connector=mock_connector)

    assert mock_connector.connect.called
    for name in SCRIPT_ORDER:
        assert results[name]["uploaded"] is False
        assert results[name]["error"] == "connection failed"
    mock_connector.upload_script.assert_not_called()


def test_deploy_upload_failure():
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector.upload_script.return_value = False

    results = deploy_via_api("192.168.88.1", "admin", "pass", connector=mock_connector)

    first = SCRIPT_ORDER[0]
    assert results[first]["uploaded"] is False
    assert results[first]["error"] == "upload failed"


def test_deploy_script_order():
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector.upload_script.return_value = True
    mock_connector.run_script.return_value = "[]"

    deploy_via_api("192.168.88.1", "admin", "pass", connector=mock_connector)

    upload_names = [call.args[0] for call in mock_connector.upload_script.call_args_list]
    assert upload_names == list(SCRIPT_ORDER)


def test_deploy_does_not_close_injected_connector():
    mock_connector = MagicMock()
    mock_connector.connect.return_value = True
    mock_connector.upload_script.return_value = True
    mock_connector.run_script.return_value = "[]"

    deploy_via_api("192.168.88.1", "admin", "pass", connector=mock_connector)
    mock_connector.close.assert_not_called()
