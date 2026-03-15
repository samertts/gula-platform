#!/bin/bash

# ======================================
# GULA Next UI Layer
# واجهة حديثة دون تغيير backend
# ======================================

set -e

HTML="index.html"
BACKUP="gula_ui_backup_$(date +%s)"

echo "Starting GULA next UI upgrade..."

mkdir -p "$BACKUP"
cp "$HTML" "$BACKUP/"

echo "Backup created."

# ======================================
# CSS
# ======================================

cat > gula-next-ui.css <<'EOF'

body{
font-family:system-ui;
background:#f6f8fb;
margin:0;
}

.gula-layout{
display:flex;
min-height:100vh;
}

.gula-sidebar{
width:240px;
background:#111827;
color:white;
padding:20px;
}

.gula-sidebar h2{
margin-top:0;
}

.gula-menu a{
display:block;
padding:10px;
border-radius:8px;
text-decoration:none;
color:#d1d5db;
margin-bottom:6px;
}

.gula-menu a:hover{
background:#1f2937;
}

.gula-main{
flex:1;
padding:30px;
}

.gula-topbar{
display:flex;
justify-content:space-between;
margin-bottom:20px;
}

.gula-search input{
padding:8px 12px;
border-radius:10px;
border:1px solid #ddd;
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
box-shadow:0 5px 20px rgba(0,0,0,0.05);
transition:0.2s;
}

.gula-card:hover{
transform:translateY(-5px);
}

.gula-stat{
font-size:28px;
font-weight:bold;
}

.gula-chart{
margin-top:30px;
background:white;
padding:20px;
border-radius:14px;
}

.sam-assistant{
position:fixed;
bottom:20px;
right:20px;
background:white;
border-radius:12px;
padding:12px;
box-shadow:0 10px 30px rgba(0,0,0,0.2);
width:240px;
font-size:14px;
}

.ali-panel{
margin-top:30px;
background:#fff7ed;
padding:15px;
border-radius:12px;
}

@media(max-width:800px){

.gula-sidebar{
display:none;
}

}

EOF

# ======================================
# JS
# ======================================

cat > gula-next-ui.js <<'EOF'

window.addEventListener("load",function(){

document.body.innerHTML=`

<div class="gula-layout">

<div class="gula-sidebar">

<h2>GULA</h2>

<div class="gula-menu">

<a href="#">Dashboard</a>
<a href="#">Worklist</a>
<a href="#">Patients</a>
<a href="#">Results</a>
<a href="#">Analytics</a>

</div>

</div>

<div class="gula-main">

<div class="gula-topbar">

<div class="gula-search">

<input placeholder="Search patient, sample...">

</div>

</div>

<div class="gula-grid">

<div class="gula-card">

<div>Patients</div>
<div class="gula-stat">1245</div>

</div>

<div class="gula-card">

<div>Samples</div>
<div class="gula-stat">350</div>

</div>

<div class="gula-card">

<div>Tests Today</div>
<div class="gula-stat">890</div>

</div>

<div class="gula-card">

<div>Critical</div>
<div class="gula-stat" style="color:red">12</div>

</div>

</div>

<div class="gula-chart">

<canvas id="chart"></canvas>

</div>

<div class="ali-panel">

<b>علي رضا</b><br>
يمكنني تحليل النتائج الطبية ومساعدتك في تفسيرها.

</div>

</div>

</div>

<div class="sam-assistant">

<b>سامر</b><br>
أنا هنا لمساعدتك أثناء استخدام المنصة.

</div>

`

const ctx=document.getElementById("chart")

new Chart(ctx,{
type:"bar",
data:{
labels:["CBC","Glucose","Lipid","Creatinine"],
datasets:[{
label:"Tests",
data:[120,90,70,40]
}]
}
})

})

EOF

# ======================================
# إضافة المكتبات
# ======================================

if ! grep -q "gula-next-ui.css" "$HTML"; then

sed -i "s|</head>|<link rel=\"stylesheet\" href=\"gula-next-ui.css\">\n<script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>\n</head>|" "$HTML"

fi

if ! grep -q "gula-next-ui.js" "$HTML"; then

sed -i "s|</body>|<script src=\"gula-next-ui.js\"></script>\n</body>|" "$HTML"

fi

echo "GULA next UI installed."
