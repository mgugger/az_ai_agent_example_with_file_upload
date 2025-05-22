from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.ai.projects.models import MessageAttachment
from dotenv import load_dotenv
import os

load_dotenv()

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=os.environ['AI_FOUNDRY_CONN_STR'])

# Use the defined agent ID that has "code_interpreter" capability but without uploaded files
agent = project_client.agents.get_agent(os.environ['AI_AGENT_ID'])

# Create a new thread (or possibly reuse an existing one)
thread = project_client.agents.create_thread(
    body={},
    messages=[],
    tool_resources=[],
    metadata={}
)

# Create a file to attach to the message
file_path = "./data.csv"
uploaded_file = project_client.agents.upload_file(file_path=file_path, purpose="assistants")
attachment = MessageAttachment(
    file_id=uploaded_file.id,
    tools=[{"type": "code_interpreter"}]
)

# Run the agent with a message and the file attachment
message = project_client.agents.create_message(
    thread_id=thread.id,
    role="user",
    content="""Generate me the paid gross loss per country based on the data provided in the data.csv file.""",
    attachments=[attachment]
)

run = project_client.agents.create_and_process_run(
    thread_id=thread.id,
    agent_id=agent.id)
messages = project_client.agents.list_messages(thread_id=thread.id)

# Output the messages and download the chart image if generated
file_ids = []
for msg in messages.data:
    msg_dict = msg.as_dict()
    for content in msg_dict.get("content", []):
        content_type = content.get("type")
        if content.get("type") == "text":
            print(f"Message: {content['text']}")
        elif content_type == "image_file":
            file_id = content["image_file"]["file_id"]
            file_ids.append(file_id)
            # Download the image file using get_file_content
            with open("chart.png", "wb") as f:
                for chunk in project_client.agents.get_file_content(file_id=file_id):
                    f.write(chunk)
            print(f"Chart image saved as chart.png (file_id: {file_id})")

# Delete the thread and files
project_client.agents.delete_file(file_id=uploaded_file.id)
for file_id in file_ids:
    project_client.agents.delete_file(file_id=file_id)
project_client.agents.delete_thread(thread_id=thread.id)