function samerInit(){

fetch("/components/samer_assistant.html")
.then(r=>r.text())
.then(html=>{

document.body.insertAdjacentHTML("beforeend",html)

document.getElementById("samer-button")
.onclick=toggleSamer

})

}

function toggleSamer(){

let panel=document.getElementById("samer-panel")

panel.classList.toggle("hidden")

}

function samerSend(){

let input=document.getElementById("samer-input")
let chat=document.getElementById("samer-chat")

let text=input.value.trim()

if(!text) return

chat.innerHTML+=`
<div class="bg-indigo-600 p-2 rounded text-white">
${text}
</div>
`

input.value=""

let reply=samerLocalLogic(text)

chat.innerHTML+=`
<div class="bg-gray-800 p-2 rounded">
${reply}
</div>
`

chat.scrollTop=chat.scrollHeight

}

function samerLocalLogic(text){

text=text.toLowerCase()

if(text.includes("worklist"))
return "الـ Worklist تعرض العينات التي تحتاج مراجعة أو تحليل."

if(text.includes("patient"))
return "يمكنك البحث عن المرضى من صفحة Patients."

if(text.includes("result"))
return "نتائج الفحوصات تظهر في صفحة Results بعد اعتمادها."

return "يمكنني مساعدتك في التنقل داخل المنصة أو شرح الميزات."
}

document.addEventListener("DOMContentLoaded",samerInit)
