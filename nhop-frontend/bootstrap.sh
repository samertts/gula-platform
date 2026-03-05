#!/bin/bash

echo "=== GOVLAB CONTROLLED CHECK ==="

STATE_FILE=".govlab_state"

# حساب بصمة المشروع
NEW_HASH=$(find src -type f -exec sha1sum {} \; | sha1sum | awk '{print $1}')

OLD_HASH=""

if [ -f "$STATE_FILE" ]; then
  OLD_HASH=$(cat $STATE_FILE)
fi

# لا يوجد تغيير
if [ "$NEW_HASH" == "$OLD_HASH" ]; then
  echo "✅ No changes detected. Nothing to build."
  exit 0
fi

echo "⚠️ Changes detected in project."

read -p "Do you want to rebuild now? (y/n): " ANSWER

if [ "$ANSWER" != "y" ]; then
  echo "Build cancelled."
  exit 0
fi

echo "Starting controlled build..."

# تثبيت dependencies فقط إذا غير موجودة
if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm install
fi

# فحص TypeScript
npx tsc --noEmit

# build عند توفره
npm run build --if-present

# حفظ الحالة الجديدة
echo $NEW_HASH > $STATE_FILE

echo "✅ Build completed successfully."
