#!/usr/bin/env python3

from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
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
    version = '3.4.0',
    packages=['conf'],
    py_modules=[
        'droidconfig',
        'droidcountry',
        'droidlysis3',
        'droidproperties',
        'droidreport',
        'droidsample',
        'droidsql',
        'droidurl',
        'droidutil',
        'droidziprar',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Operating System :: Unix",
        "Topic :: Software Development :: Disassemblers",
    ],
    include_package_data=True,
    install_requires=[ 'python-magic', 'SQLAlchemy', 'rarfile', 'androguard' ],
    scripts = [ 'droidlysis' ],
)
