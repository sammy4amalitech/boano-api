from autogen_agentchat.base import TaskResult
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import ExternalTermination, TextMentionTermination
from github import Auth, Github

from src.app.ai.agents.calender import CalendarAgent
from src.app.ai.agents.github import GitHubAgent
from src.app.core.config import AISettings

# Create an OpenAI model client.
model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=AISettings().OPENAI_API_KEY,
)



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

        self.assistant = AssistantAgent(
            "timelog",
            model_client=model_client,
            system_message="You are a time log expert. Retrieve all timelogs and combine them and return an array of it.  When you are done respond with 'DONE'",
        )

    async def run(self, username: str)-> TaskResult:
        text_termination = TextMentionTermination("DONE")
        team = RoundRobinGroupChat(
            [self.github_agent, self.calendar_agent, self.assistant],
            termination_condition=text_termination
        )
        result = await team.run(task="Give me a json of of all timelogs in format: {title, date, time, person } . " )
        print(result)
        return result

