from os import getenv
import openai
import discord
from dotenv import load_dotenv

load_dotenv()


DISCORD_TOKEN = getenv("DISCORD_TOKEN")
ASSISTANT_ID = getenv("ASSISTANT_ID")
openai_client = openai.Client(
    api_key=openai.api_key,
)

# Declare our intent with the bot and setting the messeage_content to true
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

PREFIX = ">>"  # set any prefix you want


@client.event
async def on_ready():
    """
    Print a message when the bot is ready
    """
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    """
    Listen to message event
    """
    # ignore messages from the bot itself and messages that don't start with the prefix we have set
    if message.author == client.user or not not message.content.startswith(PREFIX):
        return

    await chat(message)


async def chat(dm: discord.Message):
    text = dm.content

    thread = openai_client.beta.threads.create()

    message = openai_client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=text,
    )
    # This creates a Run in a queued status. You can periodically retrieve the Run to check on its status to see if it has moved to completed.
    run = openai_client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
    )

    # Peridically check the status of the run until it is completed
    while run.status != "completed":
        run = openai_client.beta.threads.runs.retrieve(
            run_id=run.id,
            thread_id=thread.id,
        )
    
    
    # Retrieve the assistant message from the completed run.
    messages = openai_client.beta.threads.messages.list(
        thread_id=thread.id
    )
    print(messages.data[0])
    # SyncCursorPage[ThreadMessage](data=[ThreadMessage(id='msg_NdaZuRQ9V0bEoLXOJ6EbsCRc', assistant_id='asst_DOhy7RappORVrBLMAZz6Ly5A', content=[MessageContentText(text=Text(annotations=[], value='Guten Tag! Wie kann ich Ihnen heute im Bereich des Qualitätsmanagements behilflich sein?'), type='text')], created_at=1699519540, file_ids=[], metadata={}, object='thread.message', role='assistant', run_id='run_Eetxj4sM6BxgvztoJQM3y7FG', thread_id='thread_D0GrpmaCAU64NMQ5zHk9JAQ1'), ThreadMessage(id='msg_YoRprkXrZQDyTnTVR9kGHt1R', assistant_id=None, content=[MessageContentText(text=Text(annotations=[], value='Hallo'), type='text')], created_at=1699519538, file_ids=[], metadata={}, object='thread.message', role='user', run_id=None, thread_id='thread_D0GrpmaCAU64NMQ5zHk9JAQ1')], object='list', first_id='msg_NdaZuRQ9V0bEoLXOJ6EbsCRc', last_id='msg_YoRprkXrZQDyTnTVR9kGHt1R', has_more=False)
    message = messages.data[0]
    # Extract the message content
    message_content = message.content[0].text
    annotations = message_content.annotations
    citations = []  

    # Iterate over the annotations and add footnotes
    for index, annotation in enumerate(annotations):
        # Replace the text with a footnote
        message_content.value = message_content.value.replace(annotation.text, f' [{index}]')
        
        # Gather citations based on annotation attributes
        if (file_citation := getattr(annotation, 'file_citation', None)):
            cited_file = openai_client.files.retrieve(file_citation.file_id)
            citations.append(f'[{index}] {file_citation.quote} from {cited_file.filename}')
        elif (file_path := getattr(annotation, 'file_path', None)):
            cited_file = openai_client.files.retrieve(file_path.file_id)
            citations.append(f'[{index}] Click <here> to download {cited_file.filename}')
            # Note: File download functionality not implemented above for brevity

    # Add footnotes to the end of the message before displaying to user
    message_content.value += '\n' + '\n'.join(citations)

    await dm.channel.send(message_content.value)


# Run the bot by passing the discord token into the function
client.run(DISCORD_TOKEN)
