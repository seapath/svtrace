# Copyright (C) 2024, RTE (http://www.rte-france.com)
# Copyright (C) 2024 Savoir-faire Linux, Inc.
# SPDX-License-Identifier: Apache-2.0

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="svtrace",
    version="0.1",
    packages=find_packages(),  # This should detect the 'svtrace' package
    include_package_data=True,
    zip_safe=False,
    package_data={
        'svtrace': ['*.bt', '*.cfg'],  # Ensure package data is included
    },
    install_requires=['pyshark'],
    scripts=['svtrace/svtrace.py'],  # Point to the script inside the package
    url="https://github.com/seapath/svtrace",
    license="Apache-2.0",
    long_description=long_description,
    author="Savoir-faire Linux",
    description="svtrace is a tool used to monitor IEC61850 SV network performance on a machine.",
    keywords="seapath iec61850 samples values performance network SV",
    classifiers=[
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
