import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to sys.path to ensure we can import agent.py
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from google.adk.agents import Agent
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import Session, DatabaseSessionService
from agent import root_agent

# --- Configuration for Persistent Sessions ---
SESSIONS_DIR = Path(os.path.expanduser("~")) / ".adk_codelab" / "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)
SESSION_DB_FILE = SESSIONS_DIR / "trip_planner.db"
SESSION_URL = f"sqlite:///{SESSION_DB_FILE}"

# --- A Helper Function to Run Our Agents ---
async def run_agent_query(agent: Agent, query: str, session: Session, user_id: str, session_service: DatabaseSessionService, is_router: bool = False):
    """Initializes a runner and executes a query for a given agent and session."""
    print(f"\n🚀 Running query for agent: '{agent.name}' in session: '{session.id}'...")

    runner = Runner(
        agent=agent,
        session_service=session_service,
        app_name=agent.name
    )

    final_response = ""
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=types.Content(parts=[types.Part(text=query)], role="user")
        ):
            if not is_router:
                # Let's see what the agent is thinking!
                # print(f"EVENT: {event}")
                pass
            if event.is_final_response():
                final_response = event.content.parts[0].text
    except Exception as e:
        final_response = f"An error occurred: {e}"

    if not is_router:
        print("\n" + "-"*50)
        print("✅ Final Response:")
        print(final_response)
        print("-"*50 + "\n")

    return final_response

async def main():
    session_service = DatabaseSessionService(db_url=SESSION_URL)
    
    session_id = "my_persistent_trip" # A fixed ID for our trip
    
    # Try to get existing session or create new one
    session = await session_service.get_session(
        app_name=root_agent.name, user_id="user_01", session_id=session_id
    )
    
    if session:
        print(f"Agent: Welcome back! Resuming our trip planning session ({session_id}).")
    else:
        print(f"Agent: Hello! Let's start planning a new trip ({session_id}). Where to?")
        session = await session_service.create_session(
            app_name=root_agent.name, user_id="user_01", session_id=session_id
        )
    
    print(f"--- Persistent Trip Planner ---")
    
    # Example interaction
    query = "I want to go to Paris."
    await run_agent_query(root_agent, query, session, "user_01", session_service)

if __name__ == "__main__":
    asyncio.run(main())