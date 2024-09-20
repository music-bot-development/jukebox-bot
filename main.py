from dotenv import load_dotenv
import discord
from discord.ext import commands
import os
import sys

load_dotenv()


TOKEN = "MTI4NjY4Nzk4Mzg3MzAzNjQwMg.GXBYH4.Pid_aMxrr5EwWqXjTGs_PwsjxhlAiI9LeRHuls"

# Channel ID where the bot should log the start and shutdown messages
LOG_CHANNEL_ID = 1286649079266279549

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


bot.run(TOKEN)