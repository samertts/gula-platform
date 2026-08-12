import importlib

from ai_registry import AI_MODULES


def run_ai(module_name):

    module_path = AI_MODULES.get(module_name)

    if not module_path:
        return "AI module not found"

    module = importlib.import_module(module_path)

    return module
