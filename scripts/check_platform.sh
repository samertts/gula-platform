#!/bin/bash

echo "=============================="
echo "GULA PLATFORM DIAGNOSTIC"
echo "=============================="

echo ""
echo "Project path:"
pwd

echo ""
echo "Git status:"
git status

echo ""
echo "Last commit:"
git log -1 --oneline

echo ""
echo "Remote repository:"
git remote -v

echo ""
echo "Checking if branch is synced with origin..."
git fetch
git status

echo ""
echo "Checking API server on port 8000..."
if lsof -i :8000 > /dev/null
then
    echo "API server is running"
else
    echo "API server NOT running"
fi

echo ""
echo "Checking Python environment..."
python3 --version

echo ""
echo "Checking installed packages..."
pip list | grep -E "fastapi|pydantic|uvicorn"

echo ""
echo "Diagnostic complete"
