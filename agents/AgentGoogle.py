from agents.Agent import Agent, Message
from google import generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()


class AgentGoogle(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        self.context = []

    def run(self, instruction, prompt, **kwargs):
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
        model = genai.GenerativeModel(
            model_name=self.model,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                response_mime_type="application/json" if response_format else None,
                response_schema=response_format,
            ),
            system_instruction=system_message["content"],
        )
        chat = model.start_chat(history=self.context if self.use_context else [])
        self.log([system_message, user_message])
        response = Message(
            role="assistant",
            content=chat.send_message(user_message["content"]).text,
            instruction=instruction,
        )
        self.log([response])
        if self.use_context:
            self.context = chat.history
        return response["content"]

    def flush_context(self):
        self.context = []
