from google.adk.agents import Agent
from .knowledge import SYSTEM_INSTRUCTION

root_agent = Agent(
    name="portfolio_agent",
    model="gemini-2.5-flash", 
    description = "FAQ agent for Amayas MAHMOUDI's portfolio", 
    instruction= SYSTEM_INSTRUCTION,
)
