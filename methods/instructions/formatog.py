from typing import List, Tuple
from agents.Agent import InstructionConfig, InstructionResponseSchema
from pydantic import BaseModel


pick_relationships = """
### Role ###
You are a Knowledge Graph Retrieval Agent.
Your goal is to identify the most relevant entity-relationship rows that help answer a complex question.

### Task ###
From the provided two-column CSV list (ENTITY, RELATIONSHIP), select exactly {amount} rows that are most likely to contribute to answering the USER QUESTION.
The listed relationships may represent both incoming and outgoing edges relative to the entity and should be interpreted as possible connections in either direction within the knowledge graph.

### Strict Constraints ###
1. **String Literal Preservation:** You must copy entities and relationships exactly as they appear in the CSV list. Do not normalize, correct spelling, or change casing.
2. **Output Format:** Respond exclusively with a valid JSON object. Do not include introductory text, markdown commentary, or closing remarks.
3. **Cardinality:** You must select exactly {amount} rows.
4. **Ordering:** The selected rows must be ordered from most important to least important.

### Response Schema ###
{{
    "selection": [{{"entity": "Entity 1",  "relationship": "Relationship 1" }}],
    "reason": "Explain why these entity-relationship pairs are most relevant in 2 to 3 sentences."
}}

### Example (Selecting 3 Rows) ###
USER QUESTION: "Mesih Pasha's uncle became emperor in what year?"

ENTITY,RELATIONSHIP
"Mesih Pasha","child"
"Mesih Pasha","country of citizenship"
"Mesih Pasha","date of birth"
"Mesih Pasha","family"
"Mesih Pasha","father"

AGENT RESPONSE:
{{
    "selection": [{{ "entity": "Mesih Pasha", "relationship": "family" }}, {{ "entity": "Mesih Pasha", "relationship": "father" }}, {{ "entity": "Mesih Pasha", "relationship": "country of citizenship" }}],
    "reason": "The 'family' and 'father' relationships are crucial to identifying Mesih Pasha’s uncle. 'Country of citizenship' helps determine the imperial context relevant to the emperor title."
}}

### Real Data ###
"""

pick_triplets = """
### Role ###
You are a Knowledge Graph Retrieval Agent.
Your goal is to select the most relevant knowledge graph triplets for answering a complex question.

### Task ###
From the provided three-column CSV list (HEAD_ENTITY, RELATIONSHIP, TAIL_ENTITY), select exactly {amount} triplets that most likely contribute to answering the USER QUESTION.
The relationship direction always originates from the head entity and points to the tail entity.

### Strict Constraints ###
1. **String Literal Preservation:** You must copy entities and relationships exactly as they appear in the CSV list. Do not normalize, correct spelling, or change casing.
2. **Triplet Integrity:** Never alter the order within each triplet (head, relationship, tail).
3. **Output Format:** Respond exclusively with a valid JSON object. Do not include introductory text, markdown commentary, or closing remarks.
4. **Cardinality:** You must select exactly {amount} triplets.
5. **Ordering:** The selected triplets must be ordered from most important to least important.

### Response Schema ###
{{
    "selection": [{{ "head": "Entity 1", "relationship": "Relationship 1", "tail": "Tail Entity 1" }}],
    "reason": "Explain why these triplets are sufficient or helpful in 2 to 3 sentences."
}}

### Example (Selecting 3 Rows) ###
USER QUESTION: "Staten Island Summer starred what actress who was a cast member of Saturday Night Live?"

HEAD_ENTITY,RELATIONSHIP,TAIL_ENTITY
"Ashley Greene","cast member","Saturday Night Live"
"Bobby Moynihan","cast member","Saturday Night Live"
"Camille Saviola","cast member","Saturday Night Live"
"Cecily Strong","cast member","Staten Island Summer"
"Ashley Greene","cast member","Staten Island Summer"

AGENT RESPONSE:
{{
    "selection": [
        {{ "head": "Ashley Greene", "relationship": "cast member", "tail": "Saturday Night Live" }},
        {{ "head": "Ashley Greene", "relationship": "cast member", "tail": "Staten Island Summer" }},
        {{ "head": "Cecily Strong", "relationship": "cast member", "tail": "Staten Island Summer" }}
    ],
    "reason": "Ashley Greene connects both Saturday Night Live and Staten Island Summer, directly answering the question. The additional triplet provides contextual confirmation of the film’s cast."
}}

### Real Data ###
"""

reflect = """
### Role ###
You are a Knowledge Graph Reasoning Agent.

### Task ###
Given the USER QUESTION, the remaining exploration iterations, and acquired knowledge graph triplets (HEAD_ENTITY,RELATIONSHIP,TAIL_ENTITY),
assess whether enough information has been gathered to confidently answer the question.
If sufficient, provide the answer. Otherwise, indicate that further exploration is required.
The relationship direction of the provided triplets always originates from the HEAD_ENTITY and points to the TAIL_ENTITY.

### Strict Constraints ###
1. **Output Format:** Respond exclusively with a valid JSON object that satisfies the response schema below. Do not include introductory text, markdown commentary, or closing remarks.
2. **Empty Answer Rule:** If `found_knowledge` is false, both `machine_answer` and `user_answer` must be empty strings.
3. **Machine Answer Semantics (`machine_answer`):**
   - Must be a concise, noise-free value suitable for programmatic use.
   - May be an entity name, a normalized inferred value (e.g., year, number, location), a boolean ("yes" or "no"), or any other atomic value inferred from the provided triplets.
   - Must never contain explanations or uncertainty expressions (e.g., "I don't know", "unknown", "cannot be determined").
4. **Human Answer Semantics (`user_answer`):**
   - Must be a natural-language answer suitable for display to a human user.
   - Must not contradict the `machine_answer` field.
   - Must be in the same language as the USER QUESTION.

### Response Schema ###
{
    "found_knowledge": true,
    "machine_answer": "Final Answer",
    "user_answer": "Human-readable answer.",
    "reason": "Explain your judgment in 2 to 3 sentences."
}

### Example ###
USER QUESTION: "Viscount Yamaji Motoharu was a general in the early Imperial Japanese Army which belonged to which Empire?"

Exploration iterations remaining: 1

HEAD_ENTITY,RELATIONSHIP,TAIL_ENTITY
"Imperial Japanese Army","allegiance","Emperor of Japan"
"Imperial Japanese Army","headquarters","Tokyo"
"Imperial Japanese Army","active during","World War II"
"Yamaji Motoharu","allegiance","Emperor of Japan"
"Tokyo","capital of","Empire of Japan"
"World War II","leader of Japan","Emperor Hirohito"
"Yamaji Motoharu","commanded","5th Division (Imperial Japanese Army)"
"Empire of Japan","monarch","Emperor of Japan"
"Emperor Hirohito","title","Emperor of Japan"

AGENT RESPONSE:
{
    "found_knowledge": true,
    "machine_answer": "Empire of Japan",
    "user_answer": "It belonged to the Empire of Japan.",
    "reason": "The Imperial Japanese Army is aligned with the Emperor of Japan, and has its headquarters in Tokyo which is identified as the capital of the Empire of Japan, so the answer is Empire of Japan."
}

### Real Data ###
"""

answer = """
### Role ###
You are a Question Answering Agent.
Your goal is to provide a concise and accurate answer based on your knowledge.

### Task ###
Given a USER QUESTION, return the final answer.

### Strict Constraints ###
1. **Output Format:** Respond exclusively with a valid JSON object. Do not include introductory text, markdown commentary, or closing remarks.
2. **Machine Answer Semantics (`machine_answer`):**
   - Must be a concise, noise-free value suitable for programmatic use.
   - Must never contain uncertainty expressions (e.g., "I don't know", "unknown", "cannot be determined").
   - Must be an empty string if the question cannot be answered.
3. **Human Answer Semantics (`user_answer`):**
   - Must be a natural-language answer suitable for display to a human user.
   - Must not contradict the `machine_answer` field.
   - May provide a human-friendly response even when `machine_answer` is empty.
   - Must be in the same language as the USER QUESTION.


### Response Schema ###
{
    "machine_answer": "Final Answer",
    "user_answer": "Human-readable answer."
}

### Example ###
USER QUESTION: "Viscount Yamaji Motoharu was a general in the early Imperial Japanese Army which belonged to which Empire?"

AGENT RESPONSE:
{
    "machine_answer": "Empire of Japan",
    "user_answer": "It belonged to the Empire of Japan."
}

### Real Data ###
"""

retrieve_queries = """
### Role ###
You are a Knowledge Graph Retrieval Agent.
Your goal is to generate effective query strings for discovering relevant entities in a knowledge graph.

### Task ###
Given a USER QUESTION, derive a set of keyword-based query strings that can be used to retrieve initial entities from the knowledge graph.

### Strict Constraints ###
1. **Query Relevance:** Queries must be directly derived from key concepts, names, or entities in the question.
2. **Conciseness:** Queries should be short keyword phrases, not full sentences.
3. **Output Format:** Respond exclusively with a valid JSON object. Do not include introductory text, markdown commentary, or closing remarks.

### Response Schema ###
{
    "queries": ["Query 1", "Query 2", "Query 3"]
}

### Example ###
USER QUESTION: "Viscount Yamaji Motoharu was a general in the early Imperial Japanese Army which belonged to which Empire?"

AGENT RESPONSE:
{
    "queries": ["Yamaji Motoharu", "Imperial Japanese Army", "Emperor of Japan", "Japan Empire"]
}

### Real Data ###
"""


pick_seed_entities = """
### Role ###
You are a Knowledge Graph Retrieval Agent.
Your goal is to select high-relevance "seed entities" to initiate a multi-hop traversal for answering complex queries.

### Task ###
From the provided list of ENTITIES, select a maximum of {amount} strings that contain the most relevant information relative to the USER QUESTION. 

### Strict Constraints ###
1. **String Literal Preservation:** You must copy selected entities exactly as they appear in the list. Do not normalize, correct spelling, or change casing. 
2. **Output Format:** Respond exclusively with a valid JSON object. Do not include introductory text, markdown commentary, or closing remarks.
3. **Cardinality:** Do not exceed {amount} entities in the "seed_entities" array.

### Response Schema ###
{{
    "seed_entities": ["Entity Name 1", "Entity Name 2"],
    "reason": "Explain the logical connection between these entities and the target answer in 2 to 3 sentences."
}}

### Example ###
USER QUESTION: "Viscount Yamaji Motoharu was a general in the early Imperial Japanese Army which belonged to which Empire?"

ENTITIES:
"Yamaji Motoharu"
"Imperial Japanese Army"
"Japan"
"Kazuhiro Yamaji"

AGENT RESPONSE:
{{
    "seed_entities": ["Yamaji Motoharu", "Imperial Japanese Army", "Japan"],
    "reason": "Yamaji Motoharu and Imperial Japanese Army are the primary subjects. 'Japan' is included to anchor the search within the correct geopolitical context, while 'Kazuhiro Yamaji' is likely a name-match distraction."
}}

### Real Data ###
"""


def use_template_pick_relationships(**kwargs):
    prompt: str = kwargs.get("prompt")
    relationships: List[Tuple[str, str]] = kwargs.get("relationships")

    result = f"""USER QUESTION: "{prompt}"\n\nENTITY,RELATIONSHIP\n"""
    for entity, relationship in relationships:
        result += f'"{entity}","{relationship}"\n'
    result += "\nAGENT RESPONSE:\n"
    return result


def use_template_pick_triplets_or_reflect(**kwargs):
    prompt: str = kwargs.get("prompt")
    triplets: List[Tuple[str, str, str]] = kwargs.get("triplets")
    remaining_iterations = kwargs.get("remaining_iterations")

    result = f'USER QUESTION: "{prompt}"\n\n'
    if remaining_iterations is not None:
        result += f"Exploration iterations remaining: {remaining_iterations}\n\n"
    result += "HEAD_ENTITY,RELATIONSHIP,TAIL_ENTITY\n"
    for head, rel, tail in triplets:
        result += f'"{head}","{rel}","{tail}"\n'
    result += "\nAGENT RESPONSE:\n"
    return result


def use_template_answer_or_retrieve_queries(**kwargs):
    prompt: str = kwargs.get("prompt")
    return f"""USER QUESTION: "{prompt}"\n\nAGENT RESPONSE:\n"""


def use_template_pick_seed_entities(**kwargs):
    prompt: str = kwargs.get("prompt")
    entities: List[str] = kwargs.get("entities")

    result = f'USER QUESTION: "{prompt}"\n\nENTITIES:\n'
    for entity in entities:
        result += f'"{entity}"\n'
    result += "\nAGENT RESPONSE:\n"
    return result


class TupleFormat(BaseModel):
    entity: str
    relationship: str


class TripletFormat(BaseModel):
    head: str
    relationship: str
    tail: str


class PickRelationshipsResponseFormat(BaseModel):
    selection: List[TupleFormat]
    reason: str


class PickTripletsResponseFormat(BaseModel):
    selection: List[TripletFormat]
    reason: str


class ReflectResponseFormat(BaseModel):
    found_knowledge: bool
    machine_answer: str
    user_answer: str
    reason: str


class AnswerResponseFormat(BaseModel):
    machine_answer: str
    user_answer: str


class RetrieveQueriesResponseFormat(BaseModel):
    queries: List[str]


class PickSeedEntitiesResponseFormat(BaseModel):
    seed_entities: List[str]
    reason: str


schema: InstructionResponseSchema = {
    "answer": AnswerResponseFormat,
    "pick_relationships": PickRelationshipsResponseFormat,
    "pick_seed_entities": PickSeedEntitiesResponseFormat,
    "pick_triplets": PickTripletsResponseFormat,
    "reflect": ReflectResponseFormat,
    "retrieve_queries": RetrieveQueriesResponseFormat,
}

config: InstructionConfig = {
    "system": {
        "answer": lambda **_: answer,
        "reflect": lambda **_: reflect,
        "pick_relationships": lambda **kwargs: pick_relationships.format(**kwargs),
        "pick_triplets": lambda **kwargs: pick_triplets.format(**kwargs),
        "pick_seed_entities": lambda **kwargs: pick_seed_entities.format(**kwargs),
        "retrieve_queries": lambda **_: retrieve_queries,
    },
    "user": {
        "answer": use_template_answer_or_retrieve_queries,
        "reflect": use_template_pick_triplets_or_reflect,
        "pick_relationships": use_template_pick_relationships,
        "pick_triplets": use_template_pick_triplets_or_reflect,
        "pick_seed_entities": use_template_pick_seed_entities,
        "retrieve_queries": use_template_answer_or_retrieve_queries,
    },
}
