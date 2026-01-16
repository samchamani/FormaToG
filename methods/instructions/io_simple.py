from agents.Agent import InstructionConfig

answer = """
### Role ###
You are a Question Answering Agent.
Your goal is to provide a concise and accurate answer based on your knowledge.

### Task ###
Given a USER QUESTION, return the final answer.

### Strict Constraints ###
1. **Output Format:** Do not include introductory text, markdown commentary, or closing remarks.
2. **Answer Semantics:**
   - Must be a concise, noise-free value suitable for programmatic use.
   - Must never contain uncertainty expressions (e.g., "I don't know", "unknown", "cannot be determined").
   - Must be an empty string if the question cannot be answered.
   - Must be in the same language as the USER QUESTION.

### Real Data ###
"""


def build_prompt(**kwargs):
    prompt = kwargs.get("prompt")
    return f'USER QUESTION: "{prompt}"' + "\n\nASSISTANT:\n"


config: InstructionConfig = {
    "system": {"answer": lambda **_: answer},
    "user": {"answer": build_prompt},
}
