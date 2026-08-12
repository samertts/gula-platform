import os

BASE = os.path.expanduser("~/lab-platform")

for root, dirs, files in os.walk(BASE):

    for f in files:

        if not f.endswith(".py"):
            continue

        path = os.path.join(root, f)

        with open(path, "r", errors="ignore") as file:
            data = file.read()

        if "from services.identity_engine.citizens_db import" in data:
            data = data.replace(
                "from services.identity_engine.citizens_db import",
                "from services.identity_engine.citizens_db import"
            )

        with open(path, "w") as file:
            file.write(data)

print("✔ Auto import fix done")
