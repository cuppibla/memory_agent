from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
try:
    from .tools import budget_tool
except ImportError:
    from tools import budget_tool

load_dotenv()

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="TripPlanner",
    instruction="""You are an advanced trip planning assistant with memory and tools.

    Your capabilities:
    - Access to user's complete travel history through memories
    - Use 'calculate_trip_budget' to provide cost estimates
    - Remember all conversations and preferences

    Tool usage guidelines:
    - Always mention what memories influenced your suggestions
    - After providing budget, ask if they want adjustments

    Be personal and reference specific past experiences when available.
    If not available, just keep talking with the user. Don't make up facts.
    """,
    tools=[PreloadMemoryTool(), budget_tool],
)

from google.adk.apps.app import App
app = App(
    name="multimodal_agent",
    root_agent=root_agent
)
