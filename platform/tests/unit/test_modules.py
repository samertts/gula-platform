import pytest


class TestModule:
    def test_module_decorator_registers(self):
        from platform.core.modules import module
        from platform.core.modules.registrar import get_registered_modules

        @module(
            name="test.my_module",
            version="0.1.0",
            description="A test module",
        )
        class MyTestModule:
            pass

        modules = get_registered_modules()
        assert "test.my_module" in modules
        assert modules["test.my_module"] == MyTestModule

    def test_module_manifest_created(self):
        from platform.core.modules import module
        from platform.core.modules.registrar import clear_registered_modules, get_registered_modules

        clear_registered_modules()

        @module(
            name="test.manifest",
            version="1.0.0",
            description="Testing manifest",
            dependencies=["core.kernel"],
            events_published=["event.one", "event.two"],
        )
        class ManifestModule:
            pass

        instance = ManifestModule()
        assert instance.name == "test.manifest"

    def test_module_state_transitions(self):
        from platform.core.modules.module import Module, ModuleManifest, ModuleState

        manifest = ModuleManifest(name="state.test", version="1.0.0")
        mod = Module(manifest)
        assert mod.state == ModuleState.DISCOVERED

        import asyncio
        asyncio.run(mod.initialize())
        assert mod.state == ModuleState.INITIALIZED

        asyncio.run(mod.start())
        assert mod.state == ModuleState.RUNNING

        asyncio.run(mod.stop())
        assert mod.state == ModuleState.STOPPED

    def test_module_register_service(self):
        from platform.core.modules.module import Module, ModuleManifest

        manifest = ModuleManifest(name="svc.test")
        mod = Module(manifest)
        mod.register_service("db", {"type": "postgres"})
        svc = mod.get_service("db")
        assert svc["type"] == "postgres"

    def test_module_clear_registrations(self):
        from platform.core.modules.registrar import clear_registered_modules, get_registered_modules

        @module(name="temp.module")
        class TempModule:
            pass

        assert "temp.module" in get_registered_modules()
        clear_registered_modules()
        assert "temp.module" not in get_registered_modules()
