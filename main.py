from os import getenv
import openai
import discord
from dotenv import load_dotenv
from collections import defaultdict

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

# Create a dictionary to store conversation history for each channel
conversations = defaultdict(list)
# Create a dictionary to store citations for each channel
citations_dict = defaultdict(list)

MAX_HISTORY = 4 # Maximum number of messages to keep in the history

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
    # ignore messages from the bot itself
    if message.author == client.user:
        return

    await chat(message)


async def send(dm: discord.Message, message: str):
    """
    Send the assistant's response to the channel
    """
    # Send the assistant's response to the channel
    message_parts = [message[i:i+2000] for i in range(0, len(message), 2000)]

    for part in message_parts:
        await dm.channel.send(part)


async def chat(dm: discord.Message):
    text = dm.content

    # If the user's message starts with "/cite", send the corresponding citation
    if text.startswith("/cite"):
        try:
            index = int(text.split(" ", 1)[1])  # Get the index from the user's message
            citation = citations_dict[dm.channel.id][index]  # Get the corresponding citation
            await send(dm, citation)  # Send the citation
            return
        except (IndexError, ValueError):
            await send(dm, "Invalid citation index.")
            return

    # Add the user's message to the conversation history
    conversations[dm.channel.id].append({"role": "user", "content": text})

    # Ensure the conversation history doesn't exceed the maximum number of messages
    conversations[dm.channel.id] = conversations[dm.channel.id][-MAX_HISTORY:]

    thread = openai_client.beta.threads.create(
        messages= [
            {
                "role": message["role"],
                "content": message["content"]
            }
            for message in conversations[dm.channel.id]
        ]
    )


    run = openai_client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
    )

    # Show "typing..." status while fetching response
    async with dm.channel.typing():
        while run.status != "completed":
            run = openai_client.beta.threads.runs.retrieve(
                run_id=run.id,
                thread_id=thread.id,
            )

        messages = openai_client.beta.threads.messages.list(
            thread_id=thread.id
        )

        message = messages.data[0]
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
                citations.append(f'> Zitat: "{file_citation.quote}"\n> Quelle: {cited_file.filename}')
            # elif (file_path := getattr(annotation, 'file_path', None)):
                # cited_file = openai_client.files.retrieve(file_path.file_id)
                # citations.append(f'> Download: [Link]({cited_file.filename})\n')
                # Note: File download functionality not implemented above for brevity

        # Store the citations for this channel
        citations_dict[dm.channel.id] = citations

        # Add the assistant's response to the conversation history
        # conversations[dm.channel.id].append({"role": "assistant", "content": message_content.value})

        await send(dm, message_content.value)

# Run the bot by passing the discord token into the function
client.run(DISCORD_TOKEN)
