#!/usr/bin/env bash

set -e

echo "===== GULA SAFE EXTENSION ====="

USER_NAME="samertts"
HOME_DIR="/home/$USER_NAME"
PROJECT_DIR="$HOME_DIR/gula-platform"

echo "1️⃣ Checking user"

if id "$USER_NAME" &>/dev/null; then
    echo "User exists"
else
    echo "User missing"
    exit 1
fi

echo "2️⃣ Checking docker group"

if groups $USER_NAME | grep docker >/dev/null; then
    echo "Docker permission OK"
else
    usermod -aG docker $USER_NAME
fi

echo "3️⃣ Checking project directory"

if [ -d "$PROJECT_DIR" ]; then
    echo "Project found"
else
    echo "Project missing"
    exit 1
fi

echo "4️⃣ Fixing permissions"

chown -R $USER_NAME:$USER_NAME $PROJECT_DIR

echo "5️⃣ Checking docker containers"

docker ps >/dev/null

echo "Docker OK"

echo "6️⃣ Checking deploy script"

if [ -f "$HOME_DIR/deploy.sh" ]; then
    echo "Deploy script exists"
else
    echo "Deploy script missing"
fi

echo "7️⃣ Checking webhook"

if pgrep -f webhook.py >/dev/null; then
    echo "Webhook running"
else
    echo "Webhook not running"
fi

echo "8️⃣ Checking firewall"

if ufw status | grep active >/dev/null; then
    echo "Firewall active"
else
    echo "Firewall inactive"
fi

echo "9️⃣ Checking fail2ban"

if systemctl is-active fail2ban >/dev/null; then
    echo "Fail2ban active"
else
    echo "Fail2ban inactive"
fi

echo "10️⃣ Checking git"

sudo -u $USER_NAME bash <<EOF
cd $PROJECT_DIR
git fetch
EOF

echo "11️⃣ Checking docker containers"

sudo -u $USER_NAME bash <<EOF
cd $PROJECT_DIR
docker compose ps
EOF

echo ""
echo "===== SYSTEM STATUS COMPLETE ====="
echo ""
echo "Platform URL:"
echo "https://gula-platform.org"
echo ""
