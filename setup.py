"""
Setup script for OHB Simulation Model package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="expenditure_forecast",
    version="0.1.0",
    author="Your Organization",
    author_email="email@example.com",
    description="A simulation model for Ontario Health Benefits enrollment and expenditure forecasting",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gc-ohds/expenditure_forecast",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ohb-sim=expenditure_forecast.main:main",
        ],
    },
    include_package_data=True,
)
