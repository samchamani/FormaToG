from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from server.QueueHandler import QueueHandler
from server.ConfigState import ConfigState, Config
from agents.Agent import Message
from methods.formatog import think_on_graph
from dotenv import load_dotenv
from logger import get_logger
import threading
import queue
import uvicorn
import os
import json

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
logger = get_logger("server")
state = ConfigState()


def task(prompt: str, log_queue: queue.Queue):
    handler = QueueHandler(log_queue)
    logger.info("Connecting queue to agent")
    agent = state.agent
    graph = state.graph
    agent.logger.addHandler(handler)

    logger.info("Starting task")
    kg_extra_calls = 0
    agent_extra_calls = 1
    queries = json.loads(agent.run("retrieve_queries", prompt))["queries"]
    kg_extra_calls += 1
    entities = graph.find(queries)
    agent_extra_calls += 1
    agent_picks = json.loads(
        agent.run(
            "pick_seed_entities",
            prompt,
            amount=state.max_paths,
            entities=[e.get_label() for e in entities],
        )
    )["seed_entities"]
    entities = [entity for entity in entities if entity.get_label() in agent_picks]
    seed_entities = []
    if entities:
        seed_entities = entities
    elif state.default_seed_entity_ids:
        logger.info("No seed entities acquired. Using default entities")
        kg_extra_calls += 1
        seed_entities = graph.get_entities(state.default_seed_entity_ids)

    response = think_on_graph(
        prompt,
        agent,
        graph,
        max_paths=state.max_paths,
        max_depth=state.max_depth,
        seed_entities=seed_entities,
    )
    response["agent_calls"] += agent_extra_calls
    response["kg_calls"] += kg_extra_calls
    agent.logger.removeHandler(handler)
    return json.dumps(
        Message(role="assistant", content=json.dumps(response), instruction="final")
    )


def stream_processor(prompt: str):
    log_queue = queue.Queue()
    result_container = {}

    def worker():
        try:
            result_container["data"] = task(prompt, log_queue)
        except Exception as e:
            logger.error(e)
            result_container["error"] = e
            log_queue.put("")

    t = threading.Thread(target=worker)
    t.start()

    while t.is_alive() or not log_queue.empty():
        try:
            message = log_queue.get(timeout=0.1)
            if result_container.get("error", None):
                yield f"event: error\ndata: {str(result_container["error"])}\n\n"
                yield "data: [DONE]\n\n"
                return
            yield f"data: {message}\n\n"
        except queue.Empty:
            continue

    yield f"data: {result_container.get('data')}\n\n"
    yield "data: [DONE]\n\n"


@app.get("/")
async def hello():
    state.agent.flush_context()
    return True


@app.get("/chat")
async def chat(prompt: str):
    return StreamingResponse(
        stream_processor(prompt),
        media_type="text/event-stream",
        headers={"X-Content-Type-Options": "nosniff"},
    )


@app.get("/config")
async def get_config():
    return state.get()


@app.put("/config")
async def update_config(config: Config):
    state.set(config)
    return state.get()


@app.post("/reset-agent")
async def update_config():
    state.agent.flush_context()
    return True


if __name__ == "__main__":
    host = os.getenv("SERVER_HOST")
    port = int(os.getenv("SERVER_PORT"))
    uvicorn.run(app, host=host, port=port)
