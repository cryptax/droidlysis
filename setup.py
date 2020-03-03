#!/usr/bin/env python3

from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name = 'droidlysis',
    description='DroidLysis: pre-analysis script for suspicious Android samples',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='@cryptax',
    author_email='aafortinet@gmail.com',
    url='https://github.com/cryptax/droidlysis',
    license='MIT',
    keywords="android malware reverse",
    python_requires='>=3.0.*',
    version = '3.1.0',
    packages=['conf'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Operating System :: Unix",
        "Topic :: Software Development :: Disassemblers",
    ],
    include_package_data=True,
    install_requires=[ 'configparser', 'python-magic', 'SQLAlchemy', 'rarfile', 'androguard' ],
    scripts = [ 'droidlysis3.py', 'droidconfig.py', 'droidcountry.py', 'droidproperties.py', 'droidreport.py', 'droidsample.py', 'droidsql.py', 'droidurl.py', 'droidutil.py', 'droidziprar.py' ],
)
