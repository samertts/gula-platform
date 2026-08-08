import importlib
import logging
from typing import Any


class MonolithAdapter:
    def __init__(self):
        self._logger = logging.getLogger("gula.integration.monolith")
        self._modules: dict[str, Any] = {}

    def import_module(self, module_path: str) -> Any:
        if module_path not in self._modules:
            self._modules[module_path] = importlib.import_module(module_path)
        return self._modules[module_path]

    def get_model(self, model_name: str) -> Any:
        module = self.import_module("app.models")
        model = getattr(module, model_name, None)
        if model is None:
            raise ImportError(f"Model '{model_name}' not found in app.models")
        return model

    def get_service(self, module_path: str, class_name: str) -> Any:
        module = self.import_module(module_path)
        cls = getattr(module, class_name, None)
        if cls is None:
            raise ImportError(f"Class '{class_name}' not found in {module_path}")
        return cls

    def get_current_user_dependency(self) -> Any:
        module = self.import_module("app.security.auth")
        return getattr(module, "get_current_user", None)

    def get_db_session(self) -> Any:
        module = self.import_module("app.database")
        return getattr(module, "get_db", None)

    def clear_cache(self) -> None:
        self._modules.clear()
