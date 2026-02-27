import asyncio
import os
import sys
import vertexai
from pathlib import Path

# Add the current directory to sys.path to ensure we can import agent.py
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService
from google.genai import types

from vertexai import types as vertexai_types

ManagedTopicEnum = vertexai_types.ManagedTopicEnum
MemoryTopic = vertexai_types.MemoryBankCustomizationConfigMemoryTopic
CustomMemoryTopic = vertexai_types.MemoryBankCustomizationConfigMemoryTopicCustomMemoryTopic
ManagedMemoryTopic = vertexai_types.MemoryBankCustomizationConfigMemoryTopicManagedMemoryTopic

from agent import root_agent

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("LOCATION", "us-central1")

if not PROJECT_ID:
    raise ValueError("Please set GOOGLE_CLOUD_PROJECT environment variable.")

print(f"Using Project: {PROJECT_ID}, Location: {LOCATION}")

vertexai.init(project=PROJECT_ID, location=LOCATION)
client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

AGENT_NAME = "trip_agent"

# --- Memory Bank Configuration ---
travel_topics = [
    MemoryTopic(
        managed_memory_topic=ManagedMemoryTopic(
            managed_topic_enum=ManagedTopicEnum.USER_PREFERENCES
        )
    ),
    MemoryTopic(
        managed_memory_topic=ManagedMemoryTopic(
            managed_topic_enum=ManagedTopicEnum.USER_PERSONAL_INFO
        )
    ),
    MemoryTopic(
        custom_memory_topic=CustomMemoryTopic(
            label="travel_experiences",
            description="""Memorable travel experiences including:
                - Places visited and impressions
                - Favorite restaurants, cafes, and food experiences
                - Preferred accommodation types and locations
                - Activities enjoyed (museums, hiking, beaches, etc.)
                - Travel companions and social preferences
                - Photos and videos from trips with location context""",
        )
    ),
    MemoryTopic(
        custom_memory_topic=CustomMemoryTopic(
            label="travel_preferences",
            description="""Travel style and preferences:
                - Budget preferences (luxury, mid-range, budget)
                - Transportation preferences (flying, trains, driving)
                - Trip duration preferences
                - Season and weather preferences
                - Cultural interests and language abilities
                - Dietary restrictions and food preferences""",
        )
    ),
    MemoryTopic(
        custom_memory_topic=CustomMemoryTopic(
            label="travel_logistics",
            description="""Practical travel information:
                - Passport and visa information
                - Frequent flyer numbers and hotel loyalty programs
                - Emergency contacts
                - Medical considerations and insurance
                - Packing preferences and essentials
                - Time zone preferences and jet lag strategies""",
        )
    ),
]

memory_bank_config = {
    "customization_configs": [
        {
            "memory_topics": travel_topics,
        }
    ],
    "similarity_search_config": {
        "embedding_model": f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/gemini-embedding-001"
    },
    "generation_config": {
        "model": f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/gemini-2.5-flash"
    },
}

def get_or_create_agent_engine():
    # Check if agent engine exists
    # Note: Listing might be needed if we don't know the ID, but here we try to create and handle conflict if possible,
    # or just create a new one with a unique name if needed.
    # However, the notebook creates it.
    # For simplicity, we'll try to create it. If it fails because it exists, we might need to find it.
    # Actually, the SDK might not error if we just create a new resource?
    # Agent Engine display names are not unique, but we want to reuse if possible?
    # The notebook creates a new one every time? No, it creates one.
    # Let's try to create.
    try:
        print("Creating Agent Engine...")
        agent_engine = client.agent_engines.create(
            config={
                "display_name": AGENT_NAME,
                "context_spec": {
                    "memory_bank_config": memory_bank_config,
                },
            }
        )
        return agent_engine
    except Exception as e:
        print(f"Agent Engine creation might have failed or already exists: {e}")
        # In a real app, we would list and find.
        # For now, let's assume we can proceed or we need to list.
        # Let's try to list and pick the first one with the name.
        print("Listing Agent Engines...")
        engines = client.agent_engines.list()
        for engine in engines:
            if engine.display_name == AGENT_NAME:
                print(f"Found existing Agent Engine: {engine.name}")
                return engine
        raise e

agent_engine = get_or_create_agent_engine()
agent_engine_id = agent_engine.api_resource.name.split("/")[-1]
print(f"Agent Engine ID: {agent_engine_id}")

session_service = VertexAiSessionService(
    project=PROJECT_ID, location=LOCATION, agent_engine_id=agent_engine_id
)
memory_service = VertexAiMemoryBankService(
    project=PROJECT_ID, location=LOCATION, agent_engine_id=agent_engine_id
)

APP_NAME = root_agent.name
runner = Runner(
    app_name=APP_NAME,
    agent=root_agent,
    session_service=session_service,
    memory_service=memory_service,
)

def call_agent(runner: Runner, content: types.Content, session_id: str, user_id: str):
    """Calls the agent and prints the final response."""
    print(f"\n--- User ({user_id}) ---")
    # print(content) # Debug
    
    events = runner.run(user_id=user_id, session_id=session_id, new_message=content)

    final_response = ""
    for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print(f"--- Agent ({runner.agent.name}) ---")
            print(final_response)
            print("-----------------------")
    return final_response

async def test_trip_planner():
    USER_ID = "traveler_123"
    
    # Create Session
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
    print(f"🌍 Starting a new trip planning session: {session.id}")

    # 1. Text
    text_message = types.Content(role="user", parts=[{"text": "Hello!"}])
    call_agent(runner, content=text_message, session_id=session.id, user_id=USER_ID)
    await asyncio.sleep(2)

    # 2. Image
    image_uri = "https://storage.googleapis.com/github-repo/img/gemini/multimodality_usecases_overview/landmark1.jpg"
    mime_type = "image/jpeg"
    image_message = types.Content(
        role="user",
        parts=[
            {
                "text": "I'm planning a trip. First, here is a picture that shows you the kind of place I like."
            },
            {"file_data": {"file_uri": image_uri, "mime_type": mime_type}},
        ],
    )
    call_agent(runner, content=image_message, session_id=session.id, user_id=USER_ID)
    await asyncio.sleep(2)

    # 3. Video
    video_uri = "https://storage.googleapis.com/github-repo/img/gemini/multimodality_usecases_overview/mediterraneansea.mp4"
    mime_type = "video/mp4"
    video_message = types.Content(
        role="user",
        parts=[
            {
                "text": "Next, here's a video. I also enjoy cities close to Mediterranean sea."
            },
            {"file_data": {"file_uri": video_uri, "mime_type": mime_type}},
        ],
    )
    call_agent(runner, content=video_message, session_id=session.id, user_id=USER_ID)
    await asyncio.sleep(2)

    # 4. Audio
    audio_uri = "gs://github-repo/audio_ai/gaeta.wav"
    mime_type = "audio/wav"
    audio_message = types.Content(
        role="user",
        parts=[
            {"text": "Finally, I loved Gaeta. To give you an idea, Here is an audio"},
            {"file_data": {"file_uri": audio_uri, "mime_type": mime_type}},
        ],
    )
    call_agent(runner, content=audio_message, session_id=session.id, user_id=USER_ID)
    await asyncio.sleep(2)

    print("\n---------------------------------------------------")
    print("Conversation finished. Consolidating all memories at once...")
    final_session_state = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=session.id
    )
    await memory_service.add_session_to_memory(final_session_state)
    print("✅ Full conversation context (Image, Video, Audio) saved to Memory Bank.")
    print("---------------------------------------------------")

    # 5. New Session - Recall
    new_session = await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID
    )
    print(
        f"\n🌅 Starting a NEW session ({new_session.id}) to test cumulative memory..."
    )

    text_message = types.Content(role="user", parts=[{"text": "Hello!"}])
    call_agent(runner, content=text_message, session_id=new_session.id, user_id=USER_ID)

    verification_message = types.Content(
        role="user",
        parts=[
            {
                "text": "Based on the picture, video, AND audio I shared with you before, suggest a cultural destination for me."
            }
        ],
    )
    call_agent(runner, content=verification_message, session_id=new_session.id, user_id=USER_ID)

if __name__ == "__main__":
    asyncio.run(test_trip_planner())
