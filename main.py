import os
import sys
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
import yt_dlp

import streaming


def exit_handler():
    print('Deleting all files…')


# Load environment variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID'))
OPUS_PATH = os.getenv('OPUS_PATH')
discord.opus.load_opus(OPUS_PATH)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

# Track voice clients for each guild
bot.custom_voice_clients = {}


@bot.event
async def on_ready():
    await tree.sync()  # Sync slash commands
    print("Slash commands have been synced.")
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send("Bot has started up!")
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')


@tree.command(name="stop", description="Shuts down the bot, useful for simulating crashes")
async def stop(interaction: discord.Interaction):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send("Bot is shutting down via /stop command.")
    await interaction.response.send_message("Shutting down...")
    await bot.close()
    sys.exit()


# Slash command to join a voice channel and make the bot deaf
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


# Slash command to leave the voice channel
@tree.command(name="leave", description="Makes the bot leave the current voice channel")
async def leave(interaction: discord.Interaction):
    voice_client = bot.custom_voice_clients.get(interaction.guild.id)

    if voice_client:
        await voice_client.disconnect()
        await interaction.response.send_message("Disconnected from the voice channel.")
        bot.custom_voice_clients.pop(interaction.guild.id, None)
    else:
        await interaction.response.send_message("I'm not in a voice channel.")


# Slash command to play YouTube audio without downloading
@tree.command(name="play-yt", description="Streams audio from a YouTube video.")
async def play_yt(interaction: discord.Interaction, url: str):
    if "youtube.com" not in url:
        await interaction.response.send_message("Please provide a valid YouTube link.")
        return
    if not interaction.user.voice:
        await interaction.response.send_message("You need to be in a voice channel to play audio.")
        return
    await interaction.response.defer()
    channel = interaction.user.voice.channel
    voice_client = bot.custom_voice_clients.get(interaction.guild.id)

    await streaming.startStreaming(voice_client, interaction, channel, bot, url)

    await interaction.followup.send(f"Now streaming: {url}")


def cleanup(client):
    client.stop()


bot.run(TOKEN)
