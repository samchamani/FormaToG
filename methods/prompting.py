from methods.common import Response, get_default_result
from errors import AgentException, InstructionError
from logger import get_logger
from agents.Agent import Agent


def ask(prompt: str, agent: Agent, log_path: str = "", **_) -> Response:
    logger = get_logger(__name__, log_path)
    response = get_default_result()
    response["is_kg_based_answer"] = False
    try:
        response["agent_calls"] += 1
        agent_response = agent.run("answer", prompt)
        if agent.response_schema:
            answer = agent.parse_valid_json(agent_response, "answer")
            response["user_answer"] = answer["user_answer"]
            response["machine_answer"] = answer["machine_answer"]
        else:
            response["user_answer"] = agent_response
            response["machine_answer"] = agent_response
    except AgentException as e:
        response["has_err_agent"] = True
        logger.warning(f"Agent Exception: {e}")
    except InstructionError as e:
        response["has_err_instruction"] = True
        logger.warning(f"Instruction Error: {e}")
    except Exception as e:
        response["has_err_other"] = True
        logger.error(f"Unexpected error: {e}")
    return response
