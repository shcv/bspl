import bspl

grading = bspl.load_file("grading.bspl").export("Grading")

with open("/proc/self/cgroup", "r") as cgroups:
    from Grading import (
        Prof,
        Student,
        TA,
        begin_test,
        challenge,
        rubric,
        response,
        result,
    )

    in_docker = "docker" in cgroups.read()

if in_docker:
    config = {
        Prof: ("prof", 8000),
        Student: ("student", 8000),
        TA: ("ta", 8000),
    }
else:
    config = {
        Prof: ("0.0.0.0", 8000),
        Student: ("0.0.0.0", 8001),
        TA: ("0.0.0.0", 8002),
    }
