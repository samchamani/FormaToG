from methods.common import Response, get_default_result
from logger import get_logger
from agents.Agent import Agent
import json


def ask(prompt: str, agent: Agent, log_path: str = "", **_) -> Response:
    logger = get_logger(__name__, log_path)
    response = get_default_result()
    response["is_kg_based_answer"] = False

    agent_response = ""
    response["agent_calls"] += 1
    try:
        agent_response = agent.run("answer", prompt)
    except Exception as e:
        logger.error(f"Agent error occured: {e}")
        response["has_err_agent"] = True
        return response

    try:
        parsed_response = json.loads(agent_response)
        response["user_answer"] = parsed_response["user_answer"]
        response["machine_answer"] = parsed_response["machine_answer"]
    except Exception as e:
        logger.error(f"Format error occured: {e}")
        response["has_err_format"] = True

    return response
