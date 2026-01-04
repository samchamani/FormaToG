from typing import Dict, Type
from .Graph import Graph
from .GraphNeo4j import GraphNeo4j
from .GraphWikidata import GraphWikidata

graph_service: Dict[str, Type[Graph]] = {
    "neo4j": GraphNeo4j,
    "wikidata": GraphWikidata,
}
