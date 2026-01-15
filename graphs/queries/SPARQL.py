get_triplets = """
SELECT DISTINCT ?head ?headLabel ?rel ?relLabel ?tail ?tailLabel
WHERE {{
  {{
    wd:{qid} wdt:{pid} ?tail .
  }}
  UNION
  {{
    ?head wdt:{pid} wd:{qid} .
  }}

  BIND(wd:{pid} AS ?rel)
  BIND(COALESCE(?head, wd:{qid}) AS ?head)
  BIND(COALESCE(?tail, wd:{qid}) AS ?tail)

  SERVICE wikibase:label {{
    bd:serviceParam wikibase:language "en". 
    ?head rdfs:label ?headLabel .
    ?rel rdfs:label ?relLabel .
    ?tail rdfs:label ?tailLabel .
  }}
}}
"""

get_relationships = """
SELECT DISTINCT ?prop ?propLabel
WHERE {{
  {{ wd:{qid} ?p ?o . }}
  UNION 
  {{ ?o ?p wd:{qid} . }}
  
  FILTER(STRSTARTS(STR(?p), STR(wdt:)))       
  ?prop wikibase:directClaim ?p .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
"""

get_entities = """
SELECT ?entity ?entityLabel 
WHERE {{
  VALUES ?entity {{ {qids} }} 
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
"""


find = """
SELECT DISTINCT ?searchString ?entity ?entityLabel WHERE {{
  VALUES ?searchString {{ {queries} }}
  BIND(STRLANG(?searchString, "en") AS ?lookupLabel)
  ?entity rdfs:label ?lookupLabel .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT 50
"""
