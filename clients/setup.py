import os
import re
import subprocess
import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.build_ext import build_ext
from setuptools import setup, find_packages


# The information here can also be placed in setup.cfg - better separation of
# logic and declaration, and simpler if you include description/version in a file.
setup(
    name = "awadb-client",
    version = "0.0.1",
    author = "Vincent",
    author_email = "awadb.vincent@gmail.com",
    description = "Python client for AI Native database AwaDB",
    long_description = "Python client for AI Native database AwaDB",
    license = "Apache 2.0",
    keywords = "awadb-client python sdk vectordb",
    url = "https://github.com/awa-ai/awadb",
    packages = find_packages(),

    python_requires=">=3.6",
)
