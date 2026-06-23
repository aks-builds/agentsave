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
