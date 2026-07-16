from setuptools import find_packages, setup

setup(
    name="gula-cli",
    version="2.1.0",
    description="GULA Developer CLI — scaffolding, validation, and platform tooling",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="GULA Platform Team",
    url="https://github.com/samertts/gula-platform",
    packages=find_packages(),
    package_data={"cli": ["templates/*.tpl"]},
    include_package_data=True,
    python_requires=">=3.11",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "gula=cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
)
