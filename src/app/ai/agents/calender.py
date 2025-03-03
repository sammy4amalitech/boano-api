# Create an OpenAI model client.
from datetime import datetime
from typing import List

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from pydantic import BaseModel

from ...core.config import AISettings


class Event(BaseModel):
    title: str
    start_date: str
    end_date: str
    timezone: str

class AgentResponse(BaseModel):
    thoughts: str
    response: List[Event]

model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=AISettings().OPENAI_API_KEY,
    response_format=AgentResponse, # type: ignore
)

class CalendarAgent:
    def __init__(self, calendar_config: dict):
        self.config = calendar_config
        # Set up calendar client here

    async def get_calendar_events(self, username: str) -> dict:
        # Retrieve and process calendar events for the user.
        return {"calendar_events": [{"name": "Meeting", "iso-datetime": "2021-10-01T13:00:00Z"}]}

    assistant = AssistantAgent(
        "calendar",
        model_client=model_client,
        system_message="You are a calendar expert. Provide insights on events from the calendar.",
    )
