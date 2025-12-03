import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, AsyncGenerator, Optional
from dotenv import load_dotenv
from litellm import acompletion

from .function_registry import FunctionRegistry, FunctionProvider

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Represents a single chat message."""
    role: str  # "user", "assistant", "function"
    content: str
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class ChatResponse:
    """Represents a streaming chat response chunk."""
    content: str = ""
    function_calls: Optional[List[Dict[str, Any]]] = None
    is_complete: bool = False


class ChatbotInterface(ABC):
    """Abstract interface for chatbot implementations."""
    
    @abstractmethod
    async def chat_stream(
        self, 
        messages: List[ChatMessage], 
        function_provider: FunctionProvider
    ) -> AsyncGenerator[ChatResponse, None]:
        """Stream a chat response given the message history."""
        raise NotImplementedError


class LiteLLMChatbot(ChatbotInterface):
    """Chatbot implementation using LiteLLM with function calling support."""
    
    def __init__(self, model: str = "anthropic/claude-haiku-4-5-20251001"):
        self.model = model
    
    async def chat_stream(
        self, 
        messages: List[ChatMessage], 
        function_provider: FunctionProvider
    ) -> AsyncGenerator[ChatResponse, None]:
        """Stream a chat response with function calling support."""
        
        # Set up function registry
        function_registry = FunctionRegistry(function_provider)
        tools = function_registry.get_openai_tool_schema()
        
        logger.info(f"Tools schema: {tools}")
        
        # Convert our messages to LiteLLM format
        litellm_messages = self._convert_messages_to_litellm_format(messages)
        
        # Add system message for context
        system_message = {
            "role": "system",
            "content": """You are a helpful research assistant that can help users explore and analyze scraped web sources. You have access to two functions:

1. `list_crawled_sources()` - Get a list of all available sources with their summaries and metadata
2. `read_sources(source_urls)` - Get detailed facts, quotes, and figures from specific sources

When a user asks about sources, first use `list_crawled_sources()` to see what's available, then use `read_sources()` to get detailed information as needed. Always provide helpful, well-formatted responses that synthesize the information from multiple sources when relevant.

Be conversational and helpful, and make sure to cite specific sources when providing information.

IMPORTANT: Format your responses in PLAIN TEXT only. Do not use markdown formatting, headers (#), bold (**), or other markup. Use simple text with line breaks for structure."""
        }
        
        full_messages = [system_message] + litellm_messages
        
        # Handle multiple rounds of function calls in a loop
        try:
            current_messages = full_messages.copy()
            max_iterations = 5  # Prevent infinite loops
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Always provide tools for Anthropic models
                completion_params = {
                    "model": self.model,
                    "messages": current_messages,
                    "stream": False,
                    "tools": tools,
                    "tool_choice": "auto"
                }
                
                response = await acompletion(**completion_params)
                
                # Check if the model wants to call functions
                if response.choices[0].message.tool_calls:
                    # Handle function calls
                    function_results = []
                    for tool_call in response.choices[0].message.tool_calls:
                        func_name = tool_call.function.name
                        func_args = json.loads(tool_call.function.arguments)
                        
                        try:
                            result = await function_registry.call_function(func_name, func_args)
                            function_results.append({
                                "tool_call_id": tool_call.id,
                                "name": func_name,
                                "result": result
                            })
                        except Exception as e:
                            logger.error(f"Function call error for {func_name}: {e}")
                            function_results.append({
                                "tool_call_id": tool_call.id,
                                "name": func_name,
                                "result": f"Error: {str(e)}"
                            })
                    
                    # Add the assistant's function call message
                    current_messages.append({
                        "role": "assistant",
                        "tool_calls": response.choices[0].message.tool_calls
                    })
                    
                    # Add function results
                    for func_result in function_results:
                        current_messages.append({
                            "role": "tool",
                            "tool_call_id": func_result["tool_call_id"],
                            "name": func_result["name"],
                            "content": json.dumps(func_result["result"])
                        })
                    
                    # Continue the loop to potentially handle more function calls
                    continue
                else:
                    # No more function calls, get the final response with streaming
                    final_completion_params = {
                        "model": self.model,
                        "messages": current_messages,
                        "stream": True,
                        "tools": tools,
                        "tool_choice": "auto"
                    }
                    
                    final_response = await acompletion(**final_completion_params)
                    
                    # Stream the response directly without post-processing
                    async for chunk in final_response:
                        if chunk.choices[0].delta.content:
                            yield ChatResponse(content=chunk.choices[0].delta.content)
                    yield ChatResponse(is_complete=True)
                    break
            
            # If we've hit max iterations, return what we have
            if iteration >= max_iterations:
                yield ChatResponse(content="I've reached the maximum number of function calls. Please try a simpler request.", is_complete=True)
                
        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            yield ChatResponse(content=f"Sorry, I encountered an error: {str(e)}", is_complete=True)
    
    def _convert_messages_to_litellm_format(self, messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        """Convert our ChatMessage format to LiteLLM message format."""
        litellm_messages = []
        
        for msg in messages:
            litellm_msg = {
                "role": msg.role,
                "content": msg.content
            }
            
            if msg.function_call:
                litellm_msg["function_call"] = msg.function_call
            
            if msg.tool_calls:
                litellm_msg["tool_calls"] = msg.tool_calls
            
            litellm_messages.append(litellm_msg)
        
        return litellm_messages

