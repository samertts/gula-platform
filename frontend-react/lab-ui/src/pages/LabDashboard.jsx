import { useState, useEffect } from "react"

export default function LabDashboard(){

const [patients,setPatients]=useState([])
const [first,setFirst]=useState("")
const [last,setLast]=useState("")
const [age,setAge]=useState("")
const [gender,setGender]=useState("")

const API="http://localhost:8000"

async function loadPatients(){

const res=await fetch(`${API}/patients`)
const data=await res.json()

setPatients(data)

}

async function addPatient(){

await fetch(`${API}/patients`,{

method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({

first_name:first,
last_name:last,
age:Number(age),
gender:gender

})

})

loadPatients()

}

useEffect(()=>{
loadPatients()
},[])

return(

<div className="p-10">

<h1 className="text-3xl font-bold mb-6">
Laboratory Dashboard
</h1>

<div className="bg-white shadow p-6 mb-6">

<h2 className="text-xl mb-4">
Add Patient
</h2>

<div className="grid grid-cols-4 gap-4">

<input
className="border p-2"
placeholder="First Name"
value={first}
onChange={e=>setFirst(e.target.value)}
/>

<input
className="border p-2"
placeholder="Last Name"
value={last}
onChange={e=>setLast(e.target.value)}
/>

<input
className="border p-2"
placeholder="Age"
value={age}
onChange={e=>setAge(e.target.value)}
/>

<input
className="border p-2"
placeholder="Gender"
value={gender}
onChange={e=>setGender(e.target.value)}
/>

</div>

<button
onClick={addPatient}
className="bg-blue-500 text-white px-4 py-2 mt-4"
>
Add Patient
</button>

</div>

<div className="bg-white shadow p-6">

<h2 className="text-xl mb-4">
Patients
</h2>

<table className="w-full">

<thead>

<tr className="border-b">

<th>ID</th>
<th>Name</th>
<th>Age</th>
<th>Gender</th>

</tr>

</thead>

<tbody>

{patients.map(p=>(

<tr key={p[0]} className="border-b">

<td>{p[0]}</td>
<td>{p[1]} {p[2]}</td>
<td>{p[3]}</td>
<td>{p[4]}</td>

</tr>

))}

</tbody>

</table>

</div>

</div>

)

}
