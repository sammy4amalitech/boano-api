from fastapi import APIRouter

from src.app.ai.agents.calender import CalendarAgent
from src.app.ai.agents.github import GitHubAgent
from src.app.ai.teams.time_log import TimeLogTeam
from src.app.core.config import AccessTokenSettings

router = APIRouter(tags=["timelog"])
tokens = AccessTokenSettings()
@router.get("/timelog")
async def get_timelog():
    github_agent = GitHubAgent(repository="https://github.com/sammy4gh/time-tracker-full-stack.git", github_token=tokens.GITHUB_ACCESS_TOKEN)
    team_result = await TimeLogTeam(github_agent=github_agent.assistant, calendar_agent=CalendarAgent.assistant).run("John Doe")
    timelog = next((msg.content for msg in team_result.messages if msg.source == 'timelog'), None)
    return {"message": timelog}
