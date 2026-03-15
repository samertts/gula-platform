#!/bin/bash

echo "Starting advanced repository repair..."

# إنشاء gitignore احترافي
cat > .gitignore << 'EOF'
venv/
__pycache__/
*.pyc
*.pyo
*.log
.env
node_modules/
dist/
build/
.DS_Store
EOF

echo "gitignore created"

# إزالة الأشياء غير الضرورية من Git فقط
git rm -r --cached venv 2>/dev/null
git rm -r --cached node_modules 2>/dev/null
git rm -r --cached __pycache__ 2>/dev/null

# تنظيف الكاشات
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.log" -delete

echo "Cache cleaned"

# إنشاء هيكل مشروع احترافي
mkdir -p backend/api
mkdir -p backend/services
mkdir -p backend/models

mkdir -p frontend/components

mkdir -p docker
mkdir -p scripts
mkdir -p docs

echo "Project architecture created"

# نقل السكربتات
for f in *.sh; do
    if [ "$f" != "repair_gula_repo.sh" ]; then
        mv "$f" scripts/ 2>/dev/null
    fi
done

echo "Scripts organized"

# تنظيف Git وإعادة الرفع
git add .

git commit -m "Advanced repository cleanup and architecture improvement"

git push origin main

echo "Repository repaired successfully"
