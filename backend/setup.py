"""
LLMSync Server - E2E Encrypted Conversation Sync Service
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent.parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="llmsync",
    version="0.1.0",
    author="Rahul",
    author_email="",
    description="E2E encrypted LLM conversation sync service",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/4ahul/llmsync",
    project_urls={
        "Documentation": "https://github.com/4ahul/llmsync#readme",
        "Source": "https://github.com/4ahul/llmsync",
        "Bug Tracker": "https://github.com/4ahul/llmsync/issues",
    },
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "sqlalchemy[asyncio]>=2.0.25",
        "asyncpg>=0.29.0",
        "alembic>=1.13.1",
        "pydantic>=2.5.3",
        "pydantic-settings>=2.1.0",
        "redis[hiredis]>=5.0.1",
        "PyNaCl>=1.5.0",
        "cryptography>=42.0.0",
        "python-jose[cryptography]>=3.3.0",
        "python-multipart>=0.0.6",
        "aiosmtplib>=3.0.1",
        "minio>=7.2.3",
        "prometheus-client>=0.19.0",
        "sentry-sdk[fastapi]>=1.40.0",
        "slowapi>=0.1.9",
        "python-json-logger>=2.0.7",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "pytest-asyncio>=0.23.3",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "httpx>=0.26.0",
            "black>=24.1.1",
            "ruff>=0.1.14",
        ],
    },
    entry_points={
        "console_scripts": [
            "llmsync=llmsync.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Topic :: Communications :: Chat",
        "Topic :: Security :: Cryptography",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Framework :: FastAPI",
    ],
    keywords="llm sync encryption e2ee conversations chat ai",
    include_package_data=True,
)
