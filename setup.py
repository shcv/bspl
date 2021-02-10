#!/usr/bin/env python
from setuptools import setup, find_packages

# entry_points = {
#     'console_scripts': ['bspl = protocheck.main:main'],
# }

setup(
    name="bungie",
    version="0.0.0",
    author="Samuel Christie",
    author_email="schrist@ncsu.edu",
    description="Agent implementation framework",
    long_description=open("README.org").read(),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
    ],
    # entry_points=entry_points,
    install_requires=[
        "protocheck @ git+https://gitlab.com/masr/protocheck.git",
        "aiocron",
        "pyyaml",
        "ijson",
        "aiorun",
        "uvloop",
        "argparse",
    ],
    packages=find_packages(),

    test_suite='bungie'
)
