# setup.py
from setuptools import setup, find_packages

setup(
    name="smart-team",
    version="0.1.0",
    packages=find_packages(include=["smart_team"]),
    install_requires=[
        "pydantic>=1.8",
        # Add other dependencies here
    ],
    # entry_points={
    #     "console_scripts": [
    #         "dynamic_agent=dynamic_agent.main:main",
    #     ],
    # },
    author="Your Name",
    author_email="your.email@example.com",
    description="A dynamic multi-agent orchestration framework for various LLM platforms.",
    url="https://github.com/yourusername/dynamic_agent",
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
