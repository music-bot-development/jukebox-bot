import os
import downloader
import fileManagement
import sys
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from pydub import AudioSegment
import music_queue
import atexit

def exit_handler():
    print('Deleting all files…')
    fileManagement.cleanup_download_folder()
atexit.register(exit_handler)

# Load environment variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID'))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

# Track voice clients for each guild
bot.custom_voice_clients = {}
mainqueue = music_queue.queue([], True)

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
    
    cleanup(voice_client)


# Slash command to play audio from the queue
@tree.command(name="play", description="Plays audio from queue.")
async def play(interaction: discord.Interaction):
    if not interaction.user.voice:
        await interaction.response.send_message("You need to be in a voice channel to play audio.")
        return
    if not mainqueue.file_array:
        await interaction.response.send_message("The queue is empty.")
        return

    song_name = mainqueue.get_current_song()
    file_path = mainqueue.name_to_path(song_name)
    channel = interaction.user.voice.channel
    voice_client = bot.custom_voice_clients.get(interaction.guild.id)

    if voice_client is None or not voice_client.is_connected():
        voice_client = await channel.connect(self_deaf=True)  # Make the bot deaf when connecting
        bot.custom_voice_clients[interaction.guild.id] = voice_client

    if file_path.endswith('.mp3'):
        audio = AudioSegment.from_mp3(file_path)
        wav_file_path = "temp.wav"
        audio.export(wav_file_path, format='wav')
    elif file_path.endswith('.wav'):
        wav_file_path = file_path
    else:
        await interaction.response.send_message("Unsupported file format. Please use .wav or .mp3.")
        return

    voice_client.play(discord.FFmpegPCMAudio(wav_file_path), after=lambda e: on_song_end(interaction.guild))

    mainqueue.goto_next_song()
    await interaction.response.send_message(f"Now playing: {song_name}")

def on_song_end(guild):
    voice_client = bot.custom_voice_clients.get(guild.id)

    if mainqueue.file_array:
        next_song = mainqueue.get_current_song()
        file_path = mainqueue.name_to_path(next_song)

        # Determine wav file path
        if file_path.endswith('.mp3'):
            audio = AudioSegment.from_mp3(file_path)
            wav_file_path = "temp.wav"
            audio.export(wav_file_path, format='wav')
        elif file_path.endswith('.wav'):
            wav_file_path = file_path
        else:
            return  # Unsupported format, exit the function

        # Play the song if the voice client exists
        if voice_client:
            voice_client.play(discord.FFmpegPCMAudio(wav_file_path), after=lambda e: on_song_end(guild))

        # Remove temp file if created
        if file_path.endswith('.mp3') and os.path.exists("temp.wav"):
            os.remove("temp.wav")

    else:
        # Disconnect and cleanup if no more songs
        if voice_client:
            asyncio.run_coroutine_threadsafe(voice_client.disconnect(), bot.loop)
            bot.custom_voice_clients.pop(guild.id, None)

        # Clean up temp file if it exists
        if os.path.exists("temp.wav"):
            os.remove("temp.wav")


@tree.command(name="play-yt", description="Plays audio from a YouTube video.")
async def play_yt(interaction: discord.Interaction, url: str):
    
    fileManagement.cleanup_download_folder()

    if "youtube.com" not in url:
        await interaction.response.send_message("Please provide a valid YouTube link.")
        return
    if not interaction.user.voice:
        await interaction.response.send_message("You need to be in a voice channel to play audio.")
        return
    await interaction.response.defer()
    channel = interaction.user.voice.channel
    voice_client = bot.custom_voice_clients.get(interaction.guild.id)
    
    # TODO: maybe move to own function
    if voice_client is None or not voice_client.is_connected():
        voice_client = await channel.connect(self_deaf=True)  # Make the bot deaf
        bot.custom_voice_clients[interaction.guild.id] = voice_client

    success, file_or_errormsg = downloader.download_yt_mp3_from_url(url)

    audiofile = ""

    if not success:
        await interaction.followup.send(f"An error occurred: {str(file_or_errormsg)}")
        return
    else:
        audiofile = file_or_errormsg

    await interaction.followup.send(f"Now playing: {url}")
    voice_client.play(discord.FFmpegPCMAudio(audiofile),
                        after=lambda e: cleanup(voice_client))

def cleanup(client):
    
    client.stop()

    fileManagement.cleanup_ffmpeg()
    fileManagement.cleanup_download_folder()


bot.run(TOKEN)
