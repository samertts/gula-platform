#!/bin/bash

BASE=~/gula-platform/frontend

echo "Initializing GULA Frontend..."

mkdir -p $BASE/js
mkdir -p $BASE/css
mkdir -p $BASE/pages
mkdir -p $BASE/assets
mkdir -p $BASE/modules

########################################
echo "Creating index.html"
########################################

cat > $BASE/index.html <<'EOF'

<!DOCTYPE html>
<html>

<head>

<meta charset="UTF-8">
<title>GULA Platform</title>

<meta name="viewport" content="width=device-width, initial-scale=1">

<script src="https://cdn.tailwindcss.com"></script>

<link rel="stylesheet" href="/css/style.css">

</head>

<body class="bg-gray-950 text-white">

<div class="flex h-screen">

<div class="w-64 bg-black p-6">

<h1 class="text-xl font-bold mb-6">
GULA
</h1>

<nav class="space-y-2">

<button onclick="loadPage('dashboard')" class="nav">Dashboard</button>
<button onclick="loadPage('worklist')" class="nav">Worklist</button>
<button onclick="loadPage('patients')" class="nav">Patients</button>
<button onclick="loadPage('results')" class="nav">Results</button>
<button onclick="loadPage('analytics')" class="nav">Analytics</button>

</nav>

</div>

<div class="flex-1 p-10 overflow-auto">

<div id="content"></div>

</div>

</div>

<script src="/js/api.js"></script>
<script src="/js/ui.js"></script>

<script src="/modules/samir.js"></script>
<script src="/modules/ali_reza.js"></script>
<script src="/modules/realtime.js"></script>
<script src="/modules/search.js"></script>
<script src="/modules/intelligence.js"></script>

</body>

</html>

EOF

########################################
echo "CSS"
########################################

cat > $BASE/css/style.css <<'EOF'

body{
font-family:system-ui;
}

.nav{
display:block;
width:100%;
text-align:left;
padding:10px;
border-radius:6px;
}

.nav:hover{
background:#1f2937;
}

.card{
background:#111827;
padding:20px;
border-radius:10px;
margin-bottom:10px;
}

EOF

########################################
echo "API layer"
########################################

cat > $BASE/js/api.js <<'EOF'

const API="/api"

async function api(path){

try{

let r=await fetch(API+path)
return r.json()

}catch(e){

return {}

}

}

EOF

########################################
echo "UI loader"
########################################

cat > $BASE/js/ui.js <<'EOF'

async function loadPage(page){

let r=await fetch("/pages/"+page+".html")
let html=await r.text()

document.getElementById("content").innerHTML=html

}

loadPage("dashboard")

EOF

########################################
echo "Samir guide"
########################################

cat > $BASE/modules/samir.js <<'EOF'

function samir(){

const box=document.createElement("div")

box.innerHTML=`

<div style="position:fixed;bottom:20px;right:20px;width:260px;background:#111827;border-radius:10px">

<div style="background:#4f46e5;padding:10px">
سامر
</div>

<div style="padding:10px">

أنا سامر.
سأساعدك أثناء استخدام منصة GULA.

</div>

</div>

`

document.body.appendChild(box)

}

samir()

EOF

########################################
echo "Ali Reza"
########################################

cat > $BASE/modules/ali_reza.js <<'EOF'

function aliReza(){

window.aliRezaAnalyze=function(test,value){

let advice=""

if(test=="glucose" && value>140)
advice="ارتفاع محتمل في السكر"

if(test=="hb" && value<11)
advice="احتمال فقر دم"

if(advice!="")
alert("علي رضا:\n"+advice)

}

}

aliReza()

EOF

########################################
echo "Realtime dashboard"
########################################

cat > $BASE/modules/realtime.js <<'EOF'

async function realtime(){

try{

let r=await fetch("/api/dashboard")
let d=await r.json()

if(document.getElementById("patients"))
patients.innerText=d.patients

}catch(e){}

}

setInterval(realtime,15000)

EOF

########################################
echo "Search"
########################################

cat > $BASE/modules/search.js <<'EOF'

function search(){

let input=document.getElementById("search")

if(!input) return

input.addEventListener("keyup",function(){

let q=this.value.toLowerCase()

document.querySelectorAll(".card").forEach(c=>{

c.style.display = c.innerText.toLowerCase().includes(q) ? "block":"none"

})

})

}

setTimeout(search,1000)

EOF

########################################
echo "Intelligence layer"
########################################

cat > $BASE/modules/intelligence.js <<'EOF'

function intelligence(){

console.log("GULA Intelligence layer active")

}

intelligence()

EOF

########################################
echo "Dashboard"
########################################

cat > $BASE/pages/dashboard.html <<'EOF'

<h2 class="text-3xl mb-6">
Dashboard
</h2>

<div class="grid grid-cols-4 gap-4">

<div class="card">
Patients
<p id="patients" class="text-3xl">1200</p>
</div>

<div class="card">
Samples
<p class="text-3xl">320</p>
</div>

<div class="card">
Tests
<p class="text-3xl">890</p>
</div>

<div class="card">
Critical
<p class="text-3xl text-red-500">5</p>
</div>

</div>

EOF

########################################
echo "Worklist"
########################################

cat > $BASE/pages/worklist.html <<'EOF'

<h2 class="text-2xl mb-6">
Worklist
</h2>

<table class="w-full bg-gray-800 rounded">

<tr>
<th class="p-3">Sample</th>
<th class="p-3">Patient</th>
<th class="p-3">Test</th>
</tr>

<tr>
<td class="p-3">A101</td>
<td class="p-3">Ali</td>
<td class="p-3">CBC</td>
</tr>

</table>

EOF

########################################
echo "Restarting container"
########################################

docker restart gula-frontend

echo "GULA Frontend Ready"
