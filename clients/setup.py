import os
import re
import subprocess
import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.build_ext import build_ext
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

# The information here can also be placed in setup.cfg - better separation of
# logic and declaration, and simpler if you include description/version in a file.
setup(
    name = "awadb-client",
    version = "0.0.9",
    author = "Vincent",
    author_email = "awadb.vincent@gmail.com",
    description = "Python client for AI Native database AwaDB",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license = "Apache 2.0",
    keywords = ["awadb-client", "python sdk", "vectordb", "AI Native SearchEngine", "RAG"],
    url = "https://github.com/awa-ai/awadb",
    packages = ["awadb_client", "awadb_client.py_idl"],

    python_requires=">=3.3",
)
