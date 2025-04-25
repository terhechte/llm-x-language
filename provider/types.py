from dataclasses import dataclass


@dataclass
class ModelInfo:
    name: str
    prompt_pricing: str
    completion_pricing: str
