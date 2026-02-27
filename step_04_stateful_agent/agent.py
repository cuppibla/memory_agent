# --- Define 3 Specialist Activity Agents ---
from dotenv import load_dotenv

from google.adk.agents import LlmAgent, Agent
from google.adk.tools import google_search

load_dotenv()

museum_agent = LlmAgent(
    name="museum_expert",
    model="gemini-2.5-flash",
    instruction="You are a generic museum expert. When asked, suggest ONE famous museum or cultural site in the requested city. Keep it brief.",
)

restaurant_agent = LlmAgent(
    name="restaurant_expert",
    model="gemini-2.5-flash",
    instruction="You are a foodie. When asked, suggest ONE famous local restaurant or dish in the requested city. Keep it brief.",
)

outdoor_agent = LlmAgent(
    name="outdoor_expert",
    model="gemini-2.5-flash",
    instruction="You are an adventure guide. When asked, suggest ONE outdoor activity or park in the requested city. Keep it brief.",
)

print("✅ Specialist agents are ready to plan!")

from typing import Dict, Any, Optional
from google.adk.tools import ToolContext

def save_activity_type_callback(
    tool,
    args: Dict[str, Any],
    tool_context: ToolContext,
    tool_response: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Callback to save the TYPE of activity just planned into the session state.
    """
    # 1. Get the actual agent name.
    if tool.name == "transfer_to_agent":
         agent_name = args.get("agent_name")
    else:
         agent_name = tool.name

    activity_type = "unknown"

    # 2. Determine the type based on which agent was actually used
    if agent_name == "museum_expert":
        activity_type = "CULTURAL"
    elif agent_name == "restaurant_expert":
        activity_type = "FOOD"
    elif agent_name == "outdoor_expert":
        activity_type = "OUTDOOR"

    print(f"\n🔔 [CALLBACK] The planner transferred to '{agent_name}'.")

    # 3. Update the state directly
    tool_context.state["last_activity_type"] = activity_type
    print(f"💾 [STATE UPDATE] 'last_activity_type' is now set to: {activity_type}\n")

    return tool_response

def get_planner_instruction(context: ToolContext) -> str:
    """
    Dynamic instruction that safely retrieves state, defaulting to 'None' if missing.
    """
    # context is likely a ReadonlyContext which wraps the actual context
    # We need to access .state from it.
    
    last_activity = "None"
    if context and hasattr(context, "state") and context.state:
        last_activity = context.state.get("last_activity_type", "None")
    
    return f"""
        You are a Master Trip Planner dedicated to creating varied, balanced itineraries.

        ### CRITICAL STATE INFORMATION
        The last activity type you planned was: {last_activity}
        (If it says 'None', you are free to choose any activity).

        ### YOUR STRICT RULES
        1. You **MUST** delegate every request to one of your 3 specialists. NEVER answer directly.
        2. **VARIETY IS MANDATORY:** You are FORBIDDEN from using the same specialist twice in a row.
           - If last_activity_type is 'CULTURAL' -> `museum_expert` is BANNED for this turn.
           - If last_activity_type is 'FOOD' -> `restaurant_expert` is BANNED for this turn.
           - If last_activity_type is 'OUTDOOR' -> `outdoor_expert` is BANNED for this turn.
        3. If the user asks for something that fits a banned specialist (e.g., asking for a hike when OUTDOOR is banned), you MUST politely refuse and suggest a DIFFERENT available type of activity instead.
        4. **CRITICAL:** You must only transfer to ONE agent at a time. Do NOT attempt to call multiple tools or transfer to multiple agents in a single turn.
    """


root_agent = LlmAgent(
    name="master_trip_planner",
    model="gemini-2.5-flash",
    instruction=get_planner_instruction,
    sub_agents=[museum_agent, restaurant_agent, outdoor_agent],
    after_tool_callback=save_activity_type_callback,
)
print("🎩 The Master Planner is ready.")
