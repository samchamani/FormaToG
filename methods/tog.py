from agents.Agent import Agent
from graphs.Graph import Graph, Entity, Relationship, GraphTriplet
from methods.common import (
    FormatError,
    GraphException,
    InstructionError,
    Response,
    get_default_result,
    filter_relationships,
    triplet_to_string,
)
from logging import Logger
from logger import get_logger
from typing import List
import re
import copy

Path = List[GraphTriplet]


def think_on_graph(
    prompt: str,
    agent: Agent,
    graph: Graph,
    max_paths: int,
    max_depth: int,
    seed_entities: List[Entity] = None,
    log_path: str = "",
    **_,
) -> Response:
    logger = get_logger(__name__, log_path)
    response = get_default_result()
    try:
        if not len(seed_entities):
            raise GraphException("No seed entities given.")
        logger.info(f"Using seed entities {[e.get_label() for e in seed_entities]}")

        paths: List[Path] = [[] for _ in range(max_paths)]
        logger.info(f"Paths initialized with {len(paths)} empty paths")
        current_entities: List[Entity] = seed_entities[:max_paths]

        for iteration in range(max_depth):
            current_iteration = iteration + 1
            logger.info(f"Iteration {current_iteration}")
            response["depth"] = current_iteration

            # ---------------------------------------------------------------------------- #
            logger.info(f"Relationship exploration initiated")
            candidate_relationships = []
            for index, entity in enumerate(current_entities):
                logger.info(f"Checking entity {entity.get_label()} of path {index}")
                relationships = relationship_search(
                    entity, graph, paths[index], response, logger
                )
                parsed_relationship_picks = relationship_prune(
                    entity,
                    relationships,
                    agent,
                    prompt,
                    max_paths,
                    index,
                    response,
                    logger,
                )
                candidate_relationships.extend(parsed_relationship_picks)

            if len(candidate_relationships) == 0:
                raise InstructionError(
                    "No relationships were selected", candidate_relationships
                )
            selected_relationships = sorted(
                candidate_relationships, key=lambda x: x["score"], reverse=True
            )[:max_paths]

            # ---------------------------------------------------------------------------- #
            logger.info(f"Entity exploration initiated")
            candidate_triplets = []
            for entity_relationship in selected_relationships:
                triplets = entity_search(entity_relationship, graph, response, logger)
                parsed_triplet_picks = entity_prune(
                    entity_relationship, triplets, agent, prompt, response, logger
                )
                candidate_triplets.extend(parsed_triplet_picks)

            if len(candidate_triplets) == 0:
                raise InstructionError("No triplets were selected", candidate_triplets)
            selected_triplets = sorted(
                candidate_triplets, key=lambda x: x["score"], reverse=True
            )[:max_paths]

            # ---------------------------------------------------------------------------- #
            path_triplets = update_paths(paths, selected_triplets, logger)
            if reasoning(agent, prompt, path_triplets, response, logger):
                logger.info(f"Can answer with path triplets")
                generate(agent, prompt, path_triplets, response)
                return response

            logger.info(
                f"Answering with paths not possible at depth {current_iteration}"
            )
            current_entities = [
                triplet["scored_entity"] for triplet in selected_triplets
            ]

        # ---------------------------------------------------------------------------- #
        logger.info("Maximum depth reached")
    except GraphException as e:
        response["has_err_graph"] = True
        logger.warning(f"Graph Exception: {e}")
    except FormatError as e:
        response["has_err_format"] = True
        logger.warning(f"Format error: {e}")
    except InstructionError as e:
        response["has_err_instruction"] = True
        logger.warning(f"Instructions were not followed! {e}")
    except Exception as e:
        response["has_err_other"] = True
        logger.error(f"Error occured {e}")

    logger.info("Using only model knowledge to answer question")
    response["is_kg_based_answer"] = False
    try:
        generate(agent, prompt, None, response)
    except InstructionError as e:
        logger.error(f"Instructions were not followed! {e}")
        response["has_err_instruction"] = True
    except Exception as e:
        logger.error(f"Agent error occured {e}")
        response["has_err_agent"] = True
    return response


# ---------------------------------------------------------------------------- #
#                                    TOG OPS                                   #
# ---------------------------------------------------------------------------- #


def relationship_search(
    entity: Entity, graph: Graph, path: Path, response: Response, logger: Logger
):
    response["kg_calls"] += 1
    relationships = []
    try:
        relationships = graph.get_relationships(entity)
    except Exception as e:
        raise GraphException("Graph Error occured while searching relationships", e)
    logger.info("Filtering relationships")
    relationships = filter_relationships(relationships)
    if len(path) > 0:
        relationships = [
            relationship
            for relationship in relationships
            if path[-1][1] != relationship.get_label()
        ]
    logger.info(f"Found {len(relationships)} relationships")
    return relationships


def relationship_prune(
    entity: Entity,
    relationships: List[Relationship],
    agent: Agent,
    prompt: str,
    max_paths: int,
    index: int,
    response: Response,
    logger: Logger,
):
    response["agent_calls"] += 1
    pick_relationships_response = agent.run(
        "pick_relationships",
        prompt,
        relationships=[
            {
                "entity": entity.get_label(),
                "relationships": [rel.get_label() for rel in relationships],
            }
        ],
        amount=max_paths,
    )
    logger.info("parsing agent's pick_relationships response")
    parsed_relationships = []

    try:
        parsed_relationships = parse_response_pick_relationships(
            pick_relationships_response,
            relationships,
            entity,
            path_index=index,
        )
    except InstructionError as e:
        logger.warning(f"Instruction Error while parsing: {e}")
        logger.warning("Continueing despite error.")
        response["has_err_instruction"] = True
    except FormatError as e:
        logger.warning(f"Format Error while parsing: {e}")
        logger.warning("Continueing despite error.")
        response["has_err_format"] = True
    except Exception as e:
        logger.error("Error while parsing.")
        raise Exception("Error while parsing", e)
    return parsed_relationships


def entity_search(
    entity_relationship: dict, graph: Graph, response: Response, logger: Logger
):
    entity: Entity = entity_relationship["entity"]
    entityString = entity.get_label()
    relationship: Relationship = entity_relationship["relationship"]
    response["kg_calls"] += 1
    triplets = []
    try:
        triplets = graph.get_triplets(entity, relationship)
    except Exception as e:
        raise GraphException("Graph Error occured while searching triplets", e)
    logger.info(
        f"Choosing triplets containing {entityString}, {relationship.get_label()}"
    )
    return triplets


def entity_prune(
    entity_relationship: dict,
    triplets: List[GraphTriplet],
    agent: Agent,
    prompt: str,
    response: Response,
    logger: Logger,
):
    response["agent_calls"] += 1
    entity: Entity = entity_relationship["entity"]
    entityString = entity.get_label()
    relationship: Relationship = entity_relationship["relationship"]
    path_index = entity_relationship["path_index"]

    pick_triplets_response = agent.run(
        "pick_triplets",
        prompt,
        triplets=[
            {
                "entity": entityString,
                "relationship": relationship.get_label(),
                "entities": [
                    triplet[0].get_label()
                    for triplet in triplets
                    if triplet[0].get_label() != entityString
                ]
                + [
                    triplet[2].get_label()
                    for triplet in triplets
                    if triplet[2].get_label() != entityString
                ],
            }
        ],
    )

    logger.info("parsing agent's pick_triplets response")
    return parse_response_pick_triplets(
        pick_triplets_response,
        triplets,
        entity,
        relationship,
        path_index,
    )


def update_paths(paths: List[Path], selected_triplets: List[dict], logger: Logger):
    logger.info("updating paths")
    tmp_paths = copy.deepcopy(paths)
    path_triplets = []
    for index, selected_triplet in enumerate(selected_triplets):
        path_index = selected_triplet["path_index"]
        entity = selected_triplet["entity"]
        relationship = selected_triplet["relationship"]
        scored_entity = selected_triplet["scored_entity"]
        is_left_to_right = selected_triplet["is_scored_tail"]

        triplet = (
            (entity, relationship, scored_entity)
            if is_left_to_right
            else (scored_entity, relationship, entity)
        )
        paths[index] = tmp_paths[path_index] + [triplet]
        path_triplets.append(triplet_to_string(triplet))
        logger.info(f"Path {index}: {[triplet_to_string(t) for t in paths[index]]}")
    return path_triplets


def reasoning(
    agent: Agent,
    prompt: str,
    path_triplets: list,
    response: Response,
    logger: Logger,
):
    logger.info("Reflecting if paths can be used for answer")
    response["agent_calls"] += 1
    agenst_response = agent.run("reflect", prompt, triplets=path_triplets)
    return parse_response_reflect(agenst_response)


def generate(agent: Agent, prompt: str, path_triplets: list | None, response: Response):
    response["agent_calls"] += 1
    response["user_answer"] = agent.run("answer", prompt, triplets=path_triplets)
    response["machine_answer"] = parse_response_answer(response["user_answer"])[
        "answer"
    ]


# ---------------------------------------------------------------------------- #
#                                    HELPERS                                   #
# ---------------------------------------------------------------------------- #


def parse_response_pick_relationships(
    response: str, relationships: List[Relationship], entity: Entity, path_index: int
) -> List[dict]:
    """Parsing logic mostly adapted from original code."""
    pattern = r"{\s*(?P<relation>[^()]+)\s+\(Score:\s+(?P<score>[0-9.]+)\)}"
    relations = []
    for match in re.finditer(pattern, response):
        relation = match.group("relation").strip()
        relation = relation.replace("wiki.relation.", "").replace("_", " ")
        if ";" in relation:
            continue
        relation = next(
            (
                relationship
                for relationship in relationships
                if relationship.get_label() == relation
            ),
            None,
        )
        score = match.group("score")
        if not relation or not score:
            raise InstructionError(
                "A relation or score seems to be missing.",
                response,
            )
        try:
            score = float(score)
        except ValueError:
            raise FormatError("Invalid score format", score)
        relations.append(
            {
                "entity": entity,
                "relationship": relation,
                "score": score,
                "path_index": path_index,
            }
        )
    if len(relations) == 0:
        raise InstructionError(
            "No relationships extracted or response format not as instructed."
        )
    return relations


def parse_response_pick_triplets(
    response: str,
    triplets: List[GraphTriplet],
    entity: Entity,
    relationship: Relationship,
    path_index: int,
):
    """Parsing logic mostly adapted from original code."""
    scores = re.findall(r"\d+\.\d+", response)
    scores = [float(number) for number in scores]
    if len(scores) != len(triplets):
        scores = [1 / len(triplets)] * len(triplets)
    entity_string = entity.get_label()
    scored_triplets = []
    rtl_triplet_entities = [
        triplet[0] for triplet in triplets if triplet[0].get_label() != entity_string
    ]
    for index, scored_entity in enumerate(rtl_triplet_entities):
        scored_triplets.append(
            {
                "entity": entity,
                "relationship": relationship,
                "scored_entity": scored_entity,
                "score": scores[index],
                "is_scored_tail": False,
                "path_index": path_index,
            }
        )
    ltr_triplet_entities = [
        triplet[2] for triplet in triplets if triplet[2].get_label() != entity_string
    ]
    for index, scored_entity in enumerate(ltr_triplet_entities):
        scored_triplets.append(
            {
                "entity": entity,
                "relationship": relationship,
                "scored_entity": scored_entity,
                "score": scores[len(rtl_triplet_entities) + index],
                "is_scored_tail": True,
                "path_index": path_index,
            }
        )
    return scored_triplets


def parse_response_reflect(response: str) -> bool:
    yes = re.findall(r"\{([Yy]es)\}", response)
    if len(yes) > 0:
        return True
    no = re.findall(r"\{([Nn]o)\}", response)
    if len(no) > 0:
        return False
    raise InstructionError("No {yes} or {no} included in reflection step.")


def parse_response_answer(response: str) -> dict:
    answers = re.findall(r"\{(.+)\}", response)
    if not answers:
        raise InstructionError("No marked answer found", response)

    return {
        "answer": answers[0].strip(),
        "full_repsonse": response,
    }
