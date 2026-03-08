import os
import re

BASE = os.path.expanduser("~/lab-platform")

modules = {}
errors = []

# -----------------------------
# جمع كل ملفات Python
# -----------------------------

for root, dirs, files in os.walk(BASE):
    for f in files:
        if f.endswith(".py"):
            name = f[:-3]
            path = os.path.join(root, f)
            modules[name] = path

# -----------------------------
# فحص imports
# -----------------------------

pattern = re.compile(r'^\s*(from|import)\s+([a-zA-Z0-9_\.]+)')

for root, dirs, files in os.walk(BASE):
    for f in files:

        if not f.endswith(".py"):
            continue

        path = os.path.join(root, f)

        with open(path, "r", errors="ignore") as file:
            lines = file.readlines()

        for line in lines:

            match = pattern.match(line)

            if not match:
                continue

            module = match.group(2).split(".")[0]

            if module in ["os","sys","json","time","random","datetime","flask"]:
                continue

            if module not in modules:
                errors.append((path, module))

# -----------------------------
# تقرير
# -----------------------------

print("\n🔍 AI Project Doctor Report\n")

print("Total modules found:", len(modules))
print("Import problems:", len(errors))
print()

for e in errors[:30]:
    print("❌", e[0], "→ missing:", e[1])

print("\n✔ Scan complete")
