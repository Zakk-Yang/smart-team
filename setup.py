from setuptools import setup, find_packages

setup(
    name="smart-team",
    version="0.1.0",
    packages=find_packages(include=["smart_team", "smart_team.*"]),
    install_requires=[
        "openai>=1.0.0",
        "anthropic>=0.7.0",
        "ollama>=0.1.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "typing-extensions>=4.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
        ]
    },
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="A flexible multi-agent framework supporting OpenAI, Anthropic, and Ollama models",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="ai, llm, agents, openai, anthropic, ollama",
    url="https://github.com/yourusername/my-agentic-framework",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
