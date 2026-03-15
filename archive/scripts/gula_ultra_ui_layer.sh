#!/bin/bash

# ==========================================
# GULA Ultra UI Layer
# واجهة احترافية دون المساس بالـ backend
# ==========================================

set -e

BASE=~/gula-platform/frontend
HTML="$BASE/index.html"

BACKUP="$BASE/ui_backup_$(date +%s)"

echo "Installing GULA Ultra UI..."

mkdir -p "$BACKUP"

cp "$HTML" "$BACKUP/"

echo "Backup created."

# ==========================================
# CSS System
# ==========================================

cat > $BASE/gula-ultra.css <<'EOF'

body{
font-family:Inter,system-ui;
background:#f8fafc;
margin:0;
}

.gula-app{
display:flex;
min-height:100vh;
}

.gula-sidebar{
width:260px;
background:#0f172a;
color:white;
padding:20px;
}

.gula-logo{
font-size:20px;
font-weight:700;
margin-bottom:25px;
}

.gula-menu a{
display:block;
padding:10px;
color:#cbd5e1;
text-decoration:none;
border-radius:8px;
margin-bottom:4px;
}

.gula-menu a:hover{
background:#1e293b;
}

.gula-main{
flex:1;
padding:30px;
}

.gula-header{
display:flex;
justify-content:space-between;
margin-bottom:25px;
}

.gula-search input{
padding:10px;
border-radius:10px;
border:1px solid #ddd;
width:240px;
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
box-shadow:0 6px 25px rgba(0,0,0,0.05);
}

.gula-stat{
font-size:30px;
font-weight:700;
}

.gula-chart{
margin-top:30px;
background:white;
padding:20px;
border-radius:14px;
}

.gula-feed{
margin-top:30px;
background:white;
padding:20px;
border-radius:14px;
}

.sam-panel{
position:fixed;
bottom:20px;
right:20px;
background:white;
padding:14px;
border-radius:12px;
box-shadow:0 10px 30px rgba(0,0,0,0.15);
width:250px;
}

.ali-panel{
margin-top:20px;
background:#fff7ed;
padding:14px;
border-radius:12px;
}

@media(max-width:900px){

.gula-sidebar{
display:none;
}

}

EOF

# ==========================================
# JS UI Engine
# ==========================================

cat > $BASE/gula-ultra.js <<'EOF'

window.addEventListener("load",function(){

document.body.innerHTML = `

<div class="gula-app">

<div class="gula-sidebar">

<div class="gula-logo">GULA</div>

<div class="gula-menu">

<a href="#">Dashboard</a>
<a href="#">Worklist</a>
<a href="#">Patients</a>
<a href="#">Results</a>
<a href="#">Analytics</a>

</div>

</div>

<div class="gula-main">

<div class="gula-header">

<div class="gula-search">

<input placeholder="Search patient or sample">

</div>

</div>

<div class="gula-grid">

<div class="gula-card">

Patients
<div class="gula-stat">1245</div>

</div>

<div class="gula-card">

Samples
<div class="gula-stat">350</div>

</div>

<div class="gula-card">

Tests Today
<div class="gula-stat">890</div>

</div>

<div class="gula-card">

Critical
<div class="gula-stat" style="color:red">12</div>

</div>

</div>

<div class="gula-chart">

<canvas id="chart"></canvas>

</div>

<div class="gula-feed">

<b>Activity</b><br>
Sample A102 processed<br>
Result validated<br>

</div>

<div class="ali-panel">

<b>علي رضا</b><br>
يمكنني تحليل النتائج الطبية وتقديم تفسير.

</div>

</div>

</div>

<div class="sam-panel">

<b>سامر</b><br>
أنا هنا لمساعدتك في استخدام منصة GULA.

</div>

`

const ctx=document.getElementById("chart")

new Chart(ctx,{
type:"line",
data:{
labels:["Mon","Tue","Wed","Thu","Fri"],
datasets:[{
label:"Tests",
data:[120,200,180,220,300]
}]
}
})

})

EOF

# ==========================================
# Inject into HTML
# ==========================================

if ! grep -q "gula-ultra.css" "$HTML"; then

sed -i "s|</head>|<link rel=\"stylesheet\" href=\"gula-ultra.css\">\n<script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>\n</head>|" "$HTML"

fi

if ! grep -q "gula-ultra.js" "$HTML"; then

sed -i "s|</body>|<script src=\"gula-ultra.js\"></script>\n</body>|" "$HTML"

fi

echo "Ultra UI installed."
