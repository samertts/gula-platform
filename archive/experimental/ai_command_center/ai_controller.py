from ai_runner import run_ai


def execute_ai(module):

    ai_module = run_ai(module)

    if isinstance(ai_module, str):
        return ai_module

    return "AI module loaded"
