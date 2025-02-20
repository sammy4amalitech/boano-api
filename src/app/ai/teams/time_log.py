import json
import os
from datetime import datetime
from typing import Callable, Optional, Awaitable, Any, List, Literal

import aiofiles
from autogen_agentchat.base import TaskResult
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import ExternalTermination, TextMentionTermination
from github import Auth, Github
from pydantic import BaseModel

from src.app.ai.agents.calender import CalendarAgent
from src.app.ai.agents.github import GitHubAgent
from src.app.core.config import AISettings, AccessTokenSettings

class TimeLog(BaseModel):
    title: str
    date : str
    start_time: str
    end_time: str
    source: Literal["github", "calendar"]

class AgentResponse(BaseModel):
    thoughts: str
    response: List[TimeLog]

tokens = AccessTokenSettings()# Create an OpenAI model client.
model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=AISettings().OPENAI_API_KEY,
    response_format=AgentResponse, # type: ignore
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
    calendar_agent: AssistantAgent,
) -> RoundRobinGroupChat:
    timelog = AssistantAgent(
        "timelog",
        model_client=model_client,
        system_message="""
          You are a time log expert responsible for returning all timelines and combining them into a single array and returning the final result.
          ***Very Important***: 
          - You are responsible for combining all the timelogs from the tools.
          - If some of the timelogs are missing, you should use what timelogs are available.
          - Please provide the timelog in the following format:
              title: str
              date : str
              start_time: datetime
              end_time: datatime
              source: Literal["github", "calendar"]
              eg:
              title: "Meeting with the team"
              date: "2021-10-01"
              start_time: "13:00"
              end_time: "14:00"
              source: "calendar"
          - Add additional information if needed
            thoughts: str
          - The final response should be in the following format:
              response: List[TimeLog]
              thoughts: str
              eg:
              thoughts: "I have combined all the timelogs and here is the final list"
              response: [
                  {
                      title: "Meeting with the team",
                      date: "2021-10-01",
                      start_time: "13:00",
                      end_time: "14:00",
                      source: "calendar"
                  },
                  {
                      title: "Meeting with the team",
                      date: "2021-10-01",
                      start_time: "13:00",
                      end_time: "14:00",
                      source: "github"
                  }
              ]
          - If timelog is empty the response should be be an empty list
          - If there is an error in the input, the response should be an empty list
          - If the user wants to stop the conversation, the response should be an empty list

          """,
    )

    user_proxy = UserProxyAgent(
    name="user",
    input_func=user_input_func,  # Use the user input function.
        description="User input agent"
        )
    team = RoundRobinGroupChat(
    [github_agent, calendar_agent, timelog,user_proxy, ],
    termination_condition=TextMentionTermination("DONE")
        )
    return team

# async def run_timelog_team(
#     user_input_func: Callable[[str, Optional[CancellationToken]], Awaitable[str]],
#     github_agent: AssistantAgent,
#     calendar_agent: AssistantAgent,
#      username: str
#  ) -> TaskResult:
#
#
#
#     team = await get_timelog_team(user_input_func, github_agent, calendar_agent)
#     result = await team.run(task="Give me an array of timelogs .Assume that the person works 8 hours a day and the logs should be calculated to fit the time frame.")
#     print(result)
#     return result

async def get_timelog_history() -> list[dict[str, Any]]:
    """Get chat history from file."""
    if not os.path.exists(timelog_history_path):
        return []
    async with aiofiles.open(timelog_state_path, "r") as file:
        return json.loads(await file.read())

