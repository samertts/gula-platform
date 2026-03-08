import os

BASE = os.path.expanduser("~/lab-platform/frontend/lab")

pages = {

"lab_control_panel.html": """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Lab Control Panel</title>

<style>
body{font-family:Arial;background:#f5f7fa;margin:0}
header{background:#1e88e5;color:white;padding:15px;font-size:20px}
nav{width:220px;background:#263238;height:100vh;color:white;float:left}
nav a{display:block;color:white;padding:12px;text-decoration:none}
nav a:hover{background:#37474f}
main{margin-left:220px;padding:20px}
.card{background:white;padding:20px;margin:10px;border-radius:6px}
</style>

</head>

<body>

<header>Laboratory Platform</header>

<nav>
<a href="dashboard.html">Dashboard</a>
<a href="result_entry.html">Result Entry</a>
<a href="sample_tracking.html">Sample Tracking</a>
<a href="devices.html">Devices</a>
<a href="reports.html">Reports</a>
</nav>

<main>

<h2>System Status</h2>

<div class="card">
API Status: <span id="api"></span>
</div>

<div class="card">
Connected Devices: <span id="devices"></span>
</div>

</main>

<script>

fetch("http://localhost:8000/status")
.then(r=>r.json())
.then(d=>{
document.getElementById("api").innerText=d.status
})

</script>

</body>
</html>
""",

"dashboard.html":"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Dashboard</title>
</head>
<body>

<h2>Laboratory Dashboard</h2>

<div id="stats"></div>

<script>

fetch("http://localhost:8000/labs/stats")
.then(r=>r.json())
.then(d=>{
document.getElementById("stats").innerHTML=
"Tests today: "+d.tests+"<br>"+
"Samples: "+d.samples
})

</script>

</body>
</html>
""",

"result_entry.html":"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Result Entry</title>
</head>

<body>

<h2>Enter Lab Result</h2>

<form id="form">

Test:
<input name="test">

Value:
<input name="value">

<button>Save</button>

</form>

<script>

document.getElementById("form").onsubmit=async(e)=>{
e.preventDefault()

let f=new FormData(e.target)

await fetch("http://localhost:8000/results/add",{
method:"POST",
body:f
})

alert("saved")

}

</script>

</body>
</html>
""",

"sample_tracking.html":"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Sample Tracking</title>
</head>

<body>

<h2>Sample Tracking</h2>

<input id="barcode" placeholder="scan barcode">

<button onclick="track()">Track</button>

<div id="result"></div>

<script>

function track(){

let b=document.getElementById("barcode").value

fetch("http://localhost:8000/sample/"+b)
.then(r=>r.json())
.then(d=>{

document.getElementById("result").innerHTML=
"Location:"+d.location+
"<br>Device:"+d.device+
"<br>Technician:"+d.tech

})

}

</script>

</body>
</html>
""",

"devices.html":"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Devices</title>
</head>

<body>

<h2>Connected Devices</h2>

<ul id="devices"></ul>

<script>

fetch("http://localhost:8000/devices")
.then(r=>r.json())
.then(d=>{

let html=""

d.forEach(i=>{
html+="<li>"+i.name+" ("+i.type+")</li>"
})

document.getElementById("devices").innerHTML=html

})

</script>

</body>
</html>
""",

"reports.html":"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Reports</title>
</head>

<body>

<h2>Reports</h2>

<button onclick="load()">Load Reports</button>

<div id="reports"></div>

<script>

function load(){

fetch("http://localhost:8000/reports")
.then(r=>r.json())
.then(d=>{

let html=""

d.forEach(r=>{
html+="<p>"+r+"</p>"
})

document.getElementById("reports").innerHTML=html

})

}

</script>

</body>
</html>
"""

}

os.makedirs(BASE,exist_ok=True)

for name,html in pages.items():

    path=os.path.join(BASE,name)

    with open(path,"w") as f:
        f.write(html)

print("Frontend pages created:",len(pages))
