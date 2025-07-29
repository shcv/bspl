import bspl

grading = bspl.load_file("../../samples/domain-specific/grading.bspl").export("Grading")
from Grading import Prof, Student, TA

agents = {
    "Galahad": [("127.0.0.1", 8010)],
    "Lancelot": [("127.0.0.1", 8011)],
    "Pnin": [("127.0.0.1", 8001)],
    "Timofey": [("127.0.0.1", 8002)],
}

systems = {
    "galahad": {
        "protocol": grading,
        "roles": {
            Student: "Galahad",
            Prof: "Pnin",
            TA: "Timofey",
        },
    },
    "lancelot": {
        "protocol": grading,
        "roles": {
            Student: "Lancelot",
            Prof: "Pnin",
            TA: "Timofey",
        },
    },
}
