from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.text import Text

console = Console()


def format_output(data: Any, table: bool = False, title: str = "") -> None:
    if isinstance(data, list):
        if table and data:
            _render_table(data, title)
        else:
            _render_json(data)
    elif isinstance(data, dict):
        if table and _is_list_like(data):
            items = _extract_items(data)
            if items:
                _render_table(items, title)
            else:
                _render_json(data)
        else:
            _render_json(data)
    else:
        _render_json(data)


def _render_json(data: Any) -> None:
    console.print_json(json.dumps(data, default=str, ensure_ascii=False))


def _render_table(items: list[dict], title: str = "") -> None:
    if not items:
        console.print("[yellow]no results[/yellow]")
        return

    keys = _common_keys(items)
    table = Table(title=title or None)
    for k in keys:
        table.add_column(k, overflow="fold")

    for item in items:
        row = [_cell(item.get(k)) for k in keys]
        table.add_row(*row)

    console.print(table)


def _cell(value: Any) -> str:
    if value is None:
        return "[dim]—[/dim]"
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)[:60]
    return str(value)


def _common_keys(items: list[dict]) -> list[str]:
    keys: set[str] = set()
    for item in items:
        keys.update(item.keys())
    ordered = [k for k in ["id", "name", "status", "type", "created_at", "updated_at"] if k in keys]
    ordered += [k for k in keys if k not in ordered]
    return ordered


def _is_list_like(data: dict) -> bool:
    for key in ("data", "items", "results", "records"):
        if key in data and isinstance(data[key], list):
            return True
    return False


def _extract_items(data: dict) -> list[dict] | None:
    for key in ("data", "items", "results", "records"):
        if key in data and isinstance(data[key], list):
            return data[key]
    return None
