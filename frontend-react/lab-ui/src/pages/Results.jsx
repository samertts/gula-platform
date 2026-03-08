import React,{useState} from "react"

export default function Results(){

const API="http://localhost:8000"

const [order,setOrder]=useState("")
const [test,setTest]=useState("")
const [value,setValue]=useState("")

async function add(){

await fetch(`${API}/results`,{

method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({

order_id:Number(order),
test_id:Number(test),
value:value

})

})

alert("Result saved")

}

return(

<div className="p-8">

<h1 className="text-2xl mb-4">
Enter Result
</h1>

<input
className="border p-2 mr-2"
placeholder="Order ID"
onChange={e=>setOrder(e.target.value)}
/>

<input
className="border p-2 mr-2"
placeholder="Test ID"
onChange={e=>setTest(e.target.value)}
/>

<input
className="border p-2 mr-2"
placeholder="Value"
onChange={e=>setValue(e.target.value)}
/>

<button
onClick={add}
className="bg-green-600 text-white px-4 py-2">
Save
</button>

</div>

)

}
