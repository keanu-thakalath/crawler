from dataclasses import Field
from typing import Any, ClassVar, Protocol, Type, TypeVar

import msgspec
from dotenv import load_dotenv
from litellm import completion, get_supported_openai_params, supports_response_schema

from domain.values import LLMResponseMetadata

from .exceptions import UnsupportedModelError

load_dotenv()


class DataclassProtocol(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]


T = TypeVar("T", bound=DataclassProtocol)


class LiteLLMStructuredCompletion:
    # def __init__(self, model="anthropic/claude-haiku-4-5-20251001"):
    def __init__(self, model="anthropic/claude-sonnet-4-5-20250929"):
        self.model = model

        supported_params = get_supported_openai_params(model=self.model) or []
        has_response_format = "response_format" in supported_params
        has_json_schema = supports_response_schema(model=self.model)

        if not (has_response_format and has_json_schema):
            raise UnsupportedModelError(
                model, "does not support JSON schema response format"
            )

    async def complete(
        self, prompt: str, response_type: Type[T]
    ) -> tuple[T, LLMResponseMetadata]:
        json_schema = msgspec.json.schema(response_type)

        resp = completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={
                "type": "json_schema",
                "json_schema": {"schema": json_schema},
                "strict": True,
            },
        )
        content = msgspec.json.decode(resp.choices[0].message.content)
        try:
            return msgspec.convert(content, response_type), LLMResponseMetadata(
                input_tokens=resp.usage.prompt_tokens,
                output_tokens=resp.usage.completion_tokens,
                prompt=prompt,
                model=self.model,
            )
        except msgspec.ValidationError as e:
            return msgspec.convert(content['$ref'], response_type), LLMResponseMetadata(
                input_tokens=resp.usage.prompt_tokens,
                output_tokens=resp.usage.completion_tokens,
                prompt=prompt,
                model=self.model,
            )