#!/bin/bash

BASE=~/gula-platform/frontend
MOD=$BASE/modules

echo "Installing GULA advanced modules..."

mkdir -p $MOD

########################################
echo "Advanced Worklist"
########################################

cat > $BASE/pages/worklist.html <<'EOF'

<h2 class="text-2xl mb-6">
Laboratory Worklist
</h2>

<input id="search" placeholder="Search patient..." class="p-2 mb-4 text-black">

<table class="w-full bg-gray-800 rounded">

<thead>
<tr>
<th class="p-3">Sample</th>
<th class="p-3">Patient</th>
<th class="p-3">Test</th>
<th class="p-3">Status</th>
</tr>
</thead>

<tbody id="worklist"></tbody>

</table>

<script>

async function loadWorklist(){

try{

let r = await fetch("/api/worklist")
let data = await r.json()

let html=""

data.forEach(x=>{

html+=`
<tr>
<td class="p-3">${x.sample}</td>
<td class="p-3">${x.patient}</td>
<td class="p-3">${x.test}</td>
<td class="p-3">${x.status}</td>
</tr>
`

})

document.getElementById("worklist").innerHTML=html

}catch(e){

console.log("Worklist offline mode")

}

}

loadWorklist()

</script>

EOF

########################################
echo "Patients page"
########################################

cat > $BASE/pages/patients.html <<'EOF'

<h2 class="text-2xl mb-6">
Patients
</h2>

<input id="search" placeholder="Search patient..." class="p-2 mb-4 text-black">

<div id="patients"></div>

<script>

async function loadPatients(){

try{

let r=await fetch("/api/patients")
let data=await r.json()

let html=""

data.forEach(p=>{

html+=`
<div class="card">
${p.name}
</div>
`

})

document.getElementById("patients").innerHTML=html

}catch(e){

console.log("Patient API unavailable")

}

}

loadPatients()

</script>

EOF

########################################
echo "Results page"
########################################

cat > $BASE/pages/results.html <<'EOF'

<h2 class="text-2xl mb-6">
Lab Results
</h2>

<table class="w-full bg-gray-800 rounded">

<thead>
<tr>
<th class="p-3">Patient</th>
<th class="p-3">Test</th>
<th class="p-3">Value</th>
<th class="p-3">Analysis</th>
</tr>
</thead>

<tbody id="results"></tbody>

</table>

<script>

async function loadResults(){

try{

let r=await fetch("/api/results")
let data=await r.json()

let html=""

data.forEach(x=>{

html+=`
<tr>

<td class="p-3">${x.patient}</td>
<td class="p-3">${x.test}</td>
<td class="p-3">${x.value}</td>

<td class="p-3">

<button onclick="aliRezaAnalyze('${x.test}',${x.value})">

Analyze

</button>

</td>

</tr>
`

})

document.getElementById("results").innerHTML=html

}catch(e){

console.log("Results API unavailable")

}

}

loadResults()

</script>

EOF

########################################
echo "Sample Tracking"
########################################

cat > $BASE/pages/tracking.html <<'EOF'

<h2 class="text-2xl mb-6">
Sample Tracking
</h2>

<input placeholder="Scan sample barcode..." class="p-2 text-black">

<div class="card">

Tracking system ready.

</div>

EOF

########################################
echo "Analytics page"
########################################

cat > $BASE/pages/analytics.html <<'EOF'

<h2 class="text-2xl mb-6">
Analytics
</h2>

<div class="card">

Population statistics coming soon.

</div>

EOF

########################################
echo "Samir assistant intelligence"
########################################

cat > $MOD/samir_assistant.js <<'EOF'

function samirHelp(){

console.log("سامر جاهز لمساعدتك")

}

samirHelp()

EOF

########################################
echo "Ali Reza medical intelligence"
########################################

cat > $MOD/ali_reza_medical.js <<'EOF'

function aliRezaMedical(test,value){

let advice=""

if(test=="glucose" && value>140)
advice="ارتفاع محتمل في السكر"

if(test=="hb" && value<11)
advice="فقر دم محتمل"

if(advice!="")
alert("علي رضا:\n"+advice)

}

window.aliRezaAnalyze=aliRezaMedical

EOF

########################################
echo "Restart frontend"
########################################

docker restart gula-frontend

echo "GULA advanced modules installed"
