from ai_controller import execute_ai
from ai_registry import AI_MODULES


def dashboard():

    print("\nUnified AI Command Center")
    print("--------------------------")

    for name in AI_MODULES:

        result = execute_ai(name)

        print(name, "->", result)


if __name__ == "__main__":

    dashboard()
