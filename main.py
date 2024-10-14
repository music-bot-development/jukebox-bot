import os
import sys
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from getVersion import *
import music_queue
import streaming
from urllib.parse import urlparse
from flask import Flask
from threading import Thread
import ai

# Lade Umgebungsvariablen
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID'))
MAIN_QUEUE = music_queue.queue([], False)
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)
bot.custom_voice_clients = {}  # Initialize the custom_voice_clients attribute
tree = bot.tree

# Flask App erstellen für den HTTP-Server
app = Flask('')

@app.route('/')
def home():
    return "Bot is online!", 200

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# TODO: Die Funktion returned häufig false obwohl die URL stimmt.
def is_url_valid(url: str):
    is_valid = False
    try:
        parsed_url = urlparse(url)
        if "youtube.com" in parsed_url.hostname or "youtu.be" in parsed_url.hostname:
            is_valid = True
        else:
            print("Invalid URL")
    except Exception as e:
        is_valid = False
    return is_valid

@bot.event
async def on_ready():
    await tree.sync()  # Sync slash commands
    print("Slash commands have been synced.")
    latest_version = fetch_latest_release()
    activity = discord.Game(name=latest_version)
    await bot.change_presence(activity=activity)
    print(f"\nBot activity updated to latest version: {latest_version}\n")
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send("Bot has started up!")
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

# Startet den Webserver, wenn der Bot startet
keep_alive()

# Ab hier folgt dein bestehender Code (Voice Commands, Queue, etc.)
@tree.command(name="join", description="Makes the bot join a voice channel")
async def join(interaction: discord.Interaction, channel_name: str):
    guild = interaction.guild
    voice_channel = discord.utils.get(guild.voice_channels, name=channel_name)
    if voice_channel is None:
        await interaction.response.send_message(f"Channel '{channel_name}' not found.")
        return

    voice_client = bot.custom_voice_clients.get(guild.id)
    if voice_client is not None and voice_client.is_connected():
        await voice_client.move_to(voice_channel)
        await interaction.response.send_message(f"Moved to voice channel '{channel_name}'.")
    else:
        voice_client = await voice_channel.connect(self_deaf=True)  # Make the bot deaf
        bot.custom_voice_clients[guild.id] = voice_client
        await interaction.response.send_message(f"Joined and deafened in voice channel '{channel_name}'.")

@tree.command(name="leave", description="Makes the bot leave the current voice channel")
async def leave(interaction: discord.Interaction):
    voice_client = bot.custom_voice_clients.get(interaction.guild.id)

    if voice_client:
        await voice_client.disconnect()
        await interaction.response.send_message("Disconnected from the voice channel.")
        bot.custom_voice_clients.pop(interaction.guild.id, None)
    else:
        await interaction.response.send_message("I'm not in a voice channel.")

@tree.command(name="addtoqueue", description="Adds a song to the queue.")
async def add_to_queue(interaction: discord.Interaction, url: str):
    
    if not is_url_valid(url):
        await interaction.response.send_message("Can't add this url to the queue.")
        return

    MAIN_QUEUE.add_to_queue(url)
    await interaction.response.send_message(f"Added {url} to queue.")

@tree.command(name="play", description="Plays the current song in the queue.")
async def play(interaction: discord.Interaction):
    if len(MAIN_QUEUE.full_url_array) <= 0:
        await interaction.response.send_message("The Queue is empty.")
        return

    await interaction.response.defer()

    channel = interaction.user.voice.channel
    voice_client = bot.custom_voice_clients.get(interaction.guild.id)

    await streaming.startStreaming(voice_client, interaction, channel, bot, MAIN_QUEUE)
    await interaction.followup.send(f"Now streaming: {MAIN_QUEUE.get_current_song()}")

@tree.command(name="stop", description="Stops playing the current song.")
async def stop(interaction: discord.Interaction):
    await interaction.response.send_message("Stopping...")
    voice_client = bot.custom_voice_clients.get(interaction.guild.id)
    voice_client.stop()

@tree.command(name="listqueue", description="Lists the elements of the queue.")
async def listqueue(interaction: discord.Interaction):
    await interaction.response.send_message(MAIN_QUEUE.list_queue())

@tree.command(name="skip", description="Skips the current song.")
async def skip(interaction: discord.Interaction):
    await interaction.response.send_message("Skipping...")
    MAIN_QUEUE.goto_next_song()
    voice_client = bot.custom_voice_clients.get(interaction.guild.id)
    voice_client.stop()
    channel = interaction.user.voice.channel
    await streaming.startStreaming(voice_client, interaction, channel, bot, MAIN_QUEUE)
    await interaction.followup.send(f"Now streaming: {MAIN_QUEUE.get_current_song()}")

@tree.command(name="crash", description="Shuts down the bot, useful for simulating crashes")
async def crash(interaction: discord.Interaction):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send("Bot is shutting down via /stop command.")
    await interaction.response.send_message("Shutting down...")
    await bot.close()
    sys.exit()


ai_convo = ai.conversation()

@bot.tree.command(name="ask-ai", description="Ask the AI something.")
async def askAi(interaction: discord.Interaction, prompt: str):
    global ai_convo
    await interaction.response.defer()

    ai_response, conversation = ai.generate(prompt, ai_convo)
    ai_convo = conversation

    await interaction.followup.send(ai_response)

@bot.tree.command(name="clearconversation", description="Clear's the current conversation")
async def clearConvo(interaction: discord.Interaction):

    user = interaction.user

    role_name = "// Bot Developer"
    role = discord.utils.get(user.roles, name=role_name)

    if role:
        global ai_convo 
        ai_convo = ai.conversation()
        await interaction.response.send_message("Conversation cleared!", ephemeral=True)
    else:
        await interaction.response.send_message("You do not have permission to clear the conversation.", ephemeral=True)


bot.run(TOKEN)