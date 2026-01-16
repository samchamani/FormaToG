from agents.Agent import Agent, Message
from errors import AgentException
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()


class AgentGoogle(Agent):

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
            api_key = os.getenv("GOOGLE_API_KEY")
            self.client = genai.Client(api_key=api_key)
            self.context = []
        except Exception as e:
            raise AgentException(e)

    def run(self, instruction, prompt, **kwargs):
        try:
            response_format = self.get_format(instruction)
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

            config = genai.types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json" if response_format else None,
                response_schema=response_format,
                system_instruction=system_message["content"],
            )
            chat = self.client.chats.create(
                model=self.model,
                config=config,
                history=self.context if self.use_context else [],
            )

            self.log([system_message, user_message])

            response_obj = chat.send_message(user_message["content"])

            response = Message(
                role="assistant",
                content=response_obj.text,
                instruction=instruction,
            )
            self.log([response])

            if self.use_context:
                self.context = chat.get_history()

            return response["content"]
        except Exception as e:
            raise AgentException(e)

    def flush_context(self):
        self.context = []
