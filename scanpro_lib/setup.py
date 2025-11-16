import os
import platform
import shutil
import subprocess
import sys

from setuptools import find_packages, setup
from setuptools.command.build_ext import build_ext

PY_MODULE_NAME = "scanpro_lib"

setup(
    name=PY_MODULE_NAME,
    version="0.0.0",
    packages=find_packages(),  # Find all packages in current directory
    package_dir={"": "."},  # Packages are in the current directory
    include_package_data=True,  # Include package data files
    description="ScanPro Library",
)
