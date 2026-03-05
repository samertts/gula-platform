#!/bin/bash

echo "====================================="
echo "   SYSTEM FULL INSPECTOR & EXPORT"
echo "====================================="
echo ""

PROJECT_DIR=$(pwd)
EXPORT_DIR="$PROJECT_DIR/system_export"
DATE=$(date +%Y%m%d_%H%M)

mkdir -p $EXPORT_DIR

echo "1️⃣  Scanning project structure..."

tree -a $PROJECT_DIR > $EXPORT_DIR/project_tree.txt 2>/dev/null || find . > $EXPORT_DIR/project_tree.txt

echo "Project structure saved."

echo ""
echo "2️⃣  Detecting programming languages..."

echo "Python files:" >> $EXPORT_DIR/languages.txt
find . -name "*.py" >> $EXPORT_DIR/languages.txt

echo "" >> $EXPORT_DIR/languages.txt
echo "JavaScript files:" >> $EXPORT_DIR/languages.txt
find . -name "*.js" >> $EXPORT_DIR/languages.txt

echo "" >> $EXPORT_DIR/languages.txt
echo "Config files:" >> $EXPORT_DIR/languages.txt
find . -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.env" >> $EXPORT_DIR/languages.txt

echo "Languages scan complete."

echo ""
echo "3️⃣  Exporting environment variables..."

printenv > $EXPORT_DIR/environment_variables.txt

echo "Environment variables saved."

echo ""
echo "4️⃣  Checking database files..."

find . -name "*.db" -o -name "*.sqlite" -o -name "*.sql" > $EXPORT_DIR/databases.txt

echo "Database scan complete."

echo ""
echo "5️⃣  Checking installed packages..."

pip freeze > $EXPORT_DIR/python_packages.txt 2>/dev/null

npm list --depth=0 > $EXPORT_DIR/node_packages.txt 2>/dev/null

echo "Packages list saved."

echo ""
echo "6️⃣  Creating full system archive..."

tar --exclude='./system_export' \
    -czf system_backup_$DATE.tar.gz .

echo ""
echo "====================================="
echo "EXPORT COMPLETE"
echo "====================================="
echo ""

echo "Backup file:"
echo "system_backup_$DATE.tar.gz"

echo ""
echo "Report folder:"
echo "$EXPORT_DIR"

echo ""
echo "Files generated:"
echo "- project_tree.txt"
echo "- languages.txt"
echo "- environment_variables.txt"
echo "- databases.txt"
echo "- python_packages.txt"
echo "- node_packages.txt"

echo ""
echo "Done."
