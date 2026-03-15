import os
import sys
import ast
import subprocess
from collections import defaultdict

ROOT = os.path.expanduser("~/lab-platform")

errors = []
syntax_ok = 0
modules = defaultdict(list)

print("\n🔍 Scanning project...\n")

for root, dirs, files in os.walk(ROOT):

    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules']]

    for f in files:

        if f.endswith(".py"):

            path = os.path.join(root, f)
            modules[f].append(path)

            try:
                with open(path, "r", encoding="utf8") as file:
                    ast.parse(file.read())

                syntax_ok += 1

            except Exception as e:
                errors.append((path, str(e)))

print("✔ Syntax OK files:", syntax_ok)
print("❌ Syntax errors:", len(errors))

for e in errors[:20]:
    print(e)

print("\n🔁 Checking duplicate modules\n")

duplicates = {}

for name, paths in modules.items():
    if len(paths) > 1:
        duplicates[name] = paths

print("Duplicate files:", len(duplicates))

for k,v in list(duplicates.items())[:10]:
    print("\n",k)
    for p in v:
        print("  ",p)

print("\n📦 Checking Python libraries\n")

required = [
"fastapi",
"uvicorn",
"requests",
"pyserial"
]

for pkg in required:
    try:
        __import__(pkg)
        print("✔",pkg)
    except:
        print("⬇ Installing",pkg)
        subprocess.call([sys.executable,"-m","pip","install",pkg])

print("\n🧩 Creating missing __init__.py\n")

created = 0

for root, dirs, files in os.walk(ROOT):

    if "__init__.py" not in files:
        init_path = os.path.join(root,"__init__.py")
        open(init_path,"a").close()
        created += 1

print("created:",created)

print("\n🗺 Generating architecture map\n")

import json

tree = {}

for root, dirs, files in os.walk(ROOT):

    rel = os.path.relpath(root, ROOT)

    tree[rel] = files

with open(os.path.join(ROOT,"architecture_map.json"),"w") as f:
    json.dump(tree,f,indent=2)

print("✔ architecture_map.json created")

print("\n✅ Scan finished")
