#!/bin/bash

echo "======================================="
echo "     LAB PLATFORM FULL SYSTEM AUDIT"
echo "======================================="

cd ~/lab-platform || exit

echo ""
echo "1) Installing analysis tools..."
pip install -q black autopep8 isort ruff bandit psutil

echo ""
echo "2) Fixing Python formatting..."
autopep8 --in-place --recursive .
isort .
black .

echo ""
echo "3) Static code analysis..."
ruff check .

echo ""
echo "4) Security scan..."
bandit -r .

echo ""
echo "5) Python syntax validation..."
python3 -m compileall .

echo ""
echo "6) Counting project files..."
echo "Python files:"
find . -name "*.py" | wc -l

echo "JS files:"
find . -name "*.js" | wc -l

echo "HTML files:"
find . -name "*.html" | wc -l

echo ""
echo "7) Checking disk usage..."
df -h

echo ""
echo "8) Checking memory usage..."
free -h

echo ""
echo "9) Checking CPU load..."
uptime

echo ""
echo "10) Checking running services..."
ps aux | grep python | grep -v grep

echo ""
echo "11) Checking open ports..."
ss -tulnp

echo ""
echo "12) Checking Docker containers (if any)..."
docker ps 2>/dev/null

echo ""
echo "13) Checking TODO / FIXME in code..."
grep -R "TODO\|FIXME" .

echo ""
echo "======================================="
echo "        SYSTEM AUDIT COMPLETE"
echo "======================================="
