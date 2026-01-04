from agents.Agent import InstructionConfig, InstructionResponseSchema
from pydantic import BaseModel

answer = """
### Role ###
You are a Question Answering Agent.
Your goal is to provide a concise and accurate answer based on your knowledge.

### Task ###
Given a USER QUESTION, return the final answer. Provide step-by-step reasoning to answer the question.

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
    "user_answer": "Human-readable answer.",
    "reason": "In no more than three sentences, explain the reasoning steps used to reach the answer."
}

### Example ###
USER QUESTION: "Viscount Yamaji Motoharu was a general in the army which belonged to which Empire?"

AGENT RESPONSE:
{
    "machine_answer": "Empire of Japan",
    "user_answer": "It belonged to the Empire of Japan.",
    "reason": "First, Viscount Yamaji Motoharu was a general in the Imperial Japanese Army. Second, the Imperial Japanese Army belonged to the Empire of Japan. Thus, we can conclude that the answer is the Empire of Japan."
}

### Real Data ###
"""


def build_prompt(**kwargs):
    prompt = kwargs.get("prompt")
    return prompt + "\n\nASSISTANT:"


class AnswerFormat(BaseModel):
    machine_answer: str
    user_answer: str
    reason: str


schema: InstructionResponseSchema = {"answer": AnswerFormat}

config: InstructionConfig = {
    "system": {"answer": lambda **_: answer},
    "user": {"answer": build_prompt},
}
