from typing import TypedDict, List
from graphs.Graph import Relationship, GraphTriplet


# ---------------------------------------------------------------------------- #
#                                   RESPONSE                                   #
# ---------------------------------------------------------------------------- #
class Response(TypedDict):
    machine_answer: str
    user_answer: str
    is_kg_based_answer: bool
    kg_calls: int
    agent_calls: int
    depth: int
    has_err_agent: bool
    has_err_graph: bool
    has_err_tog: bool
    has_err_instruction: bool
    has_err_other: bool


def get_default_result() -> Response:
    return {
        "machine_answer": "",
        "user_answer": "",
        "depth": 0,
        "is_kg_based_answer": True,
        "agent_calls": 0,
        "kg_calls": 0,
        "has_err_agent": False,
        "has_err_graph": False,
        "has_err_tog": False,
        "has_err_instruction": False,
        "has_err_other": False,
    }


# ---------------------------------------------------------------------------- #
#                                    HELPERS                                   #
# ---------------------------------------------------------------------------- #
def filter_relationships(relationships: List[Relationship]) -> List[Relationship]:
    """From original source"""
    words = [
        " ID",
        " code",
        " number",
        "instance of",
        "website",
        "URL",
        "inception",
        "image",
        " rate",
        " count",
    ]
    useless_relation_list = [
        "category's main topic",
        "topic's main category",
        "stack exchange site",
        "main subject",
        "country of citizenship",
        "commons category",
        "commons gallery",
        "country of origin",
        "country",
        "nationality",
    ]
    filtered = []
    for rel in relationships:
        relStr = rel.get_label()

        if (
            any([relStr.endswith(w) for w in words])
            or "wikidata" in relStr.lower()
            or "wikimedia" in relStr.lower()
            or relStr.lower() in useless_relation_list
        ):
            continue
        filtered.append(rel)
    return filtered


def triplet_to_string(triplet: GraphTriplet):
    return (
        triplet[0].get_label(),
        triplet[1].get_label(),
        triplet[2].get_label(),
    )
