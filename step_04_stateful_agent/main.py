import asyncio
import sys
import os

# Add the current directory to sys.path to ensure we can import agent.py
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from google.adk.agents import Agent
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import Session, InMemorySessionService
from agent import root_agent

# --- A Helper Function to Run Our Agents ---
async def run_agent_query(agent: Agent, query: str, session: Session, user_id: str, session_service: InMemorySessionService, is_router: bool = False):
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

async def run_variety_test():
    print(f"\n{'='*60}\n🗓️ PLANNING A VARIED DAY IN KYOTO 🗓️\n{'='*60}")
    
    session_service = InMemorySessionService()
    my_user_id = "adk_adventurer_004"

    # 1. Create a session and initialize the state to None
    itinerary_session = await session_service.create_session(
        app_name=root_agent.name,
        user_id=my_user_id,
        state={"last_activity_type": "None"} # Initial state
    )

    # --- Turn 1: Morning ---
    query1 = "I'm in Kyoto. Plan a morning activity for me."
    print(f"\n🗣️ TURN 1 (Morning): '{query1}'")
    # Expected: It should likely choose a cultural activity (museum_expert) for Kyoto.
    await run_agent_query(root_agent, query1, itinerary_session, my_user_id, session_service)

    # --- Turn 2: Afternoon ---
    # It just did a museum. It MUST NOT do another one, even if Kyoto is famous for them.
    # It should switch to Food or Outdoor.
    query2 = "Great! Now plan an afternoon activity for me."
    print(f"\n🗣️ TURN 2 (Afternoon - Variety Check): '{query2}'")
    await run_agent_query(root_agent, query2, itinerary_session, my_user_id, session_service)

    print(f"\n{'='*60}\n🏁 PLANNING COMPLETE 🏁\n{'='*60}")

if __name__ == "__main__":
    asyncio.run(run_variety_test())