from .Graph import (
    Graph,
    Entity as AbstractEntity,
    Relationship as AbstractRelationship,
)
from typing import List, Tuple
import graphs.queries.SPARQL as queries
from SPARQLWrapper import SPARQLWrapper
import os
from dotenv import load_dotenv


class Entity(AbstractEntity):

    def __init__(self, qid: str, value: str):
        self.qid = qid
        self.value = value

    def get_label(self):
        return self.value


class Relationship(AbstractRelationship):

    def __init__(self, pid: str, value: str):
        self.pid = pid
        self.value = value

    def get_label(self):
        return self.value


class GraphWikidata(Graph):

    def __init__(self):
        load_dotenv()
        self.url = os.getenv("GRAPH_URL")
        self.user_agent = os.getenv("GRAPH_USER_AGENT")
        self.sparql = SPARQLWrapper(self.url, agent=self.user_agent)
        self.sparql.setReturnFormat("json")

    def query(self, query: str) -> dict:
        """Executes a SPARQL query string and returns results.
        Results in JSON format by default.
        """
        self.sparql.setQuery(query)
        response = self.sparql.query().convert()
        return response

    def get_entities(self, entities, **kwargs) -> List[Entity]:
        if not entities:
            return []
        response = self.query(
            queries.get_entities.format(qids=" ".join([f"wd:{e}" for e in entities]))
        )
        return [
            Entity(
                qid=self.url2id(entry["entity"]["value"]),
                value=entry["entityLabel"]["value"],
            )
            for entry in response["results"]["bindings"]
        ]

    def get_relationships(self, entity: Entity, **kwargs) -> List[Relationship]:
        response = self.query(queries.get_relationships.format(qid=entity.qid))
        return [
            Relationship(
                pid=self.url2id(entry["prop"]["value"]),
                value=entry["propLabel"]["value"],
            )
            for entry in response["results"]["bindings"]
        ]

    def get_triplets(
        self, entity: Entity, relationship: Relationship, **kwargs
    ) -> List[Tuple[Entity, Relationship, Entity]]:
        response = self.query(
            queries.get_triplets.format(qid=entity.qid, pid=relationship.pid)
        )
        return [
            (
                Entity(
                    qid=self.url2id(entry["head"]["value"]),
                    value=entry["headLabel"]["value"],
                ),
                Relationship(
                    pid=self.url2id(entry["rel"]["value"]),
                    value=entry["relLabel"]["value"],
                ),
                Entity(
                    qid=self.url2id(entry["tail"]["value"]),
                    value=entry["tailLabel"]["value"],
                ),
            )
            for entry in response["results"]["bindings"]
        ]

    def find(self, data_list, **kwargs) -> List[Entity]:
        query_concat = " ".join([f'"{data}"' for data in data_list])
        response = self.query(queries.find.format(queries=query_concat))

        best_matches = {}
        for row in response["results"]["bindings"]:
            search_name = row["searchString"]["value"]
            item_uri = row["entity"]["value"]
            try:
                q_id_string = self.url2id(item_uri)
                q_id_val = int(q_id_string.replace("Q", ""))
            except ValueError:
                continue
            if (
                search_name not in best_matches
                or q_id_val < best_matches[search_name]["id_val"]
            ):
                best_matches[search_name] = {
                    "id_val": q_id_val,
                    "qid": q_id_string,
                    "value": row["entityLabel"]["value"],
                }

        return [
            Entity(qid=row["qid"], value=row["value"]) for row in best_matches.values()
        ]

    @staticmethod
    def url2id(url: str) -> str:
        return url.replace("http://www.wikidata.org/entity/", "")
