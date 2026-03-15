#!/bin/bash

echo "Upgrading GULA UI..."

BASE=~/gula-platform/frontend

########################################
echo "Creating modern style"
########################################

cat > $BASE/css/modern.css <<'EOF'

body{
font-family:system-ui;
background:#0f172a;
color:white;
}

.sidebar{
width:260px;
background:#020617;
position:fixed;
top:0;
left:0;
bottom:0;
padding:20px;
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
margin-bottom:6px;
color:#cbd5f5;
}

.nav:hover{
background:#1e293b;
}

.content{
margin-left:260px;
padding:30px;
}

.card{
background:#111827;
padding:20px;
border-radius:12px;
box-shadow:0 4px 20px rgba(0,0,0,0.3);
}

.grid{
display:grid;
grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
gap:20px;
}

.sam-box{
position:fixed;
bottom:20px;
right:20px;
width:260px;
background:#111827;
border-radius:12px;
overflow:hidden;
box-shadow:0 10px 40px rgba(0,0,0,0.5);
}

.sam-head{
background:#6366f1;
padding:10px;
}

.sam-body{
padding:12px;
font-size:14px;
}

@media(max-width:900px){

.sidebar{
display:none;
}

.content{
margin-left:0;
}

}

EOF

########################################
echo "Updating index.html"
########################################

cat > $BASE/index.html <<'EOF'

<!DOCTYPE html>
<html>

<head>

<meta charset="UTF-8">
<title>GULA Platform</title>

<meta name="viewport" content="width=device-width,initial-scale=1">

<link rel="stylesheet" href="/css/modern.css">

</head>

<body>

<div class="sidebar">

<div class="logo">
GULA
</div>

<a class="nav" onclick="loadPage('dashboard')">Dashboard</a>
<a class="nav" onclick="loadPage('worklist')">Worklist</a>
<a class="nav" onclick="loadPage('patients')">Patients</a>
<a class="nav" onclick="loadPage('results')">Results</a>
<a class="nav" onclick="loadPage('analytics')">Analytics</a>

</div>

<div class="content">

<div id="content"></div>

</div>

<div class="sam-box">

<div class="sam-head">
سامر
</div>

<div class="sam-body">

أنا سامر. سأساعدك أثناء استخدام منصة GULA.

</div>

</div>

<script src="/js/ui.js"></script>

</body>

</html>

EOF

########################################
echo "Creating improved dashboard"
########################################

cat > $BASE/pages/dashboard.html <<'EOF'

<h1 style="margin-bottom:20px;">Dashboard</h1>

<div class="grid">

<div class="card">

<h3>Patients</h3>
<p style="font-size:30px;">1200</p>

</div>

<div class="card">

<h3>Samples</h3>
<p style="font-size:30px;">320</p>

</div>

<div class="card">

<h3>Tests</h3>
<p style="font-size:30px;">890</p>

</div>

<div class="card">

<h3>Critical</h3>
<p style="font-size:30px;color:red;">5</p>

</div>

</div>

EOF

########################################
echo "Restart frontend"

docker restart gula-frontend

echo "GULA UI upgraded successfully"

