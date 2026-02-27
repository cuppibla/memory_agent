from dotenv import load_dotenv
from google.adk.agents import LlmAgent
try:
    from .tools import setup_user_db, save_tool, recall_tool
except ImportError:
    from tools import setup_user_db, save_tool, recall_tool
    
load_dotenv()

# Setup the DB when the agent module is loaded
setup_user_db()

root_agent = LlmAgent(
    name="profile_planner",
    model="gemini-2.5-flash",
    tools=[save_tool, recall_tool],
    instruction="""
    You are a hyper-personalized Master Trip Planner.
    1. RECALL FIRST: Before planning, your first action MUST be to call `recall_user_preferences` to learn about the user.
    2. PERSONALIZE: Use any recalled preferences (like dietary needs) to tailor your suggestions.
    3. LEARN: If a user states a new, long-term preference, your final action MUST be to use `save_user_preferences` to remember it.
    """,
)