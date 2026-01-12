from setuptools import setup, find_packages

setup(
    name="stockbit-analyzer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "selenium>=4.11.2",
        "beautifulsoup4>=4.12.2",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "stockbit-analyzer=stockbit_analyzer.cli:main",
        ],
    },
) 