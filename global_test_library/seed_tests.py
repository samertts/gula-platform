from test_library_db import init_db
from test_loader import add_test

init_db()

add_test("Hemoglobin", "HGB", "Hematology", "g/dL", 13, 17)
add_test("White Blood Cells", "WBC", "Hematology", "cells/uL", 4000, 11000)
add_test("Platelets", "PLT", "Hematology", "cells/uL", 150000, 450000)
add_test("Glucose", "GLU", "Chemistry", "mg/dL", 70, 110)
add_test("Vitamin D", "VITD", "Chemistry", "ng/mL", 30, 100)
add_test("TSH", "TSH", "Hormone", "mIU/L", 0.4, 4.0)

print("Library initialized")
