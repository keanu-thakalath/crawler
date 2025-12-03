from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Protocol
from abc import ABC, abstractmethod


@dataclass
class FunctionParameter:
    """Represents a function parameter for the chatbot function calling."""
    name: str
    type_: str
    description: str
    required: bool = True


@dataclass
class FunctionDefinition:
    """Represents a function definition for the chatbot function calling."""
    name: str
    description: str
    parameters: List[FunctionParameter]


class FunctionProvider(Protocol):
    """Protocol for objects that can provide function implementations."""
    
    async def list_crawled_sources(self) -> List[tuple[str, str, str, str, str, str]]:
        """List crawled sources with metadata."""
        ...
    
    async def read_sources(self, source_urls: List[str]) -> List[tuple[str, str, str, str]]:
        """Read detailed information from specified sources."""
        ...


class FunctionRegistry:
    """Registry for chatbot functions and their implementations."""
    
    def __init__(self, function_provider: FunctionProvider):
        self.function_provider = function_provider
        self._functions = self._build_function_definitions()
    
    def _build_function_definitions(self) -> Dict[str, FunctionDefinition]:
        """Build the function definitions for LiteLLM function calling."""
        return {
            "list_crawled_sources": FunctionDefinition(
                name="list_crawled_sources",
                description="Get a list of all crawled sources with their metadata. Use this to see what sources are available before asking for detailed information.",
                parameters=[]
            ),
            "read_sources": FunctionDefinition(
                name="read_sources",
                description="Get detailed information (key facts, quotes, and figures) for specific sources. Use this after getting the list of sources to retrieve detailed content.",
                parameters=[
                    FunctionParameter(
                        name="source_urls",
                        type_="array",
                        description="List of source URLs to read detailed information from",
                        required=True
                    )
                ]
            )
        }
    
    def get_function_definitions(self) -> List[FunctionDefinition]:
        """Get all available function definitions."""
        return list(self._functions.values())
    
    def get_openai_tool_schema(self) -> List[Dict[str, Any]]:
        """Convert function definitions to OpenAI tool schema format for LiteLLM."""
        tools = []
        
        for func_def in self._functions.values():
            properties = {}
            required = []
            
            for param in func_def.parameters:
                properties[param.name] = {
                    "type": param.type_,
                    "description": param.description
                }
                if param.required:
                    required.append(param.name)
            
            tool = {
                "type": "function",
                "function": {
                    "name": func_def.name,
                    "description": func_def.description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            }
            tools.append(tool)
        
        return tools
    
    async def call_function(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a registered function with the given arguments."""
        if function_name not in self._functions:
            raise ValueError(f"Unknown function: {function_name}")
        
        if function_name == "list_crawled_sources":
            return await self.function_provider.list_crawled_sources()
        elif function_name == "read_sources":
            source_urls = arguments.get("source_urls", [])
            return await self.function_provider.read_sources(source_urls)
        else:
            raise ValueError(f"Function implementation not found: {function_name}")