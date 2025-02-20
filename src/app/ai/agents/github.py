from datetime import datetime
from typing import List
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from github import Github, Auth
from pydantic import BaseModel
from pydriller import Repository
from src.app.core.config import AISettings

class Commit(BaseModel):
    hash: str
    message: str
    date: datetime
    author_name: str
class AgentResponse(BaseModel):
    thoughts: str
    response: List[Commit]

# Create an OpenAI model client.
model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=AISettings().OPENAI_API_KEY,
    # response_format=AgentResponse, # type: ignore
)

class GitHubAgent:
    def __init__(self, github_token: str,  agent_name: str = "github"):
        self.github_token = github_token
        self.agent_name = agent_name
        # using an access token
        auth = Auth.Token(self.github_token)

        # First create a Github instance:
        self.g = Github(auth=auth)

        # Initialize the AssistantAgent
        self.assistant = AssistantAgent(
            self.agent_name,
            model_client=model_client,
            tools=[self.get_commits, self.search_repo],
            system_message="Use tools to provide insights on commits from repository.",
        )

    async def get_commits(self, repository: str) -> List[Commit]:
        g = self.g
        # Then play with your GitHub objects:
        commits: List[Commit] = []

        repo = g.get_repo(repository)
        since_date = datetime.strptime('2021-01-01T00:00:00Z', '%Y-%m-%dT%H:%M:%SZ')
        until_date = datetime.strptime('2025-01-31T23:59:59Z', '%Y-%m-%dT%H:%M:%SZ')
        repo_commits = repo.get_commits(since=since_date, until=until_date)
        for i, commit in enumerate(repo_commits):
            print(i, commit.commit.author.date, commit.commit.author.name, commit.commit.message)
            commits.append(Commit(
                hash=commit.sha,
                message=commit.commit.message,
                date=commit.commit.author.date,
                author_name=commit.commit.author.name
            ))

        # To close connections after use
        return commits

    async def search_repo(self, repo_name: str) -> List[str]:
        g = self.g
        repo = g.search_repositories(query=repo_name)
        repo_names = []
        for i, r in enumerate(repo):
            print(i, r.full_name)
            repo_names.append(r.full_name)

        return repo_names