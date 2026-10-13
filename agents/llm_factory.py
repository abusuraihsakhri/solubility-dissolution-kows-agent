"""
Local deterministic mock adapter with regex-based identifier interception.
"""
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Solubility Dissolution Kows Agent"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return f"[{self.system_name} mock]: No model inference or scientific verification was performed. Input preview: {prompt[:60]!r}"


class LLMFactory:
    """Only mock/test mode is implemented; other providers are explicitly rejected."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Solubility Dissolution Kows Agent"):
        prov = str(provider).lower()
        if prov in ["mock", "deterministic", "test"]:
            return MockLLM(system_name)
        raise ValueError(f"Unsupported model provider: {provider!r}. Only 'mock' is implemented.")
