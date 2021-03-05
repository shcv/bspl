#!/usr/bin/env python
from setuptools import setup
from setuptools.command.build_py import build_py

import sys

sys.path.append("./protocheck/bspl")
from build import build_parser, save_parser


class Build(build_py):
    def run(self):
        model = build_parser()
        save_parser(model)
        super(Build, self).run()


setup(
    cmdclass={
        "build_py": Build,
    }
)
