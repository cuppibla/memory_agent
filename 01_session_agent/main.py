import asyncio
import sys
import os

# Add the current directory to sys.path to ensure we can import agent.py
# This handles cases where the script is run from the parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from google.adk.agents import Agent
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import Session, InMemorySessionService
from agent import root_agent as multi_day_agent

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

# --- Scenario 1: Tokyo Trip (Original) ---
async def run_trip_same_session_scenario(session_service: InMemorySessionService, user_id: str):
    print("### 🧠 SCENARIO 1: TOKYO TRIP (Adaptive Memory) ###")

    # Create ONE session that we will reuse for the whole conversation
    trip_session = await session_service.create_session(
        app_name=multi_day_agent.name,
        user_id=user_id
    )
    print(f"Created a single session for our trip: {trip_session.id}")

    # --- Turn 1: The user initiates the trip ---
    query1 = "Hi! I want to plan a 2-day trip to Tokyo. I'm interested in historic sites and sushi."
    print(f"\n🗣️ User (Turn 1): '{query1}'")
    await run_agent_query(multi_day_agent, query1, trip_session, user_id, session_service)

    # --- Turn 2: The user gives FEEDBACK and asks for a CHANGE ---
    # We use the EXACT SAME `trip_session` object!
    query2 = "That sounds pretty good, do you remember what I liked about the food?"
    print(f"\n🗣️ User (Turn 2 - Feedback): '{query2}'")
    await run_agent_query(multi_day_agent, query2, trip_session, user_id, session_service)

# --- Scenario 2: Tokyo Trip (New Destination) ---
async def run_trip_different_session_scenario(session_service: InMemorySessionService, user_id: str):
    print("\n\n### 🗼 SCENARIO 2: TOKYO TRIP (New Destination) ###")

    # Create a NEW session for a different trip
    tokyo_session = await session_service.create_session(
        app_name=multi_day_agent.name,
        user_id=user_id
    )
    print(f"Created a new session for Tokyo trip: {tokyo_session.id}")

    query1 = "Hi! I want to plan a 2-day trip to Tokyo. I'm interested in historic sites and sushi."
    print(f"\n🗣️ User (Turn 1): '{query1}'")
    await run_agent_query(multi_day_agent, query1, tokyo_session, user_id, session_service)

    tokyo_session_2 = await session_service.create_session(
        app_name=multi_day_agent.name,
        user_id=user_id
    )
    query2 = "That sounds pretty good, do you remember what I liked about the food?"
    print(f"\n🗣️ User (Turn 2): '{query2}'")
    await run_agent_query(multi_day_agent, query2, tokyo_session_2, user_id, session_service)

async def main():
    # --- Initialize our Session Service ---
    # This one service will manage all the different sessions.
    session_service = InMemorySessionService()
    my_user_id = "adk_adventurer_001"

    await run_trip_same_session_scenario(session_service, my_user_id)
    await run_trip_different_session_scenario(session_service, my_user_id)

if __name__ == "__main__":
    asyncio.run(main())