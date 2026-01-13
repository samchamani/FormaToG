import threading
import queue
import logging
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
from methods.formatog import think_on_graph
from methods.instructions.formatog import config, schema
from agents.Agent import Message
from agents.AgentOllama import AgentOllama
from graphs.GraphNeo4j import GraphNeo4j
import json

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueueHandler(logging.Handler):
    def __init__(self, log_queue: queue.Queue, level=0):
        super().__init__(level)
        self.log_queue = log_queue

    def emit(self, record):
        formatted = self.format(record)
        message_start = formatted.find("{")
        self.log_queue.put(f"{formatted[message_start:]}\n")


def task(prompt: str, log_queue: queue.Queue):
    handler = QueueHandler(log_queue)
    print("Initializing graph and agent")
    agent = AgentOllama(
        model="llama3.2:3b-instruct-fp16",
        instructions=config,
        response_schema=schema,
        log_path=handler,
        use_context=True,
    )
    graph = GraphNeo4j()

    print("Starting")
    queries = json.loads(agent.run("retrieve_queries", prompt))["queries"]
    entities = graph.find(queries)
    agent_picks = json.loads(
        agent.run(
            "pick_seed_entities",
            prompt,
            amount=3,
            entities=[e.get_label() for e in entities],
        )
    )["seed_entities"]
    entities = [entity for entity in entities if entity.get_label() in agent_picks]
    seed_entities = (
        entities
        if entities
        else [graph.get_entities(["fc381815-5b9e-465f-bd9c-8240724dcb0a"])[0]]
    )

    response = json.dumps(
        think_on_graph(
            prompt, agent, graph, max_paths=3, max_depth=3, seed_entities=seed_entities
        )
    )
    agent.logger.removeHandler(handler)
    return json.dumps(Message(role="assistant", content=response, instruction="final"))


def stream_processor(prompt: str):
    log_queue = queue.Queue()
    result_container = {}

    def worker():
        result_container["data"] = task(prompt, log_queue)

    t = threading.Thread(target=worker)
    t.start()

    while t.is_alive() or not log_queue.empty():
        try:
            message = log_queue.get(timeout=0.1)
            yield f"data: {message}\n\n"
        except queue.Empty:
            continue

    yield f"data: {result_container.get('data')}\n\n"
    yield "data: [DONE]\n\n"


@app.get("/chat")
async def chat(prompt: str):
    return StreamingResponse(
        stream_processor(prompt),
        media_type="text/event-stream",
        headers={"X-Content-Type-Options": "nosniff"},
    )


if __name__ == "__main__":
    host = os.getenv("SERVER_HOST")
    port = int(os.getenv("SERVER_PORT"))
    uvicorn.run(app, host=host, port=port)
