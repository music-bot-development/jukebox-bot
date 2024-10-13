import os
import sys
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import requests
from getVersion import *
import music_queue
import streaming
import random
from urllib.parse import urlparse

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID'))
#OPUS_PATH = os.getenv('OPUS_PATH')
MAIN_QUEUE = music_queue.queue([], False)
#discord.opus.load_opus(OPUS_PATH)
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)
bot.custom_voice_clients = {}  # Initialize the custom_voice_clients attribute
tree = bot.tree

AUTO_UPDATE = True

# A dictionary to store user points
user_points = {}



def is_url_valid(url: str):
    is_valid = True

    try:
        parsed_url = urlparse(url)
        if parsed_url.hostname != "www.youtube.com" or parsed_url.hostname != "youtu.be":
            is_valid = False
    except Exception as e:
        is_valid = False

    return is_valid

@bot.event
async def on_ready():
    await tree.sync()  # Sync slash commands
    print("Slash commands have been synced.")
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send("Bot has started up!")
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    
    if AUTO_UPDATE:
        update_activity.start()

@tasks.loop(minutes=1)  # Update every minute 
async def update_activity():
    latest_version = fetch_latest_release()
    activity = discord.Game(name=latest_version)
    await bot.change_presence(activity=activity)
    print(f"Bot activity updated to latest version: {latest_version}")

# Existing voice-related commands, etc.
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

#TODO: Remove Repetitive Code
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

@tree.command(name="ask-ai", description="Asks chatgpt 3.")
async def ai(interaction: discord.Interaction, prompt: str):
    await interaction.response.send_message("Comming soon!")

bot.run(TOKEN)