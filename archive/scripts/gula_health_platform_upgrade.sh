#!/bin/bash

echo "Starting GULA Health Platform Upgrade..."

BASE=~/gula-platform/frontend
API=~/gula-platform/backend

mkdir -p $BASE/components
mkdir -p $BASE/pages
mkdir -p $BASE/js

############################################
# UI Framework Loader
############################################

cat > $BASE/js/gula-core.js <<'EOF'

const GULA = {}

GULA.loadPage = async function(page){

const res = await fetch("/pages/"+page+".html")

const html = await res.text()

document.getElementById("gula-content").innerHTML = html

}

EOF

############################################
# Modern Layout
############################################

cat > $BASE/index.html <<'EOF'

<!DOCTYPE html>
<html>

<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">

<title>GULA Platform</title>

<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

</head>

<body class="bg-gray-100">

<div class="flex min-h-screen">

<div class="w-64 bg-gray-900 text-white p-6">

<h1 class="text-xl font-bold mb-6">
GULA
</h1>

<nav class="space-y-2">

<button onclick="GULA.loadPage('dashboard')" class="block w-full text-left px-3 py-2 hover:bg-gray-700 rounded">Dashboard</button>

<button onclick="GULA.loadPage('patients')" class="block w-full text-left px-3 py-2 hover:bg-gray-700 rounded">Patients</button>

<button onclick="GULA.loadPage('results')" class="block w-full text-left px-3 py-2 hover:bg-gray-700 rounded">Results</button>

<button onclick="GULA.loadPage('analytics')" class="block w-full text-left px-3 py-2 hover:bg-gray-700 rounded">Analytics</button>

</nav>

</div>

<div class="flex-1 p-8">

<div id="gula-content"></div>

</div>

</div>

<div class="fixed bottom-4 right-4 bg-white shadow rounded p-4 w-64">

<b>سامر</b><br>

أنا هنا لمساعدتك أثناء استخدام منصة GULA.

</div>

<script src="/js/gula-core.js"></script>

<script>

GULA.loadPage("dashboard")

</script>

</body>
</html>

EOF

############################################
# Dashboard Page
############################################

cat > $BASE/pages/dashboard.html <<'EOF'

<h1 class="text-2xl font-bold mb-6">

Dashboard

</h1>

<div class="grid grid-cols-4 gap-4">

<div class="bg-white p-6 rounded shadow">

Patients

<p class="text-3xl">1245</p>

</div>

<div class="bg-white p-6 rounded shadow">

Samples

<p class="text-3xl">350</p>

</div>

<div class="bg-white p-6 rounded shadow">

Tests

<p class="text-3xl">890</p>

</div>

<div class="bg-white p-6 rounded shadow">

Critical

<p class="text-3xl text-red-500">12</p>

</div>

</div>

EOF

############################################
# Patients Page
############################################

cat > $BASE/pages/patients.html <<'EOF'

<h1 class="text-2xl font-bold mb-6">

Patients

</h1>

<input placeholder="Search patient..." class="border p-2 w-full mb-4">

<div class="bg-white p-4 rounded shadow">

Ali Hassan

</div>

<div class="bg-white p-4 rounded shadow mt-2">

Sara Ahmed

</div>

EOF

############################################
# Results Page
############################################

cat > $BASE/pages/results.html <<'EOF'

<h1 class="text-2xl font-bold mb-6">

Results

</h1>

<table class="w-full bg-white shadow rounded">

<tr class="bg-gray-200">

<th class="p-2">Patient</th>

<th class="p-2">Test</th>

<th class="p-2">Result</th>

</tr>

<tr>

<td class="p-2">Ali Hassan</td>

<td class="p-2">Glucose</td>

<td class="p-2">120</td>

</tr>

</table>

EOF

############################################
# Analytics Page
############################################

cat > $BASE/pages/analytics.html <<'EOF'

<h1 class="text-2xl font-bold mb-6">

Analytics

</h1>

<canvas id="chart"></canvas>

<script>

const ctx=document.getElementById('chart')

new Chart(ctx,{

type:'bar',

data:{

labels:['CBC','Glucose','Lipid','Creatinine'],

datasets:[{

label:'Tests',

data:[120,90,70,40]

}]

}

})

</script>

EOF

############################################
# Restart Frontend
############################################

docker restart gula-frontend

echo "GULA platform UI upgraded."
