from __future__ import annotations

import asyncio
import contextlib
import csv
import io
import json
import logging
import time
from pathlib import Path
from typing import Any
from xml.etree import ElementTree
from defusedxml.ElementTree import fromstring as safe_xml_parse

from .base import BaseConnector, ConnectorConfig, ConnectorResult, ConnectorStatus

logger = logging.getLogger("gula.ecosystem.file")


class FileConnector(BaseConnector):
    SUPPORTED_FORMATS = {"csv", "json", "xml", "xlsx", "txt"}

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._watch_dir: Path | None = None
        self._poll_task: asyncio.Task | None = None
        self._watch_interval: int = 30
        self._known_files: dict[str, float] = {}
        self._callback: Any = None

    async def connect(self) -> bool:
        try:
            options = self._config.options or {}
            watch_path = options.get("watch_directory") or self._config.endpoint or ""
            if watch_path:
                self._watch_dir = Path(watch_path)
                self._watch_dir.mkdir(parents=True, exist_ok=True)
            self._watch_interval = options.get("poll_interval_seconds", 30)
            self._callback = options.get("callback")
            self._connected = True
            self._status = ConnectorStatus.ACTIVE
            return True
        except Exception as exc:
            self._status = ConnectorStatus.ERROR
            self._metrics["last_error"] = str(exc)
            return False

    async def disconnect(self) -> bool:
        try:
            if self._poll_task and not self._poll_task.done():
                self._poll_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._poll_task
                self._poll_task = None
            self._connected = False
            self._status = ConnectorStatus.INACTIVE
            return True
        except Exception as exc:
            self._metrics["last_error"] = str(exc)
            return False

    async def start_watching(self, callback: Any = None) -> None:
        if self._poll_task and not self._poll_task.done():
            return
        self._callback = callback or self._callback
        self._poll_task = asyncio.create_task(self._poll_loop())

    async def stop_watching(self) -> None:
        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._poll_task
            self._poll_task = None

    async def send(self, data: Any) -> ConnectorResult:
        if not isinstance(data, dict):
            return self._build_result(False, error="data must be a dict with 'content', 'filename', and 'format'", status_code=400)

        content = data.get("content")
        filename = data.get("filename", f"output_{int(time.time())}")
        file_format = data.get("format", "json")
        directory = data.get("directory") or (str(self._watch_dir) if self._watch_dir else "")

        if not directory:
            return self._build_result(False, error="no output directory specified", status_code=400)

        if file_format not in self.SUPPORTED_FORMATS:
            return self._build_result(False, error=f"unsupported format: {file_format}", status_code=400)

        start = time.monotonic()
        try:
            path = Path(directory) / f"{filename}.{file_format}"
            path.parent.mkdir(parents=True, exist_ok=True)

            serialized = self._serialize(content, file_format)
            path.write_text(serialized, encoding="utf-8")

            duration_ms = int((time.monotonic() - start) * 1000)
            self._record_success(duration_ms)
            return self._build_result(True, data={"path": str(path), "size": len(serialized)}, duration_ms=duration_ms)

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            self._record_failure(str(exc), duration_ms)
            return self._build_result(False, error=str(exc), duration_ms=duration_ms)

    async def receive(self) -> ConnectorResult:
        if not self._watch_dir:
            return self._build_result(False, error="no watch directory configured", status_code=400)

        if not self._watch_dir.exists():
            return self._build_result(False, error=f"directory not found: {self._watch_dir}", status_code=404)

        start = time.monotonic()
        try:
            files = []
            for entry in self._watch_dir.iterdir():
                if entry.is_file() and entry.suffix.lstrip(".") in self.SUPPORTED_FORMATS:
                    mod_time = entry.stat().st_mtime
                    files.append({
                        "name": entry.name,
                        "path": str(entry),
                        "size": entry.stat().st_size,
                        "modified_at": mod_time,
                        "format": entry.suffix.lstrip("."),
                    })

            duration_ms = int((time.monotonic() - start) * 1000)
            self._record_success(duration_ms)
            return self._build_result(True, data={"directory": str(self._watch_dir), "files": files, "count": len(files)}, duration_ms=duration_ms)

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            self._record_failure(str(exc), duration_ms)
            return self._build_result(False, error=str(exc), duration_ms=duration_ms)

    async def read_file(self, filepath: str, file_format: str | None = None) -> ConnectorResult:
        start = time.monotonic()
        try:
            path = Path(filepath)
            if not path.exists():
                return self._build_result(False, error=f"file not found: {filepath}", status_code=404)

            fmt = file_format or path.suffix.lstrip(".")
            content = path.read_text(encoding="utf-8")
            parsed = self._parse(content, fmt)

            duration_ms = int((time.monotonic() - start) * 1000)
            self._record_success(duration_ms)
            return self._build_result(True, data=parsed, duration_ms=duration_ms)

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            self._record_failure(str(exc), duration_ms)
            return self._build_result(False, error=str(exc), duration_ms=duration_ms)

    async def _poll_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(self._watch_interval)
                if not self._watch_dir or not self._watch_dir.exists():
                    continue

                current_files: dict[str, float] = {}
                for entry in self._watch_dir.iterdir():
                    if entry.is_file():
                        mod_time = entry.stat().st_mtime
                        current_files[entry.name] = mod_time

                        if entry.name not in self._known_files or self._known_files.get(entry.name) != mod_time:
                            result = await self.read_file(str(entry))
                            if result.success and self._callback:
                                await self._callback(entry.name, result.data)

                self._known_files = current_files

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("File poll error: %s", exc)

    def _parse(self, content: str, fmt: str) -> Any:
        if fmt == "json":
            return json.loads(content)
        if fmt == "xml":
            root = safe_xml_parse(content)
            return self._xml_to_dict(root)
        if fmt == "csv":
            reader = csv.DictReader(io.StringIO(content))
            return list(reader)
        if fmt == "txt":
            return content
        return content

    def _serialize(self, data: Any, fmt: str) -> str:
        if fmt == "json":
            return json.dumps(data, indent=2, ensure_ascii=False, default=str)
        if fmt == "xml":
            if isinstance(data, dict):
                root_name = data.get("_root", "root")
                return ElementTree.tostring(self._dict_to_element(root_name, data), encoding="unicode")
            return str(data)
        if fmt == "csv":
            if isinstance(data, list) and data:
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
                return output.getvalue()
            return str(data)
        return str(data)

    def _xml_to_dict(self, element: ElementTree.Element) -> dict:
        result: dict = {}
        for child in element:
            if len(child):
                sub = self._xml_to_dict(child)
                if child.tag in result:
                    existing = result[child.tag]
                    if not isinstance(existing, list):
                        result[child.tag] = [existing]
                    result[child.tag].append(sub)
                else:
                    result[child.tag] = sub
            else:
                text = child.text or ""
                if child.tag in result:
                    existing = result[child.tag]
                    if not isinstance(existing, list):
                        result[child.tag] = [existing]
                    result[child.tag].append(text)
                else:
                    result[child.tag] = text
        return result

    def _dict_to_element(self, name: str, data: dict) -> ElementTree.Element:
        root = ElementTree.Element(name)
        for key, value in data.items():
            if key.startswith("_"):
                continue
            child = ElementTree.SubElement(root, key)
            if isinstance(value, dict):
                for k, v in value.items():
                    grandchild = ElementTree.SubElement(child, k)
                    grandchild.text = str(v)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        item_elem = ElementTree.SubElement(child, key)
                        for k, v in item.items():
                            ElementTree.SubElement(item_elem, k).text = str(v)
                    else:
                        ElementTree.SubElement(child, key).text = str(item)
            else:
                child.text = str(value)
        return root
