#!/bin/bash
# =============================================
# GULA Safe UI Enhancer
# سكريبت آمن لتحسين واجهة منصة GULA
# لا يغير backend أو قاعدة البيانات
# =============================================

set -e

HTML_FILE="index.html"
JS_FILE="gula-enhancer.js"
BACKUP_DIR="./gula_backup_$(date +%Y%m%d_%H%M%S)"

echo "---------------------------------------"
echo " GULA UI Safe Enhancer"
echo "---------------------------------------"

# =============================================
# إنشاء النسخ الاحتياطية
# =============================================

mkdir -p "$BACKUP_DIR"

echo "Backup directory created:"
echo "$BACKUP_DIR"

# =============================================
# التحقق من وجود HTML
# =============================================

if [ ! -f "$HTML_FILE" ]; then
    echo "index.html not found."
    echo "Enter HTML file path:"
    read HTML_FILE

    if [ ! -f "$HTML_FILE" ]; then
        echo "File not found. Exiting."
        exit 1
    fi
fi

cp "$HTML_FILE" "$BACKUP_DIR/"

echo "Backup created for $HTML_FILE"

# =============================================
# إنشاء ملف التحسينات
# =============================================

cat > "$JS_FILE" << 'EOF'

/*
GULA Enhancer
واجهة أخف وأجمل دون تعديل الكود الأصلي
*/

(function(){

window.addEventListener("load",function(){

const style=document.createElement("style")

style.innerHTML=`

.gula-stats-grid{
display:grid;
grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
gap:20px;
margin:20px 0;
}

.gula-card{
background:white;
border-radius:16px;
padding:20px;
box-shadow:0 4px 12px rgba(0,0,0,0.05);
display:flex;
align-items:center;
justify-content:space-between;
transition:0.2s;
}

.gula-card:hover{
transform:translateY(-4px);
}

.gula-label{
font-size:14px;
color:#777;
}

.gula-value{
font-size:28px;
font-weight:bold;
}

`

document.head.appendChild(style)

})

})()

EOF

echo "Enhancer JS created."

# =============================================
# منع تكرار السكريبت
# =============================================

if grep -q "$JS_FILE" "$HTML_FILE"; then
    echo "Enhancer already installed."
else

if grep -q "</body>" "$HTML_FILE"; then

cp "$HTML_FILE" "$BACKUP_DIR/$(basename "$HTML_FILE").before_edit"

sed -i "s|</body>|<script src=\"$JS_FILE\"></script>\n</body>|" "$HTML_FILE"

echo "Script inserted into HTML."

else

echo "Could not find </body> tag."
echo "Insert this manually before </body>:"
echo "<script src=\"$JS_FILE\"></script>"

fi

fi

echo "---------------------------------------"
echo "Installation complete"
echo "Backup stored in:"
echo "$BACKUP_DIR"
echo "---------------------------------------"
