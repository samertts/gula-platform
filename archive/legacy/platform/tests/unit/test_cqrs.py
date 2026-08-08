import asyncio

import pytest


class TestCommandBus:
    def test_register_and_dispatch(self, command_bus):
        results = []

        async def handler(cmd):
            results.append(cmd.command_id)

        command_bus.register("test_cmd", handler)
        from platform.core.cqrs import Command
        asyncio.run(command_bus.dispatch("test_cmd", Command()))
        assert len(results) == 1

    def test_no_handlers_logs_warning(self, command_bus):
        from platform.core.cqrs import Command
        result = asyncio.run(command_bus.dispatch("no_handler", Command()))
        assert result == []

    def test_multiple_handlers(self, command_bus):
        results = []

        async def h1(cmd):
            results.append("h1")

        async def h2(cmd):
            results.append("h2")

        command_bus.register("multi", h1)
        command_bus.register("multi", h2)
        from platform.core.cqrs import Command
        asyncio.run(command_bus.dispatch("multi", Command()))
        assert results == ["h1", "h2"]

    def test_unregister_handler(self, command_bus):
        async def handler(cmd):
            pass

        command_bus.register("cmd", handler)
        command_bus.unregister("cmd", handler)
        assert command_bus.handler_count() == 0

    def test_registered_commands(self, command_bus):
        assert command_bus.registered_commands() == []

        async def h(cmd):
            pass

        command_bus.register("a", h)
        command_bus.register("b", h)
        assert sorted(command_bus.registered_commands()) == sorted(["a", "b"])

    def test_handler_count(self, command_bus):
        async def h1(cmd):
            pass

        async def h2(cmd):
            pass

        command_bus.register("x", h1)
        command_bus.register("x", h2)
        assert command_bus.handler_count() == 2


class TestQueryBus:
    def test_register_and_ask(self, query_bus):
        async def handler(query):
            return {"result": 42}

        query_bus.register("test_query", handler)
        from platform.core.cqrs import Query
        result = asyncio.run(query_bus.ask("test_query", Query()))
        assert result["result"] == 42

    def test_unknown_query_raises(self, query_bus):
        from platform.core.cqrs import Query
        with pytest.raises(KeyError):
            asyncio.run(query_bus.ask("unknown"))

    def test_unregister(self, query_bus):
        async def handler(q):
            return None

        query_bus.register("q", handler)
        query_bus.unregister("q")
        assert query_bus.handler_count() == 0

    def test_registered_queries(self, query_bus):
        async def h(q):
            return None

        query_bus.register("q1", h)
        query_bus.register("q2", h)
        assert sorted(query_bus.registered_queries()) == sorted(["q1", "q2"])
