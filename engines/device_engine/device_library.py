devices = {
    "sysmex_xs1000i": {
        "type": "hematology",
        "protocol": "serial",
        "tests": ["WBC", "RBC", "HGB", "PLT"],
    },
    "mindray_bc30": {
        "type": "hematology",
        "protocol": "serial",
        "tests": ["WBC", "RBC", "HGB", "PLT"],
    },
    "abbott_architect": {
        "type": "chemistry",
        "protocol": "tcp",
        "tests": ["ALT", "AST", "CRE", "GLU"],
    },
    "roche_cobas_c311": {
        "type": "chemistry",
        "protocol": "tcp",
        "tests": ["ALT", "AST", "BUN", "CRE"],
    },
}
