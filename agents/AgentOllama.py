from agents.Agent import Agent, Message
from ollama import Client
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from errors import AgentException

load_dotenv()
os.environ["NO_PROXY"] = "localhost,127.0.0.1"


class AgentOllama(Agent):
    def __init__(
        self,
        model,
        instructions,
        response_schema=None,
        log_path=None,
        use_context=False,
    ):
        try:
            super().__init__(
                model, instructions, response_schema, log_path, use_context
            )
            host = os.getenv("OLLAMA_HOST", "localhost:11434")
            self.client = Client(host=f"http://{host}")
            self.context = []
        except Exception as e:
            raise AgentException(e)

    def run(self, instruction, prompt, **kwargs) -> str:
        try:
            fmt = self.get_format(instruction)
            if isinstance(fmt, type) and issubclass(fmt, BaseModel):
                fmt = fmt.model_json_schema()
            system_message = Message(
                role="system",
                content=self.instructions["system"][instruction](**kwargs),
                instruction=instruction,
            )
            user_message = Message(
                role="user",
                content=self.instructions["user"][instruction](prompt=prompt, **kwargs),
                instruction=instruction,
            )
            messages = [system_message, user_message]
            self.log(messages)
            if self.use_context:
                messages = self.context + messages
            assistant_message = Message(
                role="assistant",
                content=self.client.chat(
                    model=self.model,
                    messages=messages,
                    format=fmt,
                ).message.content,
                instruction=instruction,
            )
            if self.use_context:
                messages.append(assistant_message)
            self.log([assistant_message])
            return assistant_message["content"]
        except Exception as e:
            raise AgentException(e)

    def flush_context(self):
        self.context = []
