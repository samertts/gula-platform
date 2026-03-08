#!/bin/bash

echo "======================================"
echo "   LAB PLATFORM FULL SYSTEM CHECK"
echo "======================================"

cd ~/lab-platform || exit

echo ""
echo "1️⃣ Installing analysis tools..."
pip install -q black autopep8 isort ruff bandit

echo ""
echo "2️⃣ Fixing code style..."
autopep8 --in-place --recursive .
isort .
black .

echo ""
echo "3️⃣ Static code analysis..."
ruff check .

echo ""
echo "4️⃣ Security scan..."
bandit -r .

echo ""
echo "5️⃣ Python syntax check..."
python3 -m compileall .

echo ""
echo "6️⃣ Counting Python files..."
find . -name "*.py" | wc -l

echo ""
echo "7️⃣ Detecting TODO / FIXME..."
grep -R "TODO\|FIXME" .

echo ""
echo "======================================"
echo " SYSTEM CHECK COMPLETE"
echo "======================================"
