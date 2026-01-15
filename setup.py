from setuptools import setup, find_packages

setup(
    name="tltd",
    version="0.1.0",
    description="A terminal-based todo app with hierarchical tasks",
    author="",
    packages=find_packages(),
    install_requires=[
        "textual>=0.47.0",
    ],
    entry_points={
        "console_scripts": [
            "tltd=src.main:main",
        ],
    },
    python_requires=">=3.8",
)
