from platform.core.modules import module


@module(
    name="gula.user",
    version="1.0.0",
    description="User and authentication management",
    dependencies=[],
    events_published=["user.created", "user.login", "user.logout"],
    events_subscribed=["user.login"],
    commands_handled=["create_user", "update_user", "deactivate_user"],
    queries_handled=["get_user", "list_users_by_lab"],
)
class UserModule:
    def __init__(self, auth_service=None, audit_service=None):
        self._auth_service = auth_service
        self._audit_service = audit_service
        self.register_service("auth_service", auth_service)

    async def on_initialize(self) -> None:
        pass

    async def on_start(self) -> None:
        pass

    async def on_stop(self) -> None:
        pass
