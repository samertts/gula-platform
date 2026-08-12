from setuptools import setup, find_packages

setup(
    name="gula-sdk",
    version="1.0.0",
    description="GULA Platform Python SDK — laboratory information management, patient records, and healthcare analytics",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="GULA Platform Team",
    url="https://github.com/samertts/gula-platform",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "httpx>=0.25.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
    ],
    extras_require={
        "cli": ["click>=8.1", "rich>=13.0"],
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
