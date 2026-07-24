from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: Literal["mock", "openai_compatible", "minimax", "anthropic"] = "mock"
    data_provider: Literal["mock", "yfinance"] = "mock"
    max_debate_rounds: int = 2
    llm_max_retries: int = 2
    output_dir: Path = Path("outputs")
    data_dir: Path = Path("data")

    minimax_api_key: str = ""
    minimax_base_url: str = "https://api.minimax.io/anthropic"
    minimax_model: str = "MiniMax-M2.1"
    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://api.anthropic.com"
    anthropic_model: str = "claude-sonnet-4-5"
    openai_api_key: str = ""
    openai_base_url: str = "http://localhost:8000/v1"
    openai_model: str = "Qwen3.5-35B-A3B"

