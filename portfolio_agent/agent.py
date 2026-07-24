import os
from google.adk.agents import Agent
from .knowledge import SYSTEM_INSTRUCTION
from .tools import get_github_repos

def make_agent(model_name: str) -> Agent :

    return Agent(
        name="portfolio_agent",
        model=model_name, 
        description = "FAQ agent for Amayas MAHMOUDI's portfolio", 
        instruction= SYSTEM_INSTRUCTION,
        tools=[get_github_repos],
    )


#on conserve pour le dev
root_agent = make_agent(os.environ.get("MODEL_NAME", 'gemini-3.5-flash-lite'))
