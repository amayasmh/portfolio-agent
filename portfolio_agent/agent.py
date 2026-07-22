from google.adk.agents import Agent


root_agent = Agent(
    name="portfolio_agent",
    model="gemini-2.5-flash", 
    description = "FAQ agent for Amayas MAHMOUDI's portfolio", 
    instruction= "You are a helpful assistant. For now, just answer questions politely",
)
