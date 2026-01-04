from graphs.Graph import (
    Graph,
    Entity as AbstractEntity,
    Relationship as AbstractRelationship,
)
from neo4j import GraphDatabase, Transaction
from dotenv import load_dotenv
import os
from typing import Literal, List, Tuple
import graphs.queries.Cypher as queries
import re


class Entity(AbstractEntity):

    def __init__(self, uuid: str, label: str):
        self.uuid = uuid
        self.label = label

    def get_label(self):
        return self.label.replace("\n", " ")


class Relationship(AbstractRelationship):

    def __init__(self, type: str):
        self.type = type

    def get_label(self):
        return self.type


class GraphNeo4j(Graph):

    def __init__(self):
        load_dotenv()
        host = os.getenv("NEO4J_HOST", "localhost")
        user = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        bolt_port = os.getenv("NEO4J_BOLT_PORT", 7687)
        uri = f"bolt://{host}:{bolt_port}"
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """Close the Neo4j driver. Run this after you are done using an instance of this class."""
        if self.driver:
            self.driver.close()

    def run_query(
        self, mode: Literal["read", "write", "admin"], query: str, key=None, **kwargs
    ):
        try:
            with self.driver.session() as session:
                if mode == "admin":
                    return session.run(query, **kwargs).data()
                execute = (
                    session.execute_read if mode == "read" else session.execute_write
                )
                result = execute(self._run_tx, query, key, **kwargs)
                return result
        except Exception as e:
            print(f"Failed to {mode}", e)

    @staticmethod
    def _run_tx(tx: Transaction, query: str, key: str | None, **kwargs):
        results = tx.run(query, **kwargs)

        return [
            record.data() if key is None else record.data()[key] for record in results
        ]

    def format_labels(self, labels: List[str]):
        if not labels:
            return ":NODE"
        result = ""
        for label in labels:
            if self.check_label(label):
                result += ":" + label
        return result

    @staticmethod
    def check_label(label: str) -> bool:
        if not re.match(r"[A-Z][A-Z_]*[A-Z]", label):
            raise ValueError(
                f"Wrong format. Expected '[A-Z][A-Z_]*[A-Z]' but received: {label}"
            )
        return True

    def export_graphml(self, filename: str) -> bool:
        return self.run_query("admin", queries.export_graphml.format(filename=filename))

    def import_graphml(self, filename: str) -> bool:
        return self.run_query("admin", queries.import_graphml.format(filename=filename))

    # ---------------------------------------------------------------------------- #
    #                                    ToG OPS                                   #
    # ---------------------------------------------------------------------------- #

    def get_entities(self, entities, **kwargs) -> List[Entity]:
        if not entities:
            return []
        results = self.run_query(
            "read",
            queries.get_entities,
            data_list=entities,
        )
        return [
            Entity(uuid=result["entity"]["uuid"], label=result["entity"]["label"])
            for result in results
        ]

    def get_relationships(self, entity: Entity, **kwargs) -> List[Relationship]:
        if not entity:
            return []
        results = self.run_query(
            "read", queries.get_relationships.format(uuid=entity.uuid)
        )
        return [Relationship(type=result["relationship"]) for result in results]

    def get_triplets(self, entity: Entity, relationship: Relationship, **kwargs):
        if not entity or not relationship:
            return []
        results = self.run_query(
            "read",
            queries.get_triplets.format(uuid=entity.uuid, rel_type=relationship.type),
        )
        return [
            (
                Entity(uuid=result["head"]["uuid"], label=result["head"]["label"]),
                Relationship(type=result["relationship"]),
                Entity(uuid=result["tail"]["uuid"], label=result["tail"]["label"]),
            )
            for result in results
        ]

    # ---------------------------------------------------------------------------- #
    #                                GRAPH CRUD OPS                                #
    # ---------------------------------------------------------------------------- #

    def create(self, data_list: List[str], **kwargs) -> List[Entity]:
        """Create entities given a `data_list` array of format of labels, each
        representing an entity
        """
        if not data_list:
            return []
        results = self.run_query(
            "write",
            queries.create.format(labels=self.format_labels(kwargs.get("labels"))),
            data_list=data_list,
        )
        return [
            Entity(uuid=result["entity"]["uuid"], label=result["entity"]["label"])
            for result in results
        ]

    def find(self, data_list: List[str], **kwargs) -> List[Entity]:
        """find nodes that contain strings in `data_list`"""
        if not data_list:
            return []
        results = self.run_query(
            "read",
            queries.find.format(labels=self.format_labels(kwargs.get("labels"))),
            data_list=data_list,
        )
        return [
            Entity(uuid=result["entity"]["uuid"], label=result["entity"]["label"])
            for result in results
        ]

    def delete(self, data_list: List[str], **kwargs) -> bool:
        self.run_query("write", queries.delete, data_list=data_list)
        return True

    def link(self, triplets: List[Tuple[str, str, str]], **kwargs):
        """
        can be used to create links or update existing ones
        """
        for triplet in triplets:
            self.check_label(triplet[1])
        return self.run_query("write", queries.link, triplets=triplets)

    def unlink(self, triplet: Tuple[str, str, str], **kwargs):
        return self.run_query(
            "write",
            queries.unlink.format(
                head_uuid=triplet[0],
                rel_type=triplet[1],
                tail_uuid=triplet[2],
            ),
        )
