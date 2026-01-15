from agents.Agent import Agent
from graphs.Graph import Graph, Entity, GraphTriplet, GraphTuple
from methods.common import (
    FormatError,
    GraphException,
    InstructionError,
    Response,
    get_default_result,
    filter_relationships,
    triplet_to_string,
)
from logger import get_logger
from typing import List, Tuple, Set
import json
from logging import Logger


def think_on_graph(
    prompt: str,
    agent: Agent,
    graph: Graph,
    max_paths: int,
    max_depth: int,
    seed_entities: List[Entity] = None,
    log_path: str = "",
    **_,
):
    """An adjusted version of **think on graph**, where pruning is only done at most once
    for each exploration step in each iteration. This version also uses the advantage
    of structured output (json) of language model agents.
    """

    logger = get_logger(__name__, log_path)
    response = get_default_result()
    try:
        if not len(seed_entities):
            raise GraphException("No seed entities given.")

        collected_triplets: Set[Tuple[str, str, str]] = set()
        current_entities: List[Entity] = seed_entities[:max_paths]
        logger.info(
            f"Paths initialized with {len(current_entities)} empty paths and seed entities: {[e.get_label() for e in current_entities]}"
        )

        for iteration in range(max_depth):
            current_iteration = iteration + 1
            logger.info(f"Depth {current_iteration}")
            response["depth"] = current_iteration

            # ---------------------------------------------------------------------------- #
            logger.info("Relationship exploration initiated")
            candidate_tuples = relationship_search(
                current_entities, graph, response, logger
            )
            selected_tuples = relationship_prune(
                candidate_tuples, agent, prompt, max_paths, response
            )
            logger.info(
                f"Relationships selected {[f"[{e.get_label()}]-[{r.get_label()}]" for e, r in selected_tuples]}"
            )

            # ---------------------------------------------------------------------------- #
            logger.info("Entity exploration initiated")
            candidate_triplets = entity_search(
                selected_tuples, collected_triplets, graph, response, logger
            )
            selected_triplets = entity_prune(
                candidate_triplets, agent, prompt, max_paths, response
            )
            selected_triplets_str_set = {
                (h.get_label(), r.get_label(), t.get_label())
                for h, r, t in selected_triplets
            }
            logger.info(f"Triplets selected {selected_triplets_str_set}")

            # ---------------------------------------------------------------------------- #
            logger.info("Reasoning over gathered data initiated")
            collected_triplets.update(selected_triplets_str_set)
            remaining_iter = max_depth - current_iteration
            found_answer = reasoning(
                collected_triplets, agent, prompt, remaining_iter, response, logger
            )
            if found_answer:
                return response

            logger.info(
                f"Answering with paths not possible at depth {current_iteration}"
            )
            if current_iteration < max_depth:
                logger.info("Preparing next iteration")
                previous_entities = current_entities.copy()
                current_entities = [
                    get_next_entity(triplet, previous_entities)
                    for triplet in selected_triplets
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

    logger.info("Using only agent knowledge to answer question")
    response["is_kg_based_answer"] = False
    try:
        response["agent_calls"] += 1
        answer = json.loads(agent.run("answer", prompt))
        response["machine_answer"] = answer["machine_answer"]
        response["user_answer"] = answer["user_answer"]
    except Exception as e:
        logger.error(f"Agent error occured {e}")
        response["has_err_agent"] = True
    return response


# ---------------------------------------------------------------------------- #
#                                    TOG OPS                                   #
# ---------------------------------------------------------------------------- #
def relationship_search(
    entities: List[Entity], graph: Graph, response: Response, logger: Logger
):
    """Searches the graph for all unique in and outgoing relationship types of
    the given entities, through which it then generates a list of candidate
    tuples for further processing with the agent.
    """

    candidate_tuples: List[GraphTuple] = []
    checked_entities: Set[str] = set()
    for entity in entities:
        entityStr = entity.get_label()
        if entityStr in checked_entities:
            logger.info(f"Already checked entity {entityStr}")
            continue
        else:
            checked_entities.add(entityStr)
        logger.info(f"Checking entity {entityStr}")
        relationships = []
        response["kg_calls"] += 1
        try:
            relationships = graph.get_relationships(entity)
        except Exception as e:
            raise GraphException("Graph Error occured while searching relationships", e)
        logger.info("Removing unnecessary relationships (meta data etc.)")
        relationships = filter_relationships(relationships)
        candidate_tuples.extend(
            [(entity, relationship) for relationship in relationships]
        )
        logger.info(
            f"Found {len(relationships)} relationships connected to {entityStr}"
        )
    if len(candidate_tuples) == 0:
        raise GraphException("No relationships found", candidate_tuples)
    logger.info(f"Collected a total of {len(candidate_tuples)} candidate relationships")
    return candidate_tuples


def relationship_prune(
    candidate_tuples: List[GraphTuple],
    agent: Agent,
    prompt: str,
    max_paths: int,
    response: Response,
):
    """Prompts agent to choose a number of tuples from the candidate list.
    If the list size is smaller than `max_paths` than the agent will not be
    asked and instead the list is used as it is.
    """

    selected_tuples: List[GraphTuple] = []
    if len(candidate_tuples) <= max_paths:
        selected_tuples = candidate_tuples.copy()
    else:
        response["agent_calls"] += 1
        pick_relationships_response = json.loads(
            agent.run(
                "pick_relationships",
                prompt=prompt,
                relationships=[
                    (entity.get_label(), relationship.get_label())
                    for entity, relationship in candidate_tuples
                ],
                amount=max_paths,
            )
        )
        selected_tuples = map_str_tuples_to_objects(
            pick_relationships_response["selection"][:max_paths],
            candidate_tuples,
        )
    return selected_tuples


def entity_search(
    selected_tuples: List[GraphTuple],
    collected_triplets: Set[Tuple[str, str, str]],
    graph: Graph,
    response: Response,
    logger: Logger,
):
    """Searches the graph for all triplets that contain a selected tuple
    and then generates a list of unique candidate triplets with all triplets
    that have already been collected filtered out.
    Raises a `GraphException`, if the candidate triplet list is empty, because
    this would imply that there is no change of the current state.
    """

    candidate_triplets: List[GraphTriplet] = []
    checked_triplets: Set[Tuple[str, str, str]] = collected_triplets.copy()
    for entity, relationship in selected_tuples:
        entityStr = entity.get_label()
        relStr = relationship.get_label()
        logger.info(f"Searching for triplets containing {entityStr}, {relStr}")
        triplets = []
        response["kg_calls"] += 1
        try:
            triplets = graph.get_triplets(entity, relationship)
        except Exception as e:
            raise GraphException("Graph Error occured while searching triplets", e)
        triplets = [
            triplet
            for triplet in triplets
            if triplet_to_string(triplet) not in checked_triplets
        ]
        candidate_triplets.extend(triplets)
        checked_triplets.update({triplet_to_string(triplet) for triplet in triplets})
        logger.info(
            f"Found {len(triplets)} triplets including tuple [{entityStr}]-[{relStr}]"
        )
    if len(candidate_triplets) == 0:
        raise GraphException(
            "Dead ends only. No new triplets were found", candidate_triplets
        )
    logger.info(f"Collected a total of {len(candidate_triplets)} candidate triplets")
    return candidate_triplets


def entity_prune(
    candidate_triplets: List[GraphTriplet],
    agent: Agent,
    prompt: str,
    max_paths: int,
    response: Response,
):
    """Prompts agent to choose a number of triplets from the candidate list.
    If the list size is smaller than `max_paths` than the agent will not be
    asked and instead the list is used as it is.
    """

    selected_triplets: List[GraphTriplet] = []
    if len(candidate_triplets) <= max_paths:
        selected_triplets = candidate_triplets.copy()
    else:
        response["agent_calls"] += 1
        pick_triplets_response = json.loads(
            agent.run(
                "pick_triplets",
                prompt,
                triplets=[
                    (h.get_label(), r.get_label(), t.get_label())
                    for h, r, t in candidate_triplets
                ],
                amount=max_paths,
            )
        )
        selected_triplets = map_str_triplets_to_objects(
            pick_triplets_response["selection"][:max_paths], candidate_triplets
        )
    return selected_triplets


def reasoning(
    collected_triplets: Set[Tuple[str, str, str]],
    agent: Agent,
    prompt: str,
    remaining_iterations: int,
    response: Response,
    logger: Logger,
):
    """Returns `True` if the agent judges that the question can be answered
    with the gathered triplets and `False` otherwise. In this version of ToG
    the answer is provided in the same step, so if the question can be
    answered the answer will already be in the `response` dict.
    """

    response["agent_calls"] += 1
    reflection = json.loads(
        agent.run(
            "reflect",
            prompt,
            triplets=list(collected_triplets),
            remaining_iterations=remaining_iterations,
        )
    )

    if reflection["found_knowledge"] and reflection["machine_answer"] != "":
        logger.info("Answering with paths")
        response["machine_answer"] = reflection["machine_answer"]
        response["user_answer"] = reflection["user_answer"]
        return True
    return False


# ---------------------------------------------------------------------------- #
#                                    HELPERS                                   #
# ---------------------------------------------------------------------------- #


def map_str_tuples_to_objects(
    tuples_strings: List[Tuple[str, str]],
    tuples_objects: List[GraphTuple],
) -> List[GraphTuple]:
    results = []
    for entity_rel_dict in tuples_strings:
        ent_str = entity_rel_dict["entity"]
        rel_str = entity_rel_dict["relationship"]
        for ent, rel in tuples_objects:
            if ent.get_label() == ent_str and rel.get_label() == rel_str:
                results.append((ent, rel))
                break
    if len(results) != len(tuples_strings):
        raise InstructionError(f"Some tuples could not be found")
    return results


def map_str_triplets_to_objects(
    triplets_strings: List[Tuple[str, str, str]],
    triplets_objects: List[GraphTriplet],
) -> List[GraphTriplet]:
    results = []
    for triplet_dict in triplets_strings:
        head_str = triplet_dict["head"]
        rel_str = triplet_dict["relationship"]
        tail_str = triplet_dict["tail"]
        for head, rel, tail in triplets_objects:
            if (
                head.get_label() == head_str
                and rel.get_label() == rel_str
                and tail.get_label() == tail_str
            ):
                results.append((head, rel, tail))
                break

    if len(results) != len(triplets_strings):
        raise InstructionError(f"Some triplets could not be found")
    return results


def get_next_entity(
    triplet: GraphTriplet, current_entities: List[Entity]
) -> Tuple[int, Entity]:
    """Returns the path index a triplet is supposed to connect to, and the entity that should be used in case of further exploration"""
    head, _, tail = triplet
    head_str = head.get_label()
    tail_str = tail.get_label()
    for index, entity in enumerate(current_entities):
        entity_str = entity.get_label()
        if head_str == entity_str:
            return (index, tail)
        if tail_str == entity_str:
            return (index, head)
    raise GraphException("No path index or follow-up entity found")
