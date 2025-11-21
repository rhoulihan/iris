"""IRIS setup configuration."""

from setuptools import find_packages, setup

from src.cli.version import __version__

setup(
    name="iris",
    version=__version__,
    description="Intelligent Recommendation and Inference System for Oracle Database",
    author="IRIS Development Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "oracledb>=1.4.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "click>=8.1.0",
        "pyyaml>=6.0.0",
        "pandas>=2.1.0",
        "numpy>=1.24.0",
        "sqlparse>=0.4.4",
        "boto3>=1.29.0",
        "redis>=5.0.0",
        "anthropic>=0.39.0",
        "mlflow>=2.9.0",
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
    ],
    entry_points={
        "console_scripts": [
            "iris=cli.cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
