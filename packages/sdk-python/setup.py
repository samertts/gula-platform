from setuptools import setup, find_packages

setup(
    name="gula-sdk",
    version="1.0.0",
    description="Python client SDK for the GULA Laboratory Platform",
    long_description=open("README.md", encoding="utf-8").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="GULA Platform",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.24.0,<1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-httpx>=0.21",
            "mypy>=1.0",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
)
