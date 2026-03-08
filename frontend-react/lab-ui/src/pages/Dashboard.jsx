import React from "react"

export default function Dashboard(){

return(

<div className="p-8">

<h1 className="text-3xl font-bold mb-6">
Laboratory Dashboard
</h1>

<div className="grid grid-cols-3 gap-6">

<div className="bg-white shadow p-6">
<h2 className="text-xl">Patients</h2>
<p>Manage registered patients</p>
</div>

<div className="bg-white shadow p-6">
<h2 className="text-xl">Results</h2>
<p>Enter laboratory results</p>
</div>

<div className="bg-white shadow p-6">
<h2 className="text-xl">Analytics</h2>
<p>Laboratory statistics</p>
</div>

</div>

</div>

)

}
