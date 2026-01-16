from pydantic import BaseModel
from agents.registry import agent_provider
from graphs.registry import graph_service
from methods.instructions.formatog import config as instructions, schema
from typing import List, Literal


class Config(BaseModel):
    agent_provider: Literal["ollama", "google"]
    model: str
    graph_db: Literal["neo4j", "wikidata"]
    max_paths: int
    max_depth: int
    use_context: bool
    seed_entity_ids: List[str]


class ConfigState:

    def __init__(self, config: Config = None):
        self.set(
            config
            if config
            else Config(
                agent_provider="ollama",
                model="llama3.2:3b-instruct-fp16",
                graph_db="neo4j",
                max_paths=3,
                max_depth=3,
                use_context=True,
                seed_entity_ids=["fc381815-5b9e-465f-bd9c-8240724dcb0a"],
            )
        )

    def set(self, config: Config):
        self.agent_provider = config.agent_provider
        self.model = config.model
        self.graph_db = config.graph_db
        self.max_paths = config.max_paths
        self.max_depth = config.max_depth
        self.use_context = config.use_context
        self.seed_entity_ids = config.seed_entity_ids
        self.agent = self.get_agent()
        self.graph = self.get_graph()

    def get(self) -> Config:
        return Config(
            agent_provider=self.agent_provider,
            model=self.model,
            graph_db=self.graph_db,
            max_paths=self.max_paths,
            max_depth=self.max_depth,
            use_context=self.use_context,
            seed_entity_ids=self.seed_entity_ids,
        )

    def get_agent(self):
        AgentFactory = agent_provider[self.agent_provider]
        agent = AgentFactory(
            self.model,
            instructions=instructions,
            response_schema=schema,
            use_context=self.use_context,
            log_path=None,
        )
        if agent.logger.hasHandlers():
            agent.logger.handlers.clear()
        return agent

    def get_graph(self):
        return graph_service[self.graph_db]()
