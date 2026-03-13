
def analyze(test,value):

    if test=="glucose":

        if value>180:

            return "ارتفاع شديد في سكر الدم"

        if value>140:

            return "ارتفاع محتمل في السكر"

    if test=="hb":

        if value<10:

            return "فقر دم محتمل"

    if test=="creatinine":

        if value>1.5:

            return "احتمال ضعف وظائف الكلى"

    return "القيمة ضمن الطبيعي"

