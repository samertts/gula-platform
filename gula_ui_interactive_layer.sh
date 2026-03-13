#!/bin/bash

echo "Installing GULA Interactive UI Layer..."

BASE=~/gula-platform/frontend

mkdir -p $BASE/js
mkdir -p $BASE/pages

########################################
echo "Adding Chart.js loader"
########################################

if ! grep -q "chart.js" $BASE/index.html; then
sed -i '/<\/head>/i <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>' $BASE/index.html
fi

########################################
echo "Realtime dashboard script"
########################################

cat > $BASE/js/realtime.js <<'EOF'

async function updateDashboard(){

try{

let r=await fetch("/dashboard")
let data=await r.json()

let patients=document.getElementById("patients")
let samples=document.getElementById("samples")
let tests=document.getElementById("tests")
let critical=document.getElementById("critical")

if(patients)patients.innerText=data.patients
if(samples)samples.innerText=data.samples
if(tests)tests.innerText=data.tests
if(critical)critical.innerText=data.critical

}catch(e){

console.log("realtime error")

}

}

setInterval(updateDashboard,10000)

EOF

########################################
echo "Patient search"
########################################

cat > $BASE/js/patient_search.js <<'EOF'

function searchPatients(){

let input=document.getElementById("patientSearch")

if(!input)return

input.addEventListener("keyup",function(){

let q=this.value.toLowerCase()

document.querySelectorAll(".patient-row").forEach(row=>{

row.style.display=row.innerText.toLowerCase().includes(q)
?"block":"none"

})

})

}

setTimeout(searchPatients,500)

EOF

########################################
echo "Analytics page with charts"
########################################

cat > $BASE/pages/analytics.html <<'EOF'

<h1 style="margin-bottom:20px;">Analytics</h1>

<canvas id="labChart"></canvas>

<script>

const ctx=document.getElementById('labChart');

new Chart(ctx,{

type:'bar',

data:{

labels:['CBC','Glucose','Lipid','Creatinine'],

datasets:[{

label:'Tests',

data:[120,90,70,40],

backgroundColor:'#6366f1'

}]

},

options:{responsive:true}

})

</script>

EOF

########################################
echo "Improved dashboard with realtime IDs"
########################################

cat > $BASE/pages/dashboard.html <<'EOF'

<h1 style="margin-bottom:25px;">Dashboard</h1>

<div class="grid">

<div class="card">
Patients
<div class="stat" id="patients">1200</div>
</div>

<div class="card">
Samples
<div class="stat" id="samples">320</div>
</div>

<div class="card">
Tests
<div class="stat" id="tests">890</div>
</div>

<div class="card">
Critical
<div class="stat" id="critical" style="color:#ef4444;">5</div>
</div>

</div>

<script src="/js/realtime.js"></script>

EOF

########################################
echo "Patients page with search"
########################################

cat > $BASE/pages/patients.html <<'EOF'

<h1>Patients</h1>

<input id="patientSearch" placeholder="Search patient..." style="padding:10px;margin-bottom:15px;width:100%;">

<div class="patient-row">Ali Hassan</div>
<div class="patient-row">Sara Ahmed</div>
<div class="patient-row">Mohammed Ali</div>

<script src="/js/patient_search.js"></script>

EOF

########################################
echo "Restart frontend"
########################################

docker restart gula-frontend

echo "GULA Interactive UI installed successfully"
