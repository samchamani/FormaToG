import argparse
from graphs.GraphNeo4j import GraphNeo4j
from agents.AgentGoogle import AgentGoogle
from methods.instructions.formatog import config, schema
import json
from tqdm import tqdm
import time


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--questions",
        type=str,
        help="json file name (without suffix) in /questions to add seed entities to",
        required=True,
    )
    parser.add_argument(
        "--default_seed_entity",
        type=str,
        help="Fills seed entities with this value if no other can be found",
    )

    args = parser.parse_args()

    filename = f"./questions/{args.questions}.json"
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
        if not content:
            content = "[]"
        questions: list = json.loads(content)

    graph = GraphNeo4j()
    default_entity = [graph.get_entities([args.default_seed_entity])[0].uuid]
    agent = AgentGoogle(
        model="gemini-2.5-flash",
        instructions=config,
        log_path="./seed_entity_retrieval.log",
        use_context=True,
        response_schema=schema,
    )

    for q_data in tqdm(questions):
        if q_data.get("seed_entities", None):
            continue
        question = q_data["question"]
        try:
            time.sleep(4)
            queries = json.loads(agent.run("retrieve_queries", question))["queries"]
            entities = graph.find(queries)
            time.sleep(4)
            agent_picks = json.loads(
                agent.run(
                    "pick_seed_entities",
                    question,
                    amount=3,
                    entities=[e.get_label() for e in entities],
                )
            )["seed_entities"]
            entities = [
                entity.uuid for entity in entities if entity.get_label() in agent_picks
            ]
            q_data["seed_entities"] = entities if entities else default_entity
        except Exception as e:
            print(e)
            q_data["seed_entities"] = default_entity
        agent.flush_context()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(json.dumps(questions, ensure_ascii=False, indent=4))
