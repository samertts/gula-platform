
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

