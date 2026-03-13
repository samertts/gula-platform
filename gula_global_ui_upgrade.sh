#!/bin/bash

# ==========================================
# GULA Global UI Upgrade
# تحسين واجهة GULA بشكل احترافي
# بدون تغيير backend أو database
# ==========================================

set -e

HTML_FILE="index.html"
BACKUP="gula_ui_backup_$(date +%s)"

echo "Starting GULA UI upgrade..."

# ==========================================
# Backup
# ==========================================

mkdir -p "$BACKUP"

cp "$HTML_FILE" "$BACKUP/"

echo "Backup created in $BACKUP"

# ==========================================
# إنشاء CSS حديث
# ==========================================

cat > gula-global-ui.css <<'EOF'

body{
font-family:system-ui,-apple-system;
background:#f6f8fb;
margin:0;
color:#1f2937;
}

.gula-container{
max-width:1400px;
margin:auto;
padding:30px;
}

.gula-header{
display:flex;
justify-content:space-between;
align-items:center;
margin-bottom:30px;
}

.gula-title{
font-size:28px;
font-weight:700;
}

.gula-nav{
display:flex;
gap:10px;
flex-wrap:wrap;
}

.gula-nav a{
padding:8px 16px;
background:white;
border-radius:20px;
text-decoration:none;
color:#374151;
font-size:14px;
box-shadow:0 2px 8px rgba(0,0,0,0.05);
}

.gula-nav a:hover{
background:#eef2ff;
}

.gula-grid{
display:grid;
grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
gap:20px;
}

.gula-card{
background:white;
border-radius:14px;
padding:20px;
box-shadow:0 5px 15px rgba(0,0,0,0.04);
transition:0.2s;
}

.gula-card:hover{
transform:translateY(-4px);
}

.gula-stat{
font-size:28px;
font-weight:700;
}

.gula-label{
font-size:13px;
color:#6b7280;
margin-bottom:6px;
}

.gula-chart{
margin-top:40px;
background:white;
padding:20px;
border-radius:14px;
}

.gula-search{
margin:20px 0;
}

.gula-search input{
width:100%;
padding:10px;
border-radius:10px;
border:1px solid #e5e7eb;
}

.sam-box{
position:fixed;
bottom:20px;
right:20px;
background:white;
padding:12px;
border-radius:12px;
box-shadow:0 5px 20px rgba(0,0,0,0.15);
max-width:240px;
font-size:14px;
}

@media(max-width:700px){

.gula-header{
flex-direction:column;
gap:10px;
align-items:flex-start;
}

}

EOF

# ==========================================
# إنشاء JS
# ==========================================

cat > gula-global-ui.js <<'EOF'

window.addEventListener("load",function(){

const container=document.createElement("div")

container.className="gula-container"

container.innerHTML=`

<div class="gula-header">

<div class="gula-title">GULA Platform</div>

<div class="gula-nav">

<a href="#">Dashboard</a>
<a href="#">Worklist</a>
<a href="#">Patients</a>
<a href="#">Results</a>
<a href="#">Analytics</a>

</div>

</div>

<div class="gula-search">

<input placeholder="Search patient or sample...">

</div>

<div class="gula-grid">

<div class="gula-card">
<div class="gula-label">Patients</div>
<div class="gula-stat">1245</div>
</div>

<div class="gula-card">
<div class="gula-label">Samples</div>
<div class="gula-stat">350</div>
</div>

<div class="gula-card">
<div class="gula-label">Tests Today</div>
<div class="gula-stat">890</div>
</div>

<div class="gula-card">
<div class="gula-label">Critical</div>
<div class="gula-stat" style="color:red">12</div>
</div>

</div>

<div class="gula-chart">

<canvas id="gulaChart"></canvas>

</div>

<div class="sam-box">

<b>سامر</b><br>
أنا هنا لمساعدتك أثناء استخدام منصة GULA.

</div>

`

document.body.innerHTML=""
document.body.appendChild(container)

const ctx=document.getElementById("gulaChart")

new Chart(ctx,{
type:"line",
data:{
labels:["Mon","Tue","Wed","Thu","Fri","Sat"],
datasets:[{
label:"Tests",
data:[120,200,300,250,280,350],
borderWidth:2
}]
}
})

})

EOF

# ==========================================
# إدخال المكتبات
# ==========================================

if ! grep -q "gula-global-ui.css" "$HTML_FILE"; then

sed -i "s|</head>|<link rel=\"stylesheet\" href=\"gula-global-ui.css\">\n<script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>\n</head>|" "$HTML_FILE"

fi

if ! grep -q "gula-global-ui.js" "$HTML_FILE"; then

sed -i "s|</body>|<script src=\"gula-global-ui.js\"></script>\n</body>|" "$HTML_FILE"

fi

echo "UI upgrade installed successfully."
