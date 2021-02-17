#!/usr/bin/env python

import importlib.util
import os
from pathlib import Path

from setuptools import find_packages, setup


def read_flowcontrol_version():
    """This reads the version from flowcontrol/version.py without importing parts of
    flowcontrol (which would require some of the dependencies already installed)."""
    # code parts were taken from here https://stackoverflow.com/a/67692

    path2setup = os.path.dirname(__file__)
    version_file = os.path.abspath(os.path.join(path2setup, "flowcontrol", "version.py"))

    spec = importlib.util.spec_from_file_location("version", version_file)
    version = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(version)
    return version.Version.v_short


# see documentation
# https://packaging.python.org/guides/distributing-packages-using-setuptools/

AUTHOR = "crownet development team"
EMAIL = "christina_maria.mayr@hm.edu"

long_description = (
    "flowcontrol is a Python package that provides control strategies for pedestrian flow control"
)

path_to_pkg_requirements = os.path.join(
    Path(__file__).absolute().parent, "requirements.txt"
)

with open(path_to_pkg_requirements, "r") as f:
    install_requires = f.readlines()
install_requires = [req.replace("\n", "") for req in install_requires]

setup(
    name="flowcontrol",
    author=AUTHOR,
    version=read_flowcontrol_version(),
    description="flowcontrol is Python software for analysis of pedestrian flow control",
    long_description=long_description,
    license="MIT",
    url="https://sam-dev.cs.hm.edu/rover/flowcontrol",
    keywords=[
        "crowd management, flow control, information dissemination"
    ],
    author_email=EMAIL,
    packages=find_packages(),
    package_dir={"flowcontrol": "flowcontrol"},
    package_data={"": ["LICENSE"]},
    python_requires=">=3.6",  # uses f-strings
    install_requires=install_requires,
    test_suite="nose.collector",
    tests_require=["nose>=1.3.7,<1.4"],
    # taken from list: https://pypi.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Scientific/Engineering",
    ],
)
