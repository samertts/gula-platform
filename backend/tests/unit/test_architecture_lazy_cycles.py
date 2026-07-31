"""Unit tests for runtime-aware circular dependency detection (L2).

All previously flagged cycles (database↔self_healing, kernel.*, national.*)
are deferred-import-safe: one direction is under ``if TYPE_CHECKING:`` or
inside a function body, which never executes at module import time.
"""

from __future__ import annotations

import pathlib
import sys
import textwrap

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts import architecture_compliance_engine as ace


def _write_module(tmp_path: pathlib.Path, name: str, source: str) -> pathlib.Path:
    p = tmp_path / f"{name}.py"
    p.write_text(textwrap.dedent(source), encoding="utf-8")
    return p


class TestImportScopes:
    def test_module_scope_import(self, tmp_path):
        f = _write_module(tmp_path, "m", "import os\n")
        imports = ace.parse_imports(f)
        assert imports[0]["scope"] == "module"

    def test_function_scope_import(self, tmp_path):
        f = _write_module(tmp_path, "m", "def f():\n    import os\n")
        imports = ace.parse_imports(f)
        assert imports[0]["scope"] == "function"

    def test_type_checking_import(self, tmp_path):
        f = _write_module(tmp_path, "m", "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import os\n")
        imports = ace.parse_imports(f)
        scopes = {i["scope"] for i in imports}
        assert "type_checking" in scopes

    def test_nested_type_checking_restored(self, tmp_path):
        f = _write_module(
            tmp_path,
            "m",
            "if TYPE_CHECKING:\n    import os\nimport sys\n",
        )
        imports = ace.parse_imports(f)
        assert {i["module"] for i in imports if i["scope"] == "module"} == {"sys"}


class TestRuntimeCycleDetection:
    def test_module_scope_cycle_detected(self, tmp_path):
        _write_module(tmp_path, "a", "import b\n")
        _write_module(tmp_path, "b", "import a\n")
        graph = ace.build_import_graph(tmp_path, set())
        assert ace.find_cycles(graph)

    def test_function_scope_cycle_not_detected(self, tmp_path):
        _write_module(tmp_path, "a", "import b\n")
        _write_module(tmp_path, "b", "def f():\n    import a\n")
        graph = ace.build_import_graph(tmp_path, set())
        assert not ace.find_cycles(graph)

    def test_type_checking_cycle_not_detected(self, tmp_path):
        _write_module(tmp_path, "a", "import b\n")
        _write_module(tmp_path, "b", "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import a\n")
        graph = ace.build_import_graph(tmp_path, set())
        assert not ace.find_cycles(graph)

    def test_runtime_only_false_includes_deferred(self, tmp_path):
        _write_module(tmp_path, "a", "import b\n")
        _write_module(tmp_path, "b", "def f():\n    import a\n")
        graph = ace.build_import_graph(tmp_path, set(), runtime_only=False)
        assert ace.find_cycles(graph)

    def test_lazy_cycle_in_check_circular_dependencies(self, tmp_path):
        _write_module(tmp_path, "a", "import b\n")
        _write_module(tmp_path, "b", "def f():\n    import a\n")
        result = ace.check_circular_dependencies(tmp_path, set())
        assert result["status"] == ace.PASS


class TestRealRepoL2:
    def test_no_runtime_cycles_in_backend(self):
        root = pathlib.Path(__file__).resolve().parents[3] / "backend" / "app"
        result = ace.check_circular_dependencies(root, {"tests", "migrations"})
        assert result["status"] == ace.PASS, result["details"]

    def test_database_self_healing_cycle_is_deferred(self):
        database = (pathlib.Path(__file__).resolve().parents[3] / "backend" / "app" / "database.py").resolve()
        sh = (pathlib.Path(__file__).resolve().parents[3] / "backend" / "app" / "core" / "self_healing.py").resolve()
        db_imports = ace.parse_imports(database)
        sh_imports = ace.parse_imports(sh)
        db_to_sh = [i for i in db_imports if "self_healing" in i["module"]]
        sh_to_db = [i for i in sh_imports if "database" in i["module"]]
        assert db_to_sh and sh_to_db, "expected both directions of the import"
        assert all(i["scope"] == "function" for i in db_to_sh), "database→self_healing must be deferred"
        assert all(i["scope"] == "function" for i in sh_to_db), "self_healing→database must be deferred"
