#!/bin/bash

echo "Installing GULA Professional UI..."

BASE=~/gula-platform/frontend

mkdir -p $BASE/css
mkdir -p $BASE/pages

########################################
echo "Professional UI CSS"
########################################

cat > $BASE/css/pro.css <<'EOF'

body{
font-family:system-ui;
background:linear-gradient(180deg,#020617,#0f172a);
color:white;
margin:0;
}

.sidebar{
position:fixed;
left:0;
top:0;
bottom:0;
width:250px;
background:rgba(2,6,23,0.9);
backdrop-filter:blur(20px);
padding:25px;
}

.logo{
font-size:22px;
font-weight:bold;
margin-bottom:30px;
}

.nav{
display:block;
padding:12px;
border-radius:8px;
margin-bottom:8px;
color:#cbd5f5;
cursor:pointer;
}

.nav:hover{
background:#1e293b;
}

.content{
margin-left:250px;
padding:30px;
}

.grid{
display:grid;
grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
gap:20px;
}

.card{
background:rgba(17,24,39,0.6);
border:1px solid rgba(255,255,255,0.05);
padding:25px;
border-radius:14px;
backdrop-filter:blur(20px);
transition:0.2s;
}

.card:hover{
transform:translateY(-5px);
}

.stat{
font-size:30px;
margin-top:10px;
}

.sam{
position:fixed;
bottom:20px;
right:20px;
width:270px;
background:#111827;
border-radius:12px;
overflow:hidden;
box-shadow:0 20px 50px rgba(0,0,0,0.5);
}

.sam-head{
background:#6366f1;
padding:10px;
}

.sam-body{
padding:14px;
font-size:14px;
}

.mobile-nav{
display:none;
position:fixed;
bottom:0;
left:0;
right:0;
background:#020617;
padding:10px;
justify-content:space-around;
}

.mobile-nav div{
color:#cbd5f5;
}

@media(max-width:900px){

.sidebar{
display:none;
}

.content{
margin-left:0;
padding-bottom:80px;
}

.mobile-nav{
display:flex;
}

}

EOF

########################################
echo "Professional index.html"
########################################

cat > $BASE/index.html <<'EOF'

<!DOCTYPE html>
<html>

<head>

<meta charset="UTF-8">
<title>GULA</title>

<meta name="viewport" content="width=device-width,initial-scale=1">

<link rel="stylesheet" href="/css/pro.css">

</head>

<body>

<div class="sidebar">

<div class="logo">
GULA
</div>

<div class="nav" onclick="loadPage('dashboard')">Dashboard</div>
<div class="nav" onclick="loadPage('worklist')">Worklist</div>
<div class="nav" onclick="loadPage('patients')">Patients</div>
<div class="nav" onclick="loadPage('results')">Results</div>
<div class="nav" onclick="loadPage('analytics')">Analytics</div>

</div>

<div class="content">

<div id="content"></div>

</div>

<div class="sam">

<div class="sam-head">
سامر
</div>

<div class="sam-body">

أنا سامر. سأرشدك أثناء استخدام منصة GULA.

</div>

</div>

<div class="mobile-nav">

<div onclick="loadPage('dashboard')">Dashboard</div>
<div onclick="loadPage('worklist')">Worklist</div>
<div onclick="loadPage('patients')">Patients</div>
<div onclick="loadPage('results')">Results</div>

</div>

<script src="/js/ui.js"></script>

</body>

</html>

EOF

########################################
echo "Professional dashboard"
########################################

cat > $BASE/pages/dashboard.html <<'EOF'

<h1 style="margin-bottom:25px;">Dashboard</h1>

<div class="grid">

<div class="card">
Patients
<div class="stat">1200</div>
</div>

<div class="card">
Samples
<div class="stat">320</div>
</div>

<div class="card">
Tests
<div class="stat">890</div>
</div>

<div class="card">
Critical
<div class="stat" style="color:#ef4444;">5</div>
</div>

</div>

EOF

########################################
echo "Restart frontend"
########################################

docker restart gula-frontend

echo "GULA Professional UI installed successfully"
