from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="seapath-trace",
    version="0.1",
    packages=find_packages(),  # This should detect the 'seapath_trace' package
    include_package_data=True,
    zip_safe=False,
    package_data={
        'seapath_trace': ['*.bt', '*.cfg'],  # Ensure package data is included
    },
    install_requires=['pyshark'],
    scripts=['seapath_trace/seapath-trace.py'],  # Point to the script inside the package
    url="https://github.com/seapath/seapath-trace",
    license="Apache-2.0",
    long_description=long_description,
    author="Savoir-faire Linux",
    description="Seapath-trace is a tool used to monitor IEC61850 SV network performance on a machine.",
    keywords="seapath iec61850 samples values performance network SV",
    classifiers=[
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
