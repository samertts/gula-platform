import React from "react"

export default function Sidebar({setPage}){

return(

<div className="w-64 bg-gray-900 text-white min-h-screen p-4">

<h1 className="text-2xl font-bold mb-6">
Lab Platform
</h1>

<button className="block w-full text-left p-2 hover:bg-gray-700"
onClick={()=>setPage("dashboard")}>
Dashboard
</button>

<button className="block w-full text-left p-2 hover:bg-gray-700"
onClick={()=>setPage("patients")}>
Patients
</button>

<button className="block w-full text-left p-2 hover:bg-gray-700"
onClick={()=>setPage("orders")}>
Orders
</button>

<button className="block w-full text-left p-2 hover:bg-gray-700"
onClick={()=>setPage("results")}>
Results
</button>

<button className="block w-full text-left p-2 hover:bg-gray-700"
onClick={()=>setPage("qc")}>
Quality Control
</button>

<button className="block w-full text-left p-2 hover:bg-gray-700"
onClick={()=>setPage("analytics")}>
Analytics
</button>

</div>

)

}
