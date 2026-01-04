from agents.Agent import InstructionConfig, InstructionResponseSchema
from pydantic import BaseModel

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

### Examples ###
USER QUESTION: "Viscount Yamaji Motoharu was a general in the army which belonged to which Empire?"

AGENT RESPONSE:
{
    "machine_answer": "Empire of Japan",
    "user_answer": "It belonged to the Empire of Japan."
}

USER QUESTION: "What state is home to the university that is represented in sports by George Washington Colonials men's basketball?"

AGENT RESPONSE:
{
    "machine_answer": "Washington, D.C.",
    "user_answer": "It's the state Washington, D.C."
}

USER QUESTION: "Who lists Pramatha Chaudhuri as an influence and wrote Jana Gana Mana?"

AGENT RESPONSE:
{
    "machine_answer": "Bharoto Bhagyo Bidhata",
    "user_answer": "Bharoto Bhagyo Bidhata."
}


USER QUESTION: "What person born in Siegen influenced the work of Vincent Van Gogh?"

AGENT RESPONSE:
{
    "machine_answer": "Peter Paul Rubens",
    "user_answer": "Peter Paul Rubens was born in Siegen and had an influence on Van Gogh."
}

USER QUESTION: "What is the country close to Russia where Mikheil Saakashvii holds a government position?"

AGENT RESPONSE:
{
    "machine_answer": "Georgia",
    "user_answer": "Georgia meets those criteria."
}

### Real Data ###
"""


def build_prompt(**kwargs):
    prompt = kwargs.get("prompt")
    return prompt + "\n\nASSISTANT:\n"


class AnswerFormat(BaseModel):
    machine_answer: str
    user_answer: str


schema: InstructionResponseSchema = {"answer": AnswerFormat}

config: InstructionConfig = {
    "system": {"answer": lambda **_: answer},
    "user": {"answer": build_prompt},
}
