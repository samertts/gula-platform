
def analyze(test,value):

    advice=None

    if test=="glucose":

        if value>180:
            advice="ارتفاع شديد في سكر الدم"

        elif value>140:
            advice="ارتفاع محتمل في مستوى السكر"

    if test=="hb":

        if value<10:
            advice="فقر دم محتمل"

    if test=="creatinine":

        if value>1.5:
            advice="قد يكون هناك ضعف في وظائف الكلى"

    return advice

