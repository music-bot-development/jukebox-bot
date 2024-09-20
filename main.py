from dotenv import load_dotenv
import discord
from discord.ext import commands
import nacl
import os
import sys

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')

# Channel ID where the bot should log the start and shutdown messages
LOG_CHANNEL_ID = os.getenv('LOG_CHANNEL_ID')

# Create a bot instance
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# Event when the bot has connected to Discord
@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print("Slash commands have been synced.")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send("Bot has started up!")
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')


@bot.tree.command(name="stop", description="Shuts down the bot, useful for simulating crashes")
async def stop(interaction: discord.Interaction):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send("Bot is shutting down via /stop command.")

    await interaction.response.send_message("Shutting down...")

    await bot.close()
    sys.exit()

# Slash command to join a voice channel
@bot.tree.command(name="join", description="Makes the bot join a voice channel")
async def join(interaction: discord.Interaction, channel_name: str):
    # Get the voice channel by name
    guild = interaction.guild
    voice_channel = discord.utils.get(guild.voice_channels, name=channel_name)

    if voice_channel is None:
        await interaction.response.send_message(f"Channel '{channel_name}' not found.")
        return

    # Check if the bot is already connected to a voice channel
    if interaction.guild.voice_client is not None:
        await interaction.guild.voice_client.move_to(voice_channel)
        await interaction.response.send_message(f"Moved to voice channel '{channel_name}'.")
    else:
        # Connect to the voice channel
        await voice_channel.connect()
        await interaction.response.send_message(f"Joined voice channel '{channel_name}'.")


# Slash command to leave the voice channel
@bot.tree.command(name="leave", description="Makes the bot leave the current voice channel")
async def leave(interaction: discord.Interaction):
    # Check if the bot is connected to a voice channel
    voice_client = interaction.guild.voice_client

    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await interaction.response.send_message("Disconnected from the voice channel.")
    else:
        await interaction.response.send_message("I'm not in a voice channel.")


bot.run(TOKEN)