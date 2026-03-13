
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

