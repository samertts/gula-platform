

#!/usr/bin/env bash

##################################################
# NHOP SYSTEM DOCTOR v3 (FINAL)
# Safe Diagnostic Engine
##################################################

set +e

PROJECT_ROOT=$(pwd)

echo ""
echo "=============================================="
echo "        NHOP SAFE DIAGNOSTIC (DOCTOR v3)"
echo "=============================================="
echo ""

##################################################
# [1] NODE ENVIRONMENT
##################################################

echo "[1] Node environment"

node -v >/dev/null 2>&1 \
  && echo "OK   Node detected: $(node -v)" \
  || echo "FAIL Node missing"

npm -v >/dev/null 2>&1 \
  && echo "OK   npm detected: $(npm -v)" \
  || echo "WARN npm missing"

echo ""

##################################################
# [2] DIRECTORY STRUCTURE
##################################################

echo "[2] Directory structure"

DIRS=(
core
core/runtime
core/security
core/healing
core/policy
core/context
core/sandbox
extensions
modules
)

for d in "${DIRS[@]}"; do
    if [ -d "$PROJECT_ROOT/$d" ]; then
        echo "OK   $d"
    else
        echo "MISS $d"
    fi
done

echo ""

##################################################
# [3] CRITICAL FILES
##################################################

echo "[3] Critical files"

FILES=(
server.js
boot.js
core/runtime/runtime.kernel.js
core/sandbox/sandbox.factory.js
core/sandbox/capabilities.js
)

for f in "${FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$f" ]; then
        echo "OK   $f"
    else
        echo "MISS $f"
    fi
done

echo ""

##################################################
# [4] PERMISSION CHECK
##################################################

echo "[4] Permission check"

OWNER=$(stat -c '%U' . 2>/dev/null)
USER_NOW=$(whoami)

echo "Owner : $OWNER"
echo "User  : $USER_NOW"

if [ "$OWNER" != "$USER_NOW" ]; then
    echo "WARN ownership mismatch (possible npm EACCES)"
else
    echo "OK   ownership valid"
fi

echo ""

##################################################
# [5] NODE MODULES
##################################################

echo "[5] node_modules integrity"

if [ -d node_modules ]; then
    echo "OK   node_modules exists"
else
    echo "WARN node_modules missing (run npm install)"
fi

echo ""

##################################################
# [6] EXTENSION DISCOVERY
##################################################

echo "[6] Extension scan"

if [ -d extensions ]; then

    for ext in extensions/*; do
        if [ -d "$ext" ]; then

            NAME=$(basename "$ext")

            if [ -f "$ext/index.js" ]; then
                echo "OK   extension: $NAME"
            else
                echo "MISS extension entry: $NAME/index.js"
            fi
        fi
    done

else
    echo "WARN extensions folder missing"
fi

echo ""

##################################################
# [7] SANDBOX VALIDATION
##################################################

echo "[7] Sandbox validation"

node <<'EOF'
try {
    const createSandbox =
        require("./core/sandbox/sandbox.factory");

    const sb = createSandbox("doctor-test");

    if (!sb || !sb.run) {
        console.log("FAIL sandbox invalid");
        process.exit(1);
    }

    sb.run("console.log('sandbox ok')");
    console.log("OK   sandbox execution working");

} catch (e) {
    console.log("FAIL sandbox:", e.message);
}
EOF

echo ""

##################################################
# [8] REQUIRE SCAN (SAFE)
##################################################

echo "[8] Lightweight require scan"

find core extensions -type f -name "*.js" 2>/dev/null | while read file
do
    grep -oE "require\(['\"][^'\"]+['\"]\)" "$file" 2>/dev/null \
    | sed "s/require(//" | sed "s/[\"']//g" | sed "s/)//" \
    | while read mod
    do
        if [[ "$mod" == .* ]]; then
            TARGET="$(dirname "$file")/$mod.js"
            if [ ! -f "$TARGET" ]; then
                echo "BROKEN require -> $TARGET"
            fi
        fi
    done
done

echo ""

##################################################
# [9] PACKAGE CHECK
##################################################

echo "[9] Package integrity"

if [ -f package.json ]; then
    echo "OK   package.json present"
else
    echo "MISS package.json"
fi

echo ""

##################################################
# COMPLETE
##################################################

echo "=============================================="
echo "        SAFE DIAGNOSIS COMPLETE"
echo "=============================================="
echo ""

