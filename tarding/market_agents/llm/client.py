from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from market_agents.config import Settings

T = TypeVar("T", bound=BaseModel)


class LLMClient(ABC):
    model_name: str

    @abstractmethod
    def structured(self, system_prompt: str, user_prompt: str, output_schema: type[T]) -> T: ...


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("模型响应中没有 JSON 对象")
    return json.loads(text[start:end + 1])


class OpenAICompatibleClient(LLMClient):
    def __init__(self, api_key: str, base_url: str, model: str, retries: int = 2):
        from openai import OpenAI
        self.client, self.model_name, self.retries = OpenAI(api_key=api_key or "not-needed", base_url=base_url), model, retries

    def structured(self, system_prompt: str, user_prompt: str, output_schema: type[T]) -> T:
        error = None
        for _ in range(self.retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name, temperature=0,
                    messages=[{"role": "system", "content": system_prompt},
                              {"role": "user", "content": user_prompt + "\n仅输出符合此 JSON Schema 的对象：\n" + json.dumps(output_schema.model_json_schema(), ensure_ascii=False)}],
                )
                return output_schema.model_validate(_extract_json(response.choices[0].message.content or ""))
            except Exception as exc:
                error = exc
        raise RuntimeError(f"结构化输出在有限重试后失败: {error}")


class AnthropicClient(LLMClient):
    def __init__(self, api_key: str, base_url: str, model: str, retries: int = 2):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        self.model_name, self.retries = model, retries

    def structured(self, system_prompt: str, user_prompt: str, output_schema: type[T]) -> T:
        error = None
        prompt = user_prompt + "\n仅输出 JSON，Schema：\n" + json.dumps(output_schema.model_json_schema(), ensure_ascii=False)
        for _ in range(self.retries + 1):
            try:
                response = self.client.messages.create(model=self.model_name, max_tokens=4096, temperature=0,
                                                       system=system_prompt, messages=[{"role": "user", "content": prompt}])
                text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
                return output_schema.model_validate(_extract_json(text))
            except Exception as exc:
                error = exc
        raise RuntimeError(f"结构化输出在有限重试后失败: {error}")


def build_llm_client(settings: Settings) -> LLMClient:
    if settings.llm_provider == "mock":
        from .mock import MockLLMClient
        return MockLLMClient()
    if settings.llm_provider == "openai_compatible":
        return OpenAICompatibleClient(settings.openai_api_key, settings.openai_base_url,
                                      settings.openai_model, settings.llm_max_retries)
    if settings.llm_provider == "minimax":
        return AnthropicClient(settings.minimax_api_key, settings.minimax_base_url,
                               settings.minimax_model, settings.llm_max_retries)
    return AnthropicClient(settings.anthropic_api_key, settings.anthropic_base_url,
                           settings.anthropic_model, settings.llm_max_retries)

