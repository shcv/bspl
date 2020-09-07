#!/usr/bin/env python
from setuptools import setup, find_packages

from protocheck import __version__ as version

entry_points = {
    'console_scripts': ['bspl = protocheck.main:main'],
}

setup(
    name='protocheck',
    version=version,

    author='Samuel Christie',
    author_email='schrist@ncsu.edu',

    description='Protocol verification tool for BSPL',
    long_description=open('README.org').read(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers'
    ],

    entry_points=entry_points,

    setup_requires=[
        "setuptools_git >= 0.3",
    ],

    install_requires=[
        'pytest',
        'TatSu',
        'boolexpr',
        'configargparse',
        'simplejson',
        'ttictoc',
    ],

    packages=find_packages(),
    include_package_data=True,

    test_suite='protocheck'
)
