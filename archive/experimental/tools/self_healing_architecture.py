import os
import re
import json
from collections import defaultdict

BASE = os.path.expanduser("~/lab-platform")

STANDARD_LIB = {
"os","sys","json","time","random","datetime","re","math",
"subprocess","threading","logging","pathlib","itertools"
}

IMPORT_RE = re.compile(r'^\s*(?:from|import)\s+([a-zA-Z0-9_\.]+)')

modules={}
imports=defaultdict(set)
missing=[]
duplicates=defaultdict(list)

# --------------------------------
# Collect modules
# --------------------------------

for root,dirs,files in os.walk(BASE):

    for f in files:

        if f.endswith(".py"):

            name=f[:-3]

            path=os.path.join(root,f)

            modules[name]=path

            duplicates[name].append(path)

# --------------------------------
# Detect imports
# --------------------------------

for name,path in modules.items():

    try:

        with open(path,"r",errors="ignore") as f:
            lines=f.readlines()

    except:
        continue

    for line in lines:

        m=IMPORT_RE.match(line)

        if not m:
            continue

        mod=m.group(1).split(".")[0]

        if mod in STANDARD_LIB:
            continue

        if mod not in modules:
            missing.append((path,mod))
        else:
            imports[name].add(mod)

# --------------------------------
# Report
# --------------------------------

print("\n🧠 Self-Healing Architecture Scan\n")

print("Total modules:",len(modules))
print("Missing imports:",len(missing))

for e in missing[:20]:
    print("❌",e[0],"→",e[1])

print("\nDuplicate module names:")

for k,v in duplicates.items():
    if len(v)>1:
        print("⚠",k,"→",len(v),"files")

# --------------------------------
# Auto Fix
# --------------------------------

def ensure_packages():

    for root,dirs,files in os.walk(BASE):

        init=os.path.join(root,"__init__.py")

        if not os.path.exists(init):

            try:
                open(init,"w").close()
            except:
                pass

def save_dependency_map():

    out={}

    for k,v in imports.items():
        out[k]=list(v)

    path=os
