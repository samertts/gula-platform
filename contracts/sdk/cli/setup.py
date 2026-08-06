from setuptools import find_packages, setup

setup(
    name="gula-cli",
    version="1.0.0",
    description="GULA Platform CLI — laboratory information management from the terminal",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="GULA Platform Team",
    url="https://github.com/samertts/gula-platform",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "click>=8.1",
        "httpx>=0.25.0",
        "pyyaml>=6.0",
        "rich>=13.0",
    ],
    entry_points={
        "console_scripts": [
            "gula=gula_cli.main:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
)
