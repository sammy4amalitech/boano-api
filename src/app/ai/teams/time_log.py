import json
import os
from typing import Callable, Optional, Awaitable, Any

import aiofiles
from autogen_agentchat.base import TaskResult
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import ExternalTermination, TextMentionTermination
from github import Auth, Github

from src.app.ai.agents.calender import CalendarAgent
from src.app.ai.agents.github import GitHubAgent
from src.app.core.config import AISettings, AccessTokenSettings

tokens = AccessTokenSettings()# Create an OpenAI model client.
model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=AISettings().OPENAI_API_KEY,
)

model_config_path = "model_config.yaml"
timelog_state_path = "team_state.json"
timelog_history_path = "team_history.json"

# using an access token
auth = Auth.Token("access_token")

# First create a Github instance:

# Public Web Github
g = Github(auth=auth)


# Create an Autogen team that aggregates the outputs.
class TimeLogTeam:
    def __init__(self, github_agent: AssistantAgent, calendar_agent: AssistantAgent):
        self.github_agent = github_agent
        self.calendar_agent = calendar_agent

        # self.assistant = AssistantAgent(
        #     "timelog",
        #     model_client=model_client,
        #     system_message="You are a time log expert. Retrieve all timelogs and combine them and return an array of it.  When you are done respond with 'DONE'",
        # )

        self.user_proxy = UserProxyAgent(
            name="user",
            input_func=user_input_func,  # Use the user input function.
        )

    async def run(self, username: str)-> TaskResult:
        text_termination = TextMentionTermination("DONE")
        team = RoundRobinGroupChat(
            [self.github_agent, self.calendar_agent, self.user_proxy],
            termination_condition=text_termination
        )
        result = await team.run(task="Give me a json of of all timelogs in format: {title, date, time, person } . " )
        print(result)
        return result





async def get_timelog_team(
    user_input_func: Callable[[str, Optional[CancellationToken]], Awaitable[str]],
    github_agent: AssistantAgent,
    calendar_agent: AssistantAgent
) -> RoundRobinGroupChat:
    user_proxy = UserProxyAgent(
    name="user",
    input_func=user_input_func,  # Use the user input function.
        )
    team = RoundRobinGroupChat(
    [github_agent, calendar_agent, user_proxy],
    termination_condition=TextMentionTermination("DONE")
        )
    return team

async def run_timelog_team(
    user_input_func: Callable[[str, Optional[CancellationToken]], Awaitable[str]],
    github_agent: AssistantAgent,
    calendar_agent: AssistantAgent,
     username: str
 ) -> TaskResult:
    team = await get_timelog_team(user_input_func, github_agent, calendar_agent)
    result = await team.run(task="Give me a json of all timelogs in format: {title, date, time, person}.")
    print(result)
    return result

async def get_timelog_history() -> list[dict[str, Any]]:
    """Get chat history from file."""
    if not os.path.exists(timelog_history_path):
        return []
    async with aiofiles.open(timelog_state_path, "r") as file:
        return json.loads(await file.read())

