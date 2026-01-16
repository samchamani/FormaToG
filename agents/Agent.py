from abc import ABC, abstractmethod
from typing import List, TypedDict, Protocol, Any, Literal
from errors import InstructionError
from pydantic import BaseModel, ValidationError
from logger import get_logger
from logging import Handler
import json


class PromptBuilder(Protocol):
    def __call__(self, **kwargs: Any) -> str: ...


class InstructionDict(TypedDict):
    pick_relationships: PromptBuilder
    pick_triplets: PromptBuilder
    reflect: PromptBuilder
    answer: PromptBuilder
    retrieve_queries: PromptBuilder
    pick_seed_entities: PromptBuilder


InstructionKey = Literal[
    "pick_relationships",
    "pick_triplets",
    "reflect",
    "answer",
    "retrieve_queries",
    "pick_seed_entities",
]


class InstructionConfig(TypedDict):
    system: InstructionDict
    user: InstructionDict


ResponseFormat = BaseModel | str | None


class InstructionResponseSchema(TypedDict):
    pick_relationships: ResponseFormat
    pick_triplets: ResponseFormat
    reflect: ResponseFormat
    answer: ResponseFormat
    retrieve_queries: ResponseFormat
    pick_seed_entities: ResponseFormat


class Message(TypedDict):
    role: str
    content: str
    instruction: InstructionKey


class Agent(ABC):
    def __init__(
        self,
        model: str,
        instructions: InstructionConfig,
        response_schema: InstructionResponseSchema = None,
        log_path: str | Handler = None,
        use_context: bool = False,
    ):
        self.model = model
        self.instructions = instructions
        self.logger = get_logger(__name__, log_path)
        self.use_context = use_context
        self.response_schema = response_schema

    @abstractmethod
    def run(self, instruction: InstructionKey, prompt: str, **kwargs) -> str:
        """Prompts the llm to perform a task based on the instructions defined in
        `self.instructions`
        """
        pass

    @abstractmethod
    def flush_context(self):
        """
        Resets the context of the agent.
        """
        pass

    def log(self, messages: List[Message]):
        for message in messages:
            self.logger.info(json.dumps(message, ensure_ascii=False))

    def get_format(self, instruction: InstructionKey) -> ResponseFormat:
        """Retrieves the corresponding format definition from the `self.schema` dict"""
        return self.response_schema.get(instruction) if self.response_schema else None

    def parse_valid_json(self, response_string, instruction: InstructionKey):
        fmt = self.get_format(instruction)
        if not fmt or isinstance(fmt, str):
            raise Exception("Error: Tried parsing a non-json-string")
        try:
            fmt.model_validate_json(response_string)
            return json.loads(response_string)
        except ValidationError as e:
            InstructionError(
                f"Instruction error for {instruction} -- invalid response: {response_string} -- error: {e}"
            )
