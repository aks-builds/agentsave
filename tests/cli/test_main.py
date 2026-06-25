import json
import os
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from agentsave.cli.main import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "agentsave" in result.output.lower()


def test_status_when_not_logged_in():
    runner = CliRunner()
    with runner.isolated_filesystem():
        import unittest.mock as mock
        with mock.patch("agentsave.cli.main._CONFIG_FILE", "/nonexistent/path/config.json"):
            result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "login" in result.output.lower()


def test_config_set_budget():
    runner = CliRunner()
    with runner.isolated_filesystem():
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_file = os.path.join(tmpdir, "config.json")
            import unittest.mock as mock
            with mock.patch("agentsave.cli.main._CONFIG_FILE", cfg_file), \
                 mock.patch("agentsave.cli.main._CONFIG_DIR", tmpdir):
                result = runner.invoke(cli, ["config", "set", "budget", "200000"])
    assert result.exit_code == 0


def test_config_set_telemetry_off():
    runner = CliRunner()
    with runner.isolated_filesystem():
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_file = os.path.join(tmpdir, "config.json")
            import unittest.mock as mock
            with mock.patch("agentsave.cli.main._CONFIG_FILE", cfg_file), \
                 mock.patch("agentsave.cli.main._CONFIG_DIR", tmpdir):
                result = runner.invoke(cli, ["config", "set", "telemetry", "off"])
    assert result.exit_code == 0


def test_login_success(tmp_path, monkeypatch):
    monkeypatch.setattr("agentsave.cli.main._CONFIG_DIR", str(tmp_path / ".agentsave"))
    monkeypatch.setattr("agentsave.cli.main._CONFIG_FILE", str(tmp_path / ".agentsave" / "config.json"))

    health_resp = MagicMock(status_code=200)
    health_resp.raise_for_status = lambda: None
    billing_resp = MagicMock(status_code=200)
    billing_resp.raise_for_status = lambda: None

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = lambda s: mock_client
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = [health_resp, billing_resp]
        mock_client_cls.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(cli, ["login"], input="http://localhost:8000\nask-testkey123\n")

    assert result.exit_code == 0, result.output
    assert "Connected" in result.output
    cfg = json.loads((tmp_path / ".agentsave" / "config.json").read_text())
    assert cfg["api_url"] == "http://localhost:8000/api/events"
    assert cfg["token"] == "ask-testkey123"
    assert cfg["telemetry"] is True


def test_login_unreachable_server(tmp_path, monkeypatch):
    monkeypatch.setattr("agentsave.cli.main._CONFIG_DIR", str(tmp_path / ".agentsave"))
    monkeypatch.setattr("agentsave.cli.main._CONFIG_FILE", str(tmp_path / ".agentsave" / "config.json"))

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = lambda s: mock_client
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = Exception("Connection refused")
        mock_client_cls.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(cli, ["login"], input="http://localhost:9999\nask-testkey\n")

    assert result.exit_code != 0
    assert "Cannot reach" in result.output


def test_login_invalid_key(tmp_path, monkeypatch):
    monkeypatch.setattr("agentsave.cli.main._CONFIG_DIR", str(tmp_path / ".agentsave"))
    monkeypatch.setattr("agentsave.cli.main._CONFIG_FILE", str(tmp_path / ".agentsave" / "config.json"))

    health_resp = MagicMock(status_code=200)
    health_resp.raise_for_status = lambda: None
    billing_resp = MagicMock(status_code=401)
    billing_resp.raise_for_status = lambda: None

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = lambda s: mock_client
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = [health_resp, billing_resp]
        mock_client_cls.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(cli, ["login"], input="http://localhost:8000\nbad-key\n")

    assert result.exit_code != 0
    assert "Invalid API key" in result.output
