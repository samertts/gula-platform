import React,{useState,useEffect} from "react"

export default function Patients(){

const API="http://localhost:8000"

const [patients,setPatients]=useState([])
const [first,setFirst]=useState("")
const [last,setLast]=useState("")
const [age,setAge]=useState("")
const [gender,setGender]=useState("")

async function load(){

const res=await fetch(`${API}/patients`)
const data=await res.json()

setPatients(data)

}

async function add(){

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

load()

}

useEffect(()=>{
load()
},[])

return(

<div className="p-8">

<h1 className="text-2xl mb-4">
Patients
</h1>

<div className="mb-6">

<input
className="border p-2 mr-2"
placeholder="First"
onChange={e=>setFirst(e.target.value)}
/>

<input
className="border p-2 mr-2"
placeholder="Last"
onChange={e=>setLast(e.target.value)}
/>

<input
className="border p-2 mr-2"
placeholder="Age"
onChange={e=>setAge(e.target.value)}
/>

<input
className="border p-2 mr-2"
placeholder="Gender"
onChange={e=>setGender(e.target.value)}
/>

<button
onClick={add}
className="bg-blue-600 text-white px-4 py-2">
Add
</button>

</div>

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

<tr key={p[0]}>

<td>{p[0]}</td>
<td>{p[1]} {p[2]}</td>
<td>{p[3]}</td>
<td>{p[4]}</td>

</tr>

))}

</tbody>

</table>

</div>

)

}
