#!/usr/bin/env python
"""Setup configuration for StorageService"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="storage-service",
    version="0.1.0",
    author="Storage Service Team",
    description="A Python-based media backup service with intelligent directory structure",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.1.0",
        "pyyaml>=6.0",
        "python-dateutil>=2.8.2",
        "tqdm>=4.65.0",
    ],
    entry_points={
        "console_scripts": [
            "storage-service=storage_service.cli:main",
        ],
    },
)
