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

async def run_sequential_workflow():
    """
    A simplified test function that directly invokes the SequentialAgent.
    """
    # Initialize Session Service
    session_service = InMemorySessionService()
    my_user_id = "adk_adventurer_002"

    # The query contains all the information needed for the entire sequence.
    query = "Find me the best sushi restaurant in Palo Alto, and then tell me how to get there from the downtown Caltrain station."

    print(f"\n{'='*60}\n🗣️  Processing Query: '{query}'\n{'='*60}")
    print(f"🚀 Handing off the entire task to the '{root_agent.name}'...")

    # 1. Create a single session for our sequential agent
    # The session will manage the state (like the 'destination' variable) across the sub-agent calls.
    session = await session_service.create_session(app_name=root_agent.name, user_id=my_user_id)

    # 2. Run the query
    # The SequentialAgent will automatically:
    #   - Call foodie_agent with the query.
    #   - Take its output and save it to the state as `state['destination']`.
    #   - Call transportation_agent, injecting the destination into its prompt.
    #   - Stream the final response from the transportation_agent.
    await run_agent_query(root_agent, query, session, my_user_id, session_service)

    print(f"\n--- ✅ '{root_agent.name}' Workflow Complete ---")


if __name__ == "__main__":
    asyncio.run(run_sequential_workflow())