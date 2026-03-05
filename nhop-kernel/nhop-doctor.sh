#!/bin/bash

echo "======================================="
echo " NHOP SYSTEM DOCTOR"
echo " Environment Diagnostic & Auto Repair"
echo "======================================="

REPORT_DIR="system_backup"
REPORT_FILE="$REPORT_DIR/diagnostic_report.txt"

mkdir -p "$REPORT_DIR"

echo "NHOP Diagnostic Report" > "$REPORT_FILE"
echo "Date: $(date)" >> "$REPORT_FILE"
echo "--------------------------------" >> "$REPORT_FILE"

########################################
echo ""
echo "1 Checking internet connectivity..."

if ping -c 2 github.com > /dev/null 2>&1
then
    echo "Internet OK"
    echo "Internet: OK" >> "$REPORT_FILE"
else
    echo "Internet problem detected"
    echo "Internet: FAILED" >> "$REPORT_FILE"
fi

########################################
echo ""
echo "2 Fixing Git slow network settings..."

git config --global
