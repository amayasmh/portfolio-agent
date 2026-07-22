from google.adk.agents import Agent
from .knowledge import SYSTEM_INSTRUCTION
from .tools import get_github_repos



root_agent = Agent(
    name="portfolio_agent",
    model="gemini-3.5-flash-lite", 
    description = "FAQ agent for Amayas MAHMOUDI's portfolio", 
    instruction= SYSTEM_INSTRUCTION,
    tools=[get_github_repos],
)
