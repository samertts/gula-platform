GLOBAL_TESTS = [
    {
        "code": "CBC",
        "name": "Complete Blood Count",
        "category": "Hematology",
        "tests": [
            {"name": "WBC", "normal_range": "4000-11000"},
            {"name": "RBC", "normal_range": "4.0-5.5"},
            {"name": "HGB", "normal_range": "12-17"},
            {"name": "PLT", "normal_range": "150000-450000"},
        ],
    },
    {
        "code": "LIPID",
        "name": "Lipid Panel",
        "category": "Chemistry",
        "tests": [
            {"name": "Cholesterol", "normal_range": "<200"},
            {"name": "HDL", "normal_range": ">40"},
            {"name": "LDL", "normal_range": "<130"},
            {"name": "Triglycerides", "normal_range": "<150"},
        ],
    },
    {
        "code": "LIVER",
        "name": "Liver Function",
        "category": "Chemistry",
        "tests": [
            {"name": "ALT", "normal_range": "7-56"},
            {"name": "AST", "normal_range": "10-40"},
            {"name": "ALP", "normal_range": "44-147"},
            {"name": "Bilirubin", "normal_range": "0.1-1.2"},
        ],
    },
    {
        "code": "THYROID",
        "name": "Thyroid Panel",
        "category": "Hormones",
        "tests": [
            {"name": "TSH", "normal_range": "0.4-4.0"},
            {"name": "T3", "normal_range": "80-200"},
            {"name": "T4", "normal_range": "5-12"},
        ],
    },
]
