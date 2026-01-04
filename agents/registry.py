from .Agent import Agent
from .AgentOllama import AgentOllama
from .AgentGoogle import AgentGoogle
from typing import Dict, Type

agent_provider: Dict[str, Type[Agent]] = {
    "ollama": AgentOllama,
    "google": AgentGoogle,
}
