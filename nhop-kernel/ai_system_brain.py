import os
import json
from pathlib import Path

PROJECT_ROOT = os.getcwd()

ALLOWED_EXT = [
".py",
".js",
".ts",
".json",
".yaml",
".yml",
".env",
".html",
".css",
".md"
]

MAX_FILE_SIZE = 50000

def scan_files():
    files = []

    for root, dirs, filenames in os.walk(PROJECT_ROOT):

        if ".git" in root:
            continue

        for f in filenames:

            path = os.path.join(root, f)
            ext = Path(f).suffix

            if ext not in ALLOWED_EXT:
                continue

            try:

                size = os.path.getsize(path)

                if size > MAX_FILE_SIZE:
                    continue

                with open(path, "r", encoding="utf-8", errors="ignore") as file:
                    content = file.read()

                files.append({
                    "path": path.replace(PROJECT_ROOT, ""),
                    "size": size,
                    "content": content[:2000]
                })

            except:
                pass

    return files

def detect_languages(files):

    langs = {}

    for f in files:

        ext = Path(f["path"]).suffix

        if ext not in langs:
            langs[ext] = 0

        langs[ext] += 1

    return langs

def build_tree():

    tree = []

    for root, dirs, files in os.walk(PROJECT_ROOT):

        level = root.replace(PROJECT_ROOT, "").count(os.sep)
        indent = " " * 4 * level

        tree.append(f"{indent}{os.path.basename(root)}/")

        subindent = " " * 4 * (level + 1)

        for f in files:
            tree.append(f"{subindent}{f}")

    return "\n".join(tree)

def generate_summary(files, langs):

    return {
        "project": os.path.basename(PROJECT_ROOT),
        "files_scanned": len(files),
        "languages": langs,
        "sample_files": files[:10]
    }

def save_report(summary, tree):

    os.makedirs("ai_report", exist_ok=True)

    with open("ai_report/project_tree.txt", "w") as f:
        f.write(tree)

    with open("ai_report/system_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("Report saved in ai_report/")

def main():

    print("AI SYSTEM BRAIN")
    print("Scanning project...")

    files = scan_files()
    langs = detect_languages(files)
    tree = build_tree()

    summary = generate_summary(files, langs)

    save_report(summary, tree)

    print("Files scanned:", len(files))
    print("Languages:", langs)

    print("Done")

if __name__ == "__main__":
    main()
