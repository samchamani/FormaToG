from abc import ABC, abstractmethod
from typing import List, Tuple


class Entity(ABC):
    """The entity model of the graph."""

    def __init__(self):
        pass

    @abstractmethod
    def get_label(self) -> str:
        pass


class Relationship(ABC):
    """The relationship model of the graph."""

    def __init__(self):
        pass

    @abstractmethod
    def get_label(self) -> str:
        pass


GraphTriplet = Tuple[Entity, Relationship, Entity]
GraphTuple = Tuple[Entity, Relationship]


class Graph(ABC):

    @abstractmethod
    def get_entities(self, entities: List[str], **kwargs) -> List[Entity]:
        """Fetches entities from the graph based on ID"""
        pass

    @abstractmethod
    def get_relationships(self, entity: Entity, **kwargs) -> List[Relationship]:
        """Returns all ingoing and outgoing relationships of a given entity."""
        pass

    @abstractmethod
    def get_triplets(
        self, enitity: Entity, relationship: Relationship, **kwargs
    ) -> List[GraphTriplet]:
        """Returns all triplets containing the given entity and relationship.
        Triplets are returned in the format
        ```
        (head_entity, outgoing_relationship, tail_entity)
        ```.
        """
        pass

    @abstractmethod
    def find(self, data_list: List[str], **kwargs) -> List[Entity]:
        """Attempts to find entities based on query strings. If not applicable
        this can be implemented to return an empty list instead.
        """
        pass
