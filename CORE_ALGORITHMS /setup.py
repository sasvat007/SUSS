"""
Setup configuration for CapitalSense Financial State Engine.
"""

from setuptools import setup, find_packages

setup(
    name="financial-state-engine",
    version="0.1.0",
    description="Financial modeling system for small business cash flow analysis",
    author="CapitalSense Team",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        # No external dependencies required for core engine
        # Keep it lightweight for maximum portability
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.10",
        ],
        "test": [
            "pytest>=6.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "fse-example=examples:main",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
