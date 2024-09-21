import time
import psutil
import music_queue
from dotenv import load_dotenv
import discord
from discord.ext import commands
import os
import sys
import asyncio
from pydub import AudioSegment
import yt_dlp
import re

# Load environment variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID'))
OPUS_PATH = os.getenv('OPUS_PATH')

# Load the Opus library using the path from the .env file
discord.opus.load_opus(OPUS_PATH)

voice_client = None
mainqueue = music_queue.queue([], True)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree


@bot.event
async def on_ready():
    await tree.sync()  # Sync slash commands
    print("Slash commands have been synced.")
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


@bot.tree.command(name="play", description="Plays audio from queue.")
async def play(interaction: discord.Interaction):
    if not interaction.user.voice:
        await interaction.response.send_message("You need to be in a voice channel to play audio.")
        return
    if len(mainqueue.file_array) <= 0:
        await interaction.response.send_message("The queue is empty.")
        return
    song_name = mainqueue.get_current_song()
    file_path = mainqueue.name_to_path(song_name)
    channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client
    if voice_client is None:
        voice_client = await channel.connect()
    if file_path.endswith('.mp3'):
        audio = AudioSegment.from_mp3(file_path)
        wav_file_path = "temp.wav"
        audio.export(wav_file_path, format='wav')
    elif file_path.endswith('.wav'):
        wav_file_path = file_path
    else:
        await interaction.response.send_message("Unsupported file format. Please use .wav or .mp3.")
        return
    voice_client.play(discord.FFmpegPCMAudio(wav_file_path), after=mainqueue.goto_next_song())
    await interaction.response.send_message(f"Now playing: {song_name}")
    while voice_client.is_playing():
        await asyncio.sleep(1)
    if os.path.exists(wav_file_path):
        os.remove(wav_file_path)  # Remove temporary file


@bot.tree.command(name="listqueue", description="Lists all of the Songs in the current queue.")
async def listqueue(interaction: discord.Interaction):
    await interaction.response.send_message(mainqueue.list_queue())


@bot.tree.command(name="canloop", description="TRUE or FALSE: do you want the playlist to loop?")
async def canloop(interaction: discord.Interaction, userinput: str):
    if userinput.upper() == "TRUE":
        mainqueue.loop_when_done_playing = True
    elif userinput.upper() == "FALSE":
        mainqueue.loop_when_done_playing = False
    else:
        await interaction.response.send_message("Sorry, I could not understand the parameter.")
        return
    await interaction.response.send_message("Looping status set successfully!")


@bot.tree.command(name="add_song_to_queue", description="Adds a song to the queue.")
async def add_song_to_queue(interaction: discord.Interaction, song_name: str):
    result = mainqueue.add_to_queue(song_name)
    await interaction.response.send_message(result)


@tree.command(name="play-yt", description="Plays audio from a YouTube video.")
async def play_yt(interaction: discord.Interaction, url: str):
    if "youtube.com" not in url:
        await interaction.response.send_message("You have to use a YouTube Link")
        return
    if not interaction.user.voice:
        await interaction.response.send_message("You need to be in a voice channel to play audio.")
        return
    await interaction.response.defer()
    channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client
    if voice_client is None:
        voice_client = await channel.connect()
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/temp_%(id)s.%(ext)s',  # Temporarily download with a safe name
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            raw_title = info['title']
            video_id = info['id']
            downloaded_temp_file = f"downloads/temp_{video_id}.mp3"
            sanitized_title = sanitize_filename(raw_title)
            final_audio_file = f"downloads/{sanitized_title}.mp3"
            if os.path.exists(downloaded_temp_file):
                os.rename(downloaded_temp_file, final_audio_file)
                print(f"Renamed file from {downloaded_temp_file} to {final_audio_file}")
        voice_client.play(discord.FFmpegPCMAudio(final_audio_file),
                          after=lambda e: cleanup_after_playback(final_audio_file))
        await interaction.followup.send(f"Playing now: {url}")
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {str(e)}")


def cleanup_after_playback(audio_file):
    if os.path.exists(audio_file):
        os.remove(audio_file)  # Delete the audio file after playback
        print(f"Deleted audio file: {audio_file}")
    # Force kill the FFmpeg process if not terminated
    for proc in psutil.process_iter():
        if proc.name() == 'ffmpeg':
            proc.kill()
            print(f"Force killed lingering FFmpeg process: {proc.pid}")


def sanitize_filename(filename):
    # Replace any character that is not a letter, number, hyphen, or underscore with an underscore
    return re.sub(r'[^a-zA-Z0-9-_]', '_', filename)


bot.run(TOKEN)