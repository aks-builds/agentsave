import json
import os
import click
from rich.console import Console
from rich.table import Table

_CONFIG_DIR = os.path.expanduser("~/.agentsave")
_CONFIG_FILE = os.path.join(_CONFIG_DIR, "config.json")
console = Console()


def _load_config() -> dict:
    if not os.path.exists(_CONFIG_FILE):
        return {}
    with open(_CONFIG_FILE) as f:
        return json.load(f)


def _save_config(cfg: dict) -> None:
    os.makedirs(_CONFIG_DIR, exist_ok=True)
    with open(_CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


@click.group()
@click.version_option(package_name="agentsave")
def cli():
    """AgentSave — save 30% on AI agent costs. One line of code."""
    pass


@cli.command()
def login():
    """Connect to your self-hosted AgentSave dashboard."""
    url = click.prompt("Dashboard URL", default="http://localhost:8000")
    url = url.rstrip("/")
    key = click.prompt("API key", hide_input=True)

    import httpx
    try:
        with httpx.Client(timeout=5.0) as client:
            client.get(f"{url}/api/health").raise_for_status()
            resp = client.get(
                f"{url}/api/billing",
                headers={"Authorization": f"Bearer {key}"},
            )
            if resp.status_code == 401:
                console.print("[red]✗ Invalid API key.[/red]")
                raise SystemExit(1)
            resp.raise_for_status()
    except SystemExit:
        raise
    except Exception as exc:
        console.print(f"[red]✗ Cannot reach {url}: {exc}[/red]")
        raise SystemExit(1)

    cfg = _load_config()
    cfg["api_url"] = f"{url}/api/events"
    cfg["token"] = key
    cfg["telemetry"] = True
    _save_config(cfg)
    console.print("[bold green]✓ Connected. Telemetry enabled.[/bold green]")


@cli.command()
def status():
    """Show today's savings summary."""
    cfg = _load_config()
    if not cfg.get("token"):
        console.print("[yellow]Not logged in. Run [bold]agentsave login[/bold] to connect your dashboard.[/yellow]")
        return
    console.print("[bold]AgentSave status[/bold]")
    console.print(f"  Dashboard: {cfg.get('api_url', '(not connected)')}")
    console.print(f"  Telemetry: {'[green]enabled[/green]' if cfg.get('telemetry') else '[red]disabled[/red]'}")
    console.print(f"  Default budget: {cfg.get('budget', 100_000):,} tokens")


@cli.group()
def config():
    """Manage AgentSave configuration."""
    pass


@config.command("set")
@click.argument("key", type=click.Choice(["budget", "telemetry", "api_url"]))
@click.argument("value")
def config_set(key: str, value: str):
    """Set a configuration value. Keys: budget, telemetry, api_url."""
    cfg = _load_config()
    if key == "budget":
        cfg["budget"] = int(value)
        console.print(f"[green]✓ Default budget set to {int(value):,} tokens.[/green]")
    elif key == "telemetry":
        cfg["telemetry"] = value.lower() not in ("off", "false", "0", "no")
        state = "enabled" if cfg["telemetry"] else "disabled"
        console.print(f"[green]✓ Telemetry {state}.[/green]")
    elif key == "api_url":
        cfg["api_url"] = value
        console.print(f"[green]✓ API URL set to {value}.[/green]")
    _save_config(cfg)
