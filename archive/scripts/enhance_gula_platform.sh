#!/bin/bash

echo "Enhancing GULA platform safely..."

# إنشاء gitignore بدون التأثير على الملفات الحالية
if [ ! -f .gitignore ]; then
cat > .gitignore << 'EOF'
venv/
__pycache__/
*.pyc
*.log
.env
node_modules/
dist/
build/
.DS_Store
EOF
fi

echo "gitignore ensured"

# إزالة venv من Git فقط بدون حذفها
git rm -r --cached venv 2>/dev/null

# تنظيف الكاشات
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

echo "cache cleaned"

# إنشاء مجلد تحسينات الواجهة بدون المساس بالكود الحالي
mkdir -p frontend/enhancements
mkdir -p frontend/enhancements/css
mkdir -p frontend/enhancements/js

# CSS خفيف
cat > frontend/enhancements/css/ui-enhancements.css << 'EOF'
body{
font-family: system-ui, -apple-system, sans-serif;
background:#f6f8fb;
}

.card{
border-radius:10px;
box-shadow:0 2px 10px rgba(0,0,0,0.05);
}

button{
transition:all .2s ease;
}

button:hover{
transform:translateY(-1px);
}
EOF

# JS خفيف
cat > frontend/enhancements/js/ui-enhancements.js << 'EOF'
document.addEventListener("DOMContentLoaded",function(){

console.log("GULA UI enhancements loaded");

const buttons=document.querySelectorAll("button");

buttons.forEach(btn=>{
btn.addEventListener("click",()=>{
btn.style.opacity="0.8";
setTimeout(()=>btn.style.opacity="1",200);
});
});

});
EOF

echo "UI enhancement layer created"

# إنشاء ملف CDN للمكتبات الخفيفة
cat > frontend/enhancements/cdn.html << 'EOF'
<!-- Lightweight CDN libraries -->

<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">

<script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
EOF

echo "CDN layer added"

# نقل السكربتات إلى مجلد scripts بدون كسرها
mkdir -p scripts

for f in *.sh; do
if [ "$f" != "enhance_gula_platform.sh" ]; then
mv "$f" scripts/ 2>/dev/null
fi
done

echo "scripts organized"

# commit التعديلات
git add .

git commit -m "safe enhancement layer added (UI + cleanup + structure)"

git push origin main

echo "Enhancement completed successfully"
