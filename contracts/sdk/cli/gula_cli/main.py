from __future__ import annotations

import json
import sys

import click

from .client import GulaClient
from .config import Config
from .formatters import format_output

_PASS_CLIENT = click.make_pass_decorator(GulaClient, ensure=True)


@click.group()
@click.option("--base-url", "-u", envvar="GULA_BASE_URL", help="API base URL")
@click.version_option(version="1.0.0", prog_name="gula")
@click.pass_context
def cli(ctx: click.Context, base_url: str | None) -> None:
    """GULA Platform CLI — laboratory information management from the terminal."""
    cfg = Config()
    if base_url:
        cfg.base_url = base_url
    ctx.obj = GulaClient(cfg)


@cli.group()
def auth() -> None:
    """Authentication commands."""


@auth.command("login")
@click.option("--email", "-e", prompt=True, help="Account email")
@click.option("--password", "-p", prompt=True, hide_input=True, help="Account password")
@_PASS_CLIENT
def auth_login(client: GulaClient, email: str, password: str) -> None:
    """Login and store JWT token."""
    result = client.login(email, password)
    cfg = Config()
    cfg.token = result.get("access_token") or result.get("token")
    cfg.refresh_token = result.get("refresh_token")
    click.secho("login successful", fg="green")


@auth.command("refresh")
@_PASS_CLIENT
def auth_refresh(client: GulaClient) -> None:
    """Refresh stored JWT token."""
    result = client.refresh_token()
    cfg = Config()
    cfg.token = result.get("access_token") or result.get("token")
    cfg.refresh_token = result.get("refresh_token")
    click.secho("token refreshed", fg="green")


@cli.group()
def patients() -> None:
    """Patient commands."""


@patients.command("list")
@click.option("--search", "-s", help="Search term")
@click.option("--page", default=1, show_default=True, help="Page number")
@click.option("--limit", default=50, show_default=True, help="Items per page")
@click.option("--table", "-t", is_flag=True, help="Table output")
@_PASS_CLIENT
def patients_list(client: GulaClient, search: str | None, page: int, limit: int, table: bool) -> None:
    """List patients."""
    result = client.list_patients(page=page, limit=limit, search=search)
    format_output(result, table=table, title="Patients")


@patients.command("get")
@click.argument("patient_id", type=int)
@_PASS_CLIENT
def patients_get(client: GulaClient, patient_id: int) -> None:
    """Get patient by ID."""
    result = client.get_patient(patient_id)
    format_output(result)


@patients.command("create")
@click.option("--json", "json_str", help="JSON data (inline or file://path)")
@_PASS_CLIENT
def patients_create(client: GulaClient, json_str: str | None) -> None:
    """Create a new patient (interactive or --json)."""
    if json_str:
        if json_str.startswith("file://"):
            with open(json_str[7:]) as f:
                data = json.load(f)
        else:
            data = json.loads(json_str)
    else:
        click.echo("Enter patient details (Ctrl+D to finish):")
        data = json.loads(sys.stdin.read())
    result = client.create_patient(data)
    format_output(result)


@cli.group()
def orders() -> None:
    """Order commands."""


@orders.command("list")
@click.option("--page", default=1, show_default=True, help="Page number")
@click.option("--limit", default=50, show_default=True, help="Items per page")
@click.option("--table", "-t", is_flag=True, help="Table output")
@_PASS_CLIENT
def orders_list(client: GulaClient, page: int, limit: int, table: bool) -> None:
    """List orders."""
    result = client.list_orders(page=page, limit=limit)
    format_output(result, table=table, title="Orders")


@orders.command("get")
@click.argument("order_id", type=int)
@_PASS_CLIENT
def orders_get(client: GulaClient, order_id: int) -> None:
    """Get order by ID."""
    result = client.get_order(order_id)
    format_output(result)


@orders.command("create")
@click.option("--json", "json_str", help="JSON data (inline or file://path)")
@_PASS_CLIENT
def orders_create(client: GulaClient, json_str: str | None) -> None:
    """Create an order."""
    if json_str:
        if json_str.startswith("file://"):
            with open(json_str[7:]) as f:
                data = json.load(f)
        else:
            data = json.loads(json_str)
    else:
        click.echo("Enter order data (Ctrl+D to finish):")
        data = json.loads(sys.stdin.read())
    result = client.create_order(data)
    format_output(result)


@cli.group()
def results() -> None:
    """Result commands."""


@results.command("list")
@click.option("--page", default=1, show_default=True, help="Page number")
@click.option("--limit", default=50, show_default=True, help="Items per page")
@click.option("--table", "-t", is_flag=True, help="Table output")
@_PASS_CLIENT
def results_list(client: GulaClient, page: int, limit: int, table: bool) -> None:
    """List lab results."""
    result = client.list_results(page=page, limit=limit)
    format_output(result, table=table, title="Results")


@results.command("get")
@click.argument("result_id", type=int)
@_PASS_CLIENT
def results_get(client: GulaClient, result_id: int) -> None:
    """Get result by ID."""
    result = client.get_result(result_id)
    format_output(result)


@cli.group()
def labs() -> None:
    """Lab commands."""


@labs.command("list")
@click.option("--page", default=1, show_default=True, help="Page number")
@click.option("--limit", default=50, show_default=True, help="Items per page")
@click.option("--table", "-t", is_flag=True, help="Table output")
@_PASS_CLIENT
def labs_list(client: GulaClient, page: int, limit: int, table: bool) -> None:
    """List labs."""
    result = client.list_labs(page=page, limit=limit)
    format_output(result, table=table, title="Labs")


@labs.command("get")
@click.argument("lab_id", type=int)
@_PASS_CLIENT
def labs_get(client: GulaClient, lab_id: int) -> None:
    """Get lab by ID."""
    result = client.get_lab(lab_id)
    format_output(result)


@cli.group()
def samples() -> None:
    """Sample commands."""


@samples.command("list")
@click.option("--page", default=1, show_default=True, help="Page number")
@click.option("--limit", default=50, show_default=True, help="Items per page")
@click.option("--table", "-t", is_flag=True, help="Table output")
@_PASS_CLIENT
def samples_list(client: GulaClient, page: int, limit: int, table: bool) -> None:
    """List samples."""
    result = client.list_samples(page=page, limit=limit)
    format_output(result, table=table, title="Samples")


@samples.command("get")
@click.argument("sample_id", type=int)
@_PASS_CLIENT
def samples_get(client: GulaClient, sample_id: int) -> None:
    """Get sample by ID."""
    result = client.get_sample(sample_id)
    format_output(result)


@cli.group()
def consent() -> None:
    """Consent commands."""


@consent.command("grant")
@click.option("--json", "json_str", required=True, help='JSON: {"gpid": "...", "grantee_id": "...", "scope": "...", "expires_in_hours": N}')
@_PASS_CLIENT
def consent_grant(client: GulaClient, json_str: str) -> None:
    """Grant consent."""
    data = json.loads(json_str) if not json_str.startswith("file://") else json.load(open(json_str[7:]))
    result = client.grant_consent(data)
    format_output(result)


@consent.command("check")
@click.option("--gpid", required=True, help="Citizen ULID")
@click.option("--scope", required=True, help="Consent scope")
@_PASS_CLIENT
def consent_check(client: GulaClient, gpid: str, scope: str) -> None:
    """Check consent."""
    result = client.check_consent(gpid, scope)
    format_output(result)


@cli.group()
def claims() -> None:
    """Claim commands."""


@claims.command("list")
@click.option("--page", default=1, show_default=True, help="Page number")
@click.option("--limit", default=50, show_default=True, help="Items per page")
@click.option("--table", "-t", is_flag=True, help="Table output")
@_PASS_CLIENT
def claims_list(client: GulaClient, page: int, limit: int, table: bool) -> None:
    """List claims."""
    result = client.list_claims(page=page, limit=limit)
    format_output(result, table=table, title="Claims")


@claims.command("create")
@click.option("--json", "json_str", required=True, help='JSON: {"patient_id": N, "items": [...]}')
@_PASS_CLIENT
def claims_create(client: GulaClient, json_str: str) -> None:
    """Create a claim."""
    data = json.loads(json_str) if not json_str.startswith("file://") else json.load(open(json_str[7:]))
    result = client.create_claim(data)
    format_output(result)


@cli.group()
def edge() -> None:
    """Edge platform commands."""


@edge.command("devices")
@click.option("--page", default=1, show_default=True, help="Page number")
@click.option("--limit", default=50, show_default=True, help="Items per page")
@click.option("--table", "-t", is_flag=True, help="Table output")
@_PASS_CLIENT
def edge_devices(client: GulaClient, page: int, limit: int, table: bool) -> None:
    """List edge devices."""
    result = client.edge_list_devices(page=page, limit=limit)
    format_output(result, table=table, title="Edge Devices")


@edge.command("tasks")
@click.option("--page", default=1, show_default=True, help="Page number")
@click.option("--limit", default=50, show_default=True, help="Items per page")
@click.option("--table", "-t", is_flag=True, help="Table output")
@_PASS_CLIENT
def edge_tasks(client: GulaClient, page: int, limit: int, table: bool) -> None:
    """List edge tasks."""
    result = client.edge_list_tasks(page=page, limit=limit)
    format_output(result, table=table, title="Edge Tasks")


@cli.group()
def compliance() -> None:
    """Compliance commands."""


@compliance.group()
def fhir() -> None:
    """FHIR resource commands."""


@fhir.command("patient")
@click.argument("patient_id")
@_PASS_CLIENT
def fhir_patient(client: GulaClient, patient_id: str) -> None:
    """Get FHIR Patient resource."""
    result = client.fhir_get_patient(patient_id)
    format_output(result)


@fhir.command("observation")
@click.argument("observation_id")
@_PASS_CLIENT
def fhir_observation(client: GulaClient, observation_id: str) -> None:
    """Get FHIR Observation resource."""
    result = client.fhir_get_observation(observation_id)
    format_output(result)


@cli.command()
@click.option("--json", "json_str", required=True, help='JSON: {"lab_id": N, "patient_id": N, ...}')
@_PASS_CLIENT
def mpi(client: GulaClient, json_str: str) -> None:
    """Resolve identity via Master Patient Index."""
    data = json.loads(json_str) if not json_str.startswith("file://") else json.load(open(json_str[7:]))
    result = client.mpi_resolve(data)
    format_output(result)


@cli.group()
def stats() -> None:
    """Statistics commands."""


@stats.command("dashboard")
@click.option("--table", "-t", is_flag=True, help="Table output")
@_PASS_CLIENT
def stats_dashboard(client: GulaClient, table: bool) -> None:
    """Get dashboard statistics."""
    result = client.stats_dashboard()
    format_output(result, table=table, title="Dashboard Stats")


@cli.command()
@_PASS_CLIENT
def health(client: GulaClient) -> None:
    """Check system health."""
    result = client.health()
    format_output(result)


@cli.command("test-types")
@click.option("--table", "-t", is_flag=True, help="Table output")
@_PASS_CLIENT
def test_types(client: GulaClient, table: bool) -> None:
    """List available test types."""
    result = client.test_types()
    format_output(result, table=table, title="Test Types")


@cli.command()
@click.option("--base-url", "-u", help="API base URL")
@click.option("--token", "-t", help="Auth token")
@click.option("--refresh-token", "-r", help="Refresh token")
def configure(base_url: str | None, token: str | None, refresh_token: str | None) -> None:
    """Set base URL and auth configuration."""
    cfg = Config()
    if base_url:
        cfg.base_url = base_url
        click.secho(f"base URL set to {base_url}", fg="green")
    if token:
        cfg.token = token
        click.secho("token saved", fg="green")
    if refresh_token:
        cfg.refresh_token = refresh_token
        click.secho("refresh token saved", fg="green")
    if not any([base_url, token, refresh_token]):
        click.echo(f"Base URL: {cfg.base_url}")
        click.echo(f"Token: {'set' if cfg.token else 'not set'}")
        click.echo(f"Refresh token: {'set' if cfg.refresh_token else 'not set'}")
