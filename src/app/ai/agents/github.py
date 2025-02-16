from datetime import datetime
from typing import List
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from github import Github, Auth
from pydriller import Repository
from src.app.core.config import AISettings

# Create an OpenAI model client.
model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=AISettings().OPENAI_API_KEY,
)

class GitHubAgent:
    def __init__(self, github_token: str, repository: str, agent_name: str = "github"):
        self.github_token = github_token
        self.agent_name = agent_name
        self.repository = repository
        # using an access token
        auth = Auth.Token(self.github_token)

        # First create a Github instance:
        self.g = Github(auth=auth)

        # Initialize the AssistantAgent
        self.assistant = AssistantAgent(
            self.agent_name,
            model_client=model_client,
            tools=[self.get_commits],
            system_message="Use tools to provide insights on commits from repository `sammy4gh/time-tracker-full-stack`.",
        )

    async def get_commits(self, repository: str) -> List[dict]:
        g = self.g
        # Then play with your GitHub objects:
        commits: List[dict] = []

        repo = g.get_repo(repository)
        since_date = datetime.strptime('2021-01-01T00:00:00Z', '%Y-%m-%dT%H:%M:%SZ')
        until_date = datetime.strptime('2025-01-31T23:59:59Z', '%Y-%m-%dT%H:%M:%SZ')
        repo_commits = repo.get_commits(since=since_date, until=until_date)
        for i, commit in enumerate(repo_commits):
            print(i, commit.commit.author.date, commit.commit.author.name, commit.commit.message)
            commits.append({
                'hash': commit.sha,
                'author': commit.commit.author.name,
                'message': commit.commit.message,
                "date": commit.commit.author.date,
            })

        # To close connections after use
        g.close()
        return commits