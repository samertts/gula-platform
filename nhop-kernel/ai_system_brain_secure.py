import os
import json
import re
from pathlib import Path

PROJECT_ROOT = os.getcwd()

ALLOWED_EXT = [
".py",".js",".ts",".rs",".json",".yaml",".yml",".env",".html",".css"
]

MAX_SIZE = 100000

SUSPICIOUS_PATTERNS = [
r"password\s*=",
r"secret\s*=",
r"api[_-]?key",
r"eval\(",
r"exec\(",
r"system\(",
r"subprocess",
r"unsafe\s",
r"unwrap\("
]

def scan_files():

    files=[]

    for root,dirs,filenames in os.walk(PROJECT_ROOT):

        if ".git" in root or "node_modules" in root:
            continue

        for f in filenames:

            ext=Path(f).suffix

            if ext not in ALLOWED_EXT:
                continue

            path=os.path.join(root,f)

            try:

                size=os.path.getsize(path)

                if size>MAX_SIZE:
                    continue

                with open(path,"r",encoding="utf-8",errors="ignore") as file:
                    content=file.read()

                files.append({
                "path":path.replace(PROJECT_ROOT,""),
                "size":size,
                "content":content
                })

            except:
                pass

    return files

def detect_languages(files):

    langs={}

    for f in files:

        ext=Path(f["path"]).suffix

        langs[ext]=langs.get(ext,0)+1

    return langs

def security_scan(files):

    findings=[]

    for f in files:

        for pattern in SUSPICIOUS_PATTERNS:

            if re.search(pattern,f["content"],re.IGNORECASE):

                findings.append({
                "file":f["path"],
                "issue":pattern
                })

    return findings

def build_tree():

    tree=[]

    for root,dirs,files in os.walk(PROJECT_ROOT):

        level=root.replace(PROJECT_ROOT,"").count(os.sep)
        indent=" "*4*level

        tree.append(f"{indent}{os.path.basename(root)}/")

        for f in files:
            tree.append(f"{indent}    {f}")

    return "\n".join(tree)

def save_report(langs,issues,tree):

    os.makedirs("ai_security_report",exist_ok=True)

    with open("ai_security_report/project_tree.txt","w") as f:
        f.write(tree)

    with open("ai_security_report/languages.json","w") as f:
        json.dump(langs,f,indent=2)

    with open("ai_security_report/security_issues.json","w") as f:
        json.dump(issues,f,indent=2)

def main():

    print("AI SYSTEM SECURITY BRAIN")
    print("Scanning project...")

    files=scan_files()

    langs=detect_languages(files)

    issues=security_scan(files)

    tree=build_tree()

    save_report(langs,issues,tree)

    print("Files scanned:",len(files))
    print("Languages:",langs)
    print("Potential issues:",len(issues))

    print("Report saved in ai_security_report/")

if __name__=="__main__":
    main()
