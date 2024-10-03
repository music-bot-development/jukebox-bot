import os
import sys
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import requests
from getVersion import *
import streaming
import random

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID'))
OPUS_PATH = os.getenv('OPUS_PATH')
discord.opus.load_opus(OPUS_PATH)
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents, status=discord.Status.dnd)
bot.custom_voice_clients = {}  # Initialize the custom_voice_clients attribute
tree = bot.tree

# A dictionary to store user points
user_points = {}

@bot.event
async def on_ready():
    await tree.sync()  # Sync slash commands
    print("Slash commands have been synced.")
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send("Bot has started up!")
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    update_activity.start()

@tasks.loop(minutes=1)  # Update every minute 
async def update_activity():
    latest_version = fetch_latest_release()
    activity = discord.Game(name=latest_version)
    await bot.change_presence(activity=activity)
    print(f"Bot activity updated to latest version: {latest_version}")

# Command to gamble points
@tree.command(name="gamble", description="Gamble some of your points!")
async def gamble(interaction: discord.Interaction, amount: int):
    user_id = interaction.user.id

    # Ensure the user has points to gamble
    if user_id not in user_points:
        user_points[user_id] = 100  # Start users with 100 points

    if user_points[user_id] < amount:
        await interaction.response.send_message(f"You don't have enough points to gamble. You currently have {user_points[user_id]} points.")
        return

    # Simple gamble logic
    if random.random() > 0.5:
        user_points[user_id] += amount
        await interaction.response.send_message(f"Congratulations! You won {amount} points. You now have {user_points[user_id]} points.")
    else:
        user_points[user_id] -= amount
        await interaction.response.send_message(f"Sorry, you lost {amount} points. You now have {user_points[user_id]} points.")

# Command to check a users points
@tree.command(name="points", description="Check how many points a user has.")
async def points(interaction: discord.Interaction, user: discord.User):
    user_id = user.id
    if user_id not in user_points:
        user_points[user_id] = 100  # Start users with 100 points

    await interaction.response.send_message(f"<@{user_id}> has {user_points[user_id]} points.")


# Command to check the leaderboard
@tree.command(name="leaderboard", description="Check the top users by points.")
async def leaderboard(interaction: discord.Interaction):
    if not user_points:
        await interaction.response.send_message("No points have been recorded yet.")
        return

    sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)
    leaderboard_text = "\n".join([f"<@{user_id}>: {points} points" for user_id, points in sorted_users[:10]])

    await interaction.response.send_message(f"**Leaderboard:**\n{leaderboard_text}")

# Command for admins to add points
@tree.command(name="add-points", description="Add points to a user (Admins only).")
async def add_points(interaction: discord.Interaction, user: discord.User, amount: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    user_id = user.id
    if user_id not in user_points:
        user_points[user_id] = 100  # Initialize if the user doesn't have any points

    user_points[user_id] += amount
    await interaction.response.send_message(f"Added {amount} points to <@{user_id}>. They now have {user_points[user_id]} points.")

# Command for admins to remove points
@tree.command(name="remove-points", description="Remove points from a user (Admins only).")
async def remove_points(interaction: discord.Interaction, user: discord.User, amount: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    user_id = user.id
    if user_id not in user_points:
        user_points[user_id] = 100  # Initialize if the user doesn't have any points

    user_points[user_id] = max(0, user_points[user_id] - amount)  # Ensure points don't go below zero
    await interaction.response.send_message(f"Removed {amount} points from <@{user_id}>. They now have {user_points[user_id]} points.")

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

@tree.command(name="rickroll", description="Rickrolls some people")
async def rickroll(interaction: discord.Interaction, channel: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    guild = interaction.guild
    voice_channel = discord.utils.get(guild.voice_channels, name=channel)  # Get the actual voice channel object

    if voice_channel is None:
        await interaction.response.send_message(f"Channel '{channel}' not found.")
        return

    voice_client = bot.custom_voice_clients.get(guild.id)
    rickroll_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'  # Define the Rickroll URL

    # Start streaming in the correct voice channel
    await streaming.startStreaming(voice_client, interaction, voice_channel, bot, rickroll_url)
    await interaction.response.send_message(f"Rickrolling with: {rickroll_url}")

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

@tree.command(name="stop", description="Shuts down the bot, useful for simulating crashes")
async def stop(interaction: discord.Interaction):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send("Bot is shutting down via /stop command.")
    await interaction.response.send_message("Shutting down...")
    await bot.close()
    sys.exit()

def cleanup(client):
    client.stop()


@tree.command(name="who-created-the-pyramids", description="Tells you the answer to who created the pyramids")
async def who_created_the_pyramids(interaction: discord.Interaction):
    await interaction.response.send_message(file=discord.File('images/pyramids-aliens-meme.jpg'))



bot.run(TOKEN)
