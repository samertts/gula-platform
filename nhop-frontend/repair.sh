

#!/usr/bin/env bash

set -euo pipefail

echo "================================="
echo "        GOVLAB REPAIR ENGINE"
echo "================================="
echo ""

ERROR_LOG=".govlab_errors.log"
SNAPSHOT_CREATED=false

########################################
# helper: ask approval
########################################
ask () {
  read -r -p "$1 (y/n): " ans
  [[ "$ans" == "y" || "$ans" == "Y" ]]
}

########################################
# helper: safe snapshot
########################################
create_snapshot () {

  if git diff --quiet && git diff --cached --quiet; then
    echo "No changes to snapshot."
    return
  fi

  echo "Creating safety snapshot..."

  git add -A
  git commit -m "govlab: pre-repair snapshot" --no-verify >/dev/null

  SNAPSHOT_CREATED=true
}

########################################
# STEP 1 — scan project (truth mode)
########################################

echo "Scanning TypeScript..."

set +e
npx tsc --noEmit > "$ERROR_LOG" 2>&1
TS_STATUS=$?
set -e

if [ $TS_STATUS -eq 0 ]; then
  echo "✅ Project healthy. No errors."
  rm -f "$ERROR_LOG"
  exit 0
fi

echo ""
echo "Detected issues:"
echo "---------------------------------"
cat "$ERROR_LOG"
echo "---------------------------------"
echo ""

create_snapshot

########################################
# FIX TS1435 — missing export keyword
########################################

if grep -q "TS1435" "$ERROR_LOG"; then
  echo "⚠ TS1435 detected → probable missing 'export'"
  echo "Impact:"
  echo "- Fixes mistyped keyword"
  echo "- Low risk"

  if ask "Apply auto-fix?"; then
    MATCHES=$(grep -rl "^xport " src || true)

    if [ -n "$MATCHES" ]; then
      echo "$MATCHES" | xargs sed -i 's/^xport/export/'
      echo "✔ export keyword repaired"
    else
      echo "No matching typo found."
    fi
  fi
fi

########################################
# FIX TS1434 — terminal artifacts
########################################

if grep -q "TS1434" "$ERROR_LOG"; then
  echo ""
  echo "⚠ TS1434 detected → terminal command inside code"
  echo "Impact:"
  echo "- Removes accidental CLI lines"

  if ask "Clean suspicious lines?"; then
    grep -rl "^nano " src | xargs -r sed -i '/^nano /d'
    echo "✔ Terminal artifacts removed"
  fi
fi

########################################
# FIX TS1005 — missing brace
########################################

if grep -q "TS1005" "$ERROR_LOG"; then
  echo ""
  echo "⚠ TS1005 detected → possible missing brace"
  echo "Risk:"
  echo "- Brace location may not be exact"

  if ask "Attempt safe brace repair?"; then

    FILES=$(grep -o 'src/[^:]*' "$ERROR_LOG" | sort -u)

    for f in $FILES; do
      if [ -f "$f" ]; then
        echo "Checking braces in $f"

        OPEN=$(grep -o "{" "$f" | wc -l)
        CLOSE=$(grep -o "}" "$f" | wc -l)

        if [ "$OPEN" -gt "$CLOSE" ]; then
          echo "Adding missing brace to $f"
          echo "}" >> "$f"
        fi
      fi
    done

    echo "✔ Brace balancing attempt complete"
  fi
fi

########################################
# STEP 3 — validation
########################################

echo ""
echo "Revalidating project..."

set +e
npx tsc --noEmit
FINAL_STATUS=$?
set -e

########################################
# STEP 4 — impact report
########################################

echo ""
echo "=========== CHANGE SUMMARY ==========="

if $SNAPSHOT_CREATED; then
  git --no-pager diff --stat HEAD~1
else
  echo "No snapshot created."
fi

echo ""

if [ $FINAL_STATUS -eq 0 ]; then
  echo "✅ Project repaired successfully."
else
  echo "⚠ Some issues remain. Manual review required."
fi

echo ""
echo "Rollback command:"
echo "git reset --hard HEAD~1"
echo ""
echo "=========== DONE ==========="

