# ---------------------------------------------------------------------------- #
#                                  TOG queries                                 #
# ---------------------------------------------------------------------------- #

get_entities = """
UNWIND $data_list AS data
MATCH (entity { uuid: data })
RETURN entity
"""

get_relationships = """
MATCH (entity {{ uuid: "{uuid}" }})-[rel]-()
WITH DISTINCT type(rel) as relationship
RETURN relationship
"""

get_triplets = """
MATCH (a {{ uuid: "{uuid}" }})-[rel:{rel_type}]-(b)
return startNode(rel) AS head, type(rel) AS relationship, endNode(rel) AS tail
"""

# ---------------------------------------------------------------------------- #
#                                 CRUD QUERIES                                 #
# ---------------------------------------------------------------------------- #
# application generated custom id as per recommandations from docs
# https://neo4j.com/docs/cypher-manual/5/functions/scalar/#functions-elementid

create = """
UNWIND $data_list AS data
MERGE (entity{labels} {{ label: data }}) 
ON CREATE SET entity.uuid = randomUUID()
RETURN DISTINCT entity
"""

find = """
UNWIND $data_list AS data
MATCH (entity{labels})
WHERE ANY(k IN keys(entity) WHERE lower(toString(entity[k])) CONTAINS lower(data))
RETURN DISTINCT entity
"""

delete = """
UNWIND $data_list AS data
MATCH (entity { uuid: data })
DETACH DELETE entity
RETURN entity AS result
"""

link = """
UNWIND $triplets as triplet
WITH triplet[0] AS head, triplet[1] AS rel_type, triplet[2] AS tail
MERGE (a { uuid: head })
MERGE (b { uuid: tail })
WITH a, b, rel_type
CALL apoc.merge.relationship(a, rel_type, {}, {}, b) YIELD rel
RETURN a, rel, b
"""

unlink = """
MATCH (a {{ uuid: "{head_uuid}" }})-[edge:{rel_type}]->(b {{ uuid: "{tail_uuid}" }})
DELETE edge
RETURN edge AS relationship
"""

# ---------------------------------------------------------------------------- #
#                                 IMPORT EXPORT                                #
# ---------------------------------------------------------------------------- #

export_graphml = "CALL apoc.export.graphml.all('{filename}', {{useTypes:true}})"
import_graphml = "CALL apoc.import.graphml('{filename}', {{batchSize: 10000, readLabels: true, useTypes: true, storeNodeIds: false}})"
