import json
from pydantic import BaseModel, Field
from typing import List, Callable, Dict, Any, Optional
import openai
from dotenv import load_dotenv
import os
import inspect
import logging
from colorama import init, Fore, Style

import datetime
import sys
import os
import subprocess
import tempfile
import venv
from openai import OpenAI


############################################################################################ Define Agent Functions ############################################################################################
def create_virtualenv(env_name: str = "python_env") -> str:
    """
    Creates a Python virtual environment with verbose output.

    Args:
        env_name (str): Name of the virtual environment to create.

    Returns:
        str: A message indicating whether the virtual environment was created successfully.
    """
    try:
        # Check if environment already exists
        if os.path.exists(env_name):
            return f"Virtual environment '{env_name}' already exists."

        # Create the virtual environment
        subprocess.run(
            ["python3", "-m", "venv", env_name],
            check=True,
            capture_output=True,
            text=True,
        )

        # Upgrade pip in the new environment
        if os.name == "nt":  # Windows
            pip_path = os.path.join(os.getcwd(), env_name, "Scripts", "python.exe")
        else:  # Unix/Linux/MacOS
            pip_path = os.path.join(os.getcwd(), env_name, "bin", "python")

        subprocess.run(
            [pip_path, "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
            text=True,
        )

        print(f"Virtual environment '{env_name}' created successfully.")
        return f"Virtual environment '{env_name}' created successfully."

    except subprocess.CalledProcessError as e:
        error_msg = f"Error creating virtual environment: {e.stderr}"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error creating virtual environment: {str(e)}"
        print(error_msg)
        return error_msg


def install_package(env_name: str, package: str) -> str:
    """
    Install a single package in the specified virtual environment.

    Args:
        env_name (str): Name of the virtual environment
        package (str): Name of the package to install

    Returns:
        str: Installation result message
    """
    if not package or not isinstance(package, str):
        raise ValueError(f"Invalid package name: {package}")

    try:
        # Get the absolute path to pip in the virtual environment
        if os.name == "nt":  # Windows
            pip_path = os.path.join(os.getcwd(), env_name, "Scripts", "pip.exe")
        else:  # Unix/Linux/MacOS
            pip_path = os.path.join(os.getcwd(), env_name, "bin", "pip")

        if not os.path.exists(pip_path):
            return f"Error: pip not found in environment {env_name}. Please ensure the environment is created correctly."

        print(f"Installing Python package {package}...")
        
        # Use subprocess.run with full pip path
        result = subprocess.run(
            [pip_path, "install", package.strip()],
            check=True,
            capture_output=True,
            text=True,
        )
        
        if result.returncode == 0:
            print(result.stdout)
            return f"Successfully installed {package}"
        else:
            print(result.stderr)
            return f"Error installing {package}: {result.stderr}"

    except subprocess.CalledProcessError as e:
        error_msg = f"Error installing {package}: {e.stderr}"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error installing {package}: {str(e)}"
        print(error_msg)
        return error_msg


def execute_code(code: str, env_name: str = "python_env") -> tuple[bool, str]:
    """
    Execute the provided Python code in the specified virtual environment.
    Only saves successfully executed code to the permanent storage.

    Args:
        code (str): The Python code to execute
        env_name (str): Name of the virtual environment to use

    Returns:
        tuple[bool, str]: (success status, output/error message)
    """
    # Create a temporary file first
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name

    try:
        # Get the path to the Python interpreter in the virtual environment
        if sys.platform == "win32":
            python_path = os.path.join(env_name, "Scripts", "python.exe")
        else:
            python_path = os.path.join(env_name, "bin", "python")

        # Execute the code file using the virtual environment's Python
        result = subprocess.run(
            [python_path, temp_path], capture_output=True, text=True
        )

        # Save code regardless of exit code for interactive programs
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        code_filename = f"generated_code_{timestamp}.py"

        # Ensure code directory exists
        os.makedirs("code", exist_ok=True)
        permanent_path = os.path.join("code", code_filename)

        # Copy the code to permanent storage
        with open(permanent_path, "w", encoding="utf-8") as f:
            f.write(code)

        print(f"Code saved to {permanent_path}")

        # For interactive programs like games, a non-zero exit code is expected
        # when the user closes the window
        if result.returncode != 0 and "pygame" not in code.lower():
            return (
                False,
                f"Program exited with code {result.returncode}: {result.stderr}",
            )

        return True, result.stdout

    except subprocess.CalledProcessError as e:
        return False, f"Error executing code: {e.stderr}"
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_path)
        except Exception:
            pass  # Ignore cleanup errors


import requests
from bs4 import BeautifulSoup
from googlesearch import search
from typing import Optional, Union
import random

# List of user-agent strings to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
]


def search_and_fetch_content(
    query: str,
    num_results: Union[int, str] = 5,
    use_random_user_agent: Union[bool, str] = True,
) -> str:
    """
    Performs a Google search, retrieves content from the resulting URLs, and concatenates the content with the URLs.
    The result is returned as a single string.

    Args:
        query (str): The search query to use in Google.
        num_results (Union[int, str]): The number of search results to retrieve. If passed as a string, it will be converted to an integer.
        use_random_user_agent (Union[bool, str]): If passed as a string, it will be converted to a boolean.

    Returns:
        str: A single concatenated string containing the URLs and their corresponding content.
    """
    max_tokens = 200
    # Convert num_results to an integer if it's passed as a string
    if isinstance(num_results, str):
        num_results = int(num_results)

    # Convert use_random_user_agent to a boolean if it's passed as a string
    if isinstance(use_random_user_agent, str):
        use_random_user_agent = use_random_user_agent.lower() == "true"

    results = []
    urls_processed = 0
    urls_to_fetch = (
        num_results + 5
    )  # Fetch additional URLs to ensure we get valid results
    urls = search(query, num_results=urls_to_fetch)

    for url in urls:
        if urls_processed >= num_results:
            break

        headers = {}
        if use_random_user_agent:
            user_agent = random.choice(USER_AGENTS)
            headers["User-Agent"] = user_agent

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Extract content from <p> tags
                paragraphs = soup.find_all("p")
                content_list = [para.get_text().strip() for para in paragraphs]

                full_content = "\n".join(content_list)

                if max_tokens is not None:
                    tokens = full_content.split()
                    full_content = " ".join(tokens[:max_tokens])
                # Concatenate the URL with the content
                results.append("URL: " + url + "\nContent:\n" + full_content + "\n")

                urls_processed += 1
            else:
                print(
                    "Failed to retrieve content from "
                    + url
                    + " (Status Code: "
                    + str(response.status_code)
                    + ")"
                )
        except Exception as e:
            print("An error occurred while retrieving " + url + ": " + str(e))

    if len(results) < num_results:
        print(
            "Warning: Only "
            + str(len(results))
            + " results were retrieved out of "
            + str(num_results)
            + " requested."
        )

    # Concatenate all results into a single string
    return "\n".join(results)


import requests


def get_weather(city: str) -> str:
    """
    Retrieves the current temperature for a specified city.

    This function sends a GET request to the wttr.in service to obtain the current temperature
    for the given city and returns it as a formatted string.

    Parameters:
    city (str): The name of the city for which to retrieve the weather information.

    Returns:
    str: A string containing the temperature in the specified city, or an error message if the
         request fails.

    Exceptions:
    - Raises an exception if the HTTP request fails or if the response is invalid.
    """
    url = f"https://wttr.in/{city}?format=%t"
    try:
        if city.strip() == "":
            return "Please provide a city name"
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raise an exception for bad status codes
        temperature = response.text.strip()
        if not temperature:
            return f"No temperature data found for {city}"
        return f"Temperature in {city}: {temperature}"
    except requests.exceptions.RequestException as e:
        return f"Error getting weather for {city}: {str(e)}"
