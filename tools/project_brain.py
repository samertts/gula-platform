import os
import re
from collections import defaultdict

BASE = os.path.expanduser("~/lab-platform")

imports = defaultdict(set)
modules = {}

# -----------------------
# جمع كل الملفات
# -----------------------

for root, dirs, files in os.walk(BASE):
    for f in files:
        if f.endswith(".py"):
            name = f[:-3]
            path = os.path.join(root, f)
            modules[name] = path

# -----------------------
# تحليل imports
# -----------------------

pattern = re.compile(r'^\s*(from|import)\s+([a-zA-Z0-9_\.]+)')

for name, path in modules.items():

    with open(path, "r", errors="ignore") as f:
        lines = f.readlines()

    for line in lines:

        m = pattern.match(line)

        if not m:
            continue

        module = m.group(2).split(".")[0]

        if module in modules:
            imports[name].add(module)

# -----------------------
# طباعة الخريطة
# -----------------------

print("\n🧠 Project Brain Dependency Map\n")

for mod in imports:
    if imports[mod]:
        print(mod, "→", ", ".join(imports[mod]))

print("\nTotal modules:", len(modules))
print("Modules with dependencies:", len(imports))

# -----------------------
# Loop detection
# -----------------------

visited=set()

def detect_loop(node,stack):

    if node in stack:
        print("⚠ Dependency loop:", " → ".join(stack+[node]))
        return

    if node not in imports:
        return

    stack.append(node)

    for nxt in imports[node]:
        detect_loop(nxt,stack)

    stack.pop()

print("\n🔍 Searching dependency loops...\n")

for m in imports:
    detect_loop(m,[])
