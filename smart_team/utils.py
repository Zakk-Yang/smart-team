from typing import Callable, Dict, List, Union
from enum import Enum
import inspect


class SchemaFormat(Enum):
    """Supported schema formats for different AI platforms"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    GROK = "grok"
    BASELINE = "baseline"


def _get_type(annotation: type) -> str:
    """Convert Python type to JSON schema type"""
    if annotation == inspect.Parameter.empty:
        return "string"
    elif annotation in (int, float):
        return "number"
    elif annotation == bool:
        return "boolean"
    elif annotation == str:
        return "string"
    elif annotation == list:
        return "array"
    return "string"


def create_function_schema(
    func: Callable, format: Union[str, SchemaFormat] = SchemaFormat.BASELINE
) -> Dict:
    """Create a function schema in the specified format"""
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""

    if format == SchemaFormat.ANTHROPIC:
        # Create schema in Anthropic's tool format
        schema = {
            "name": func.__name__,
            "description": doc,
            "input_schema": {"type": "object", "properties": {}, "required": []},
        }

        for name, param in sig.parameters.items():
            if name == "self":
                continue

            schema["input_schema"]["properties"][name] = {
                "type": _get_type(param.annotation),
                "description": f"Parameter: {name}",
            }

            if param.default == inspect.Parameter.empty:
                schema["input_schema"]["required"].append(name)

        return schema

    elif format == SchemaFormat.OPENAI:
        # Create schema in OpenAI's tool format
        schema = {
            "name": func.__name__,
            "description": doc,
            "parameters": {"type": "object", "properties": {}, "required": []},
        }

        for name, param in sig.parameters.items():
            if name == "self":
                continue

            schema["parameters"]["properties"][name] = {
                "type": _get_type(param.annotation),
                "description": f"Parameter: {name}",
            }

            if param.default == inspect.Parameter.empty:
                schema["parameters"]["required"].append(name)

        return schema

    else:
        # Basic schema for other formats
        schema = {
            "name": func.__name__,
            "description": doc,
            "parameters": {"type": "object", "properties": {}, "required": []},
        }

        for name, param in sig.parameters.items():
            if name == "self":
                continue

            schema["parameters"]["properties"][name] = {
                "type": _get_type(param.annotation),
                "description": f"Parameter: {name}",
            }

            if param.default == inspect.Parameter.empty:
                schema["parameters"]["required"].append(name)

        return schema
