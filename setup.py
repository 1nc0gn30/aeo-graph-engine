#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="aeo-graph-engine",
    version="1.0.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
)
