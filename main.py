import os
import re
import sys
import psutil
import asyncio
import discord
import yt_dlp
from discord.ext import commands
from dotenv import load_dotenv
from pydub import AudioSegment
import music_queue

# Load environment variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID'))
OPUS_PATH = os.getenv('OPUS_PATH')

# Load the Opus library using the path from the .env file
discord.opus.load_opus(OPUS_PATH)

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
    if mainqueue.file_array:
        next_song = mainqueue.get_current_song()
        file_path = mainqueue.name_to_path(next_song)
        if file_path.endswith('.mp3'):
            audio = AudioSegment.from_mp3(file_path)
            wav_file_path = "temp.wav"
            audio.export(wav_file_path, format='wav')
        elif file_path.endswith('.wav'):
            wav_file_path = file_path
        else:
            return
        voice_client = bot.custom_voice_clients.get(guild.id)
        if voice_client:
            voice_client.play(discord.FFmpegPCMAudio(wav_file_path), after=lambda e: on_song_end(guild))
        if os.path.exists("temp.wav"):
            os.remove("temp.wav")
    else:
        voice_client = bot.custom_voice_clients.get(guild.id)
        if voice_client:
            asyncio.run_coroutine_threadsafe(voice_client.disconnect(), bot.loop)
            bot.custom_voice_clients.pop(guild.id, None)
        if os.path.exists("temp.wav"):
            os.remove("temp.wav")


def cleanup_ffmpeg():
    """Helper function to kill any lingering FFmpeg processes."""
    for proc in psutil.process_iter():
        if proc.name() == 'ffmpeg':
            proc.kill()
            print(f"Force killed lingering FFmpeg process: {proc.pid}")


@tree.command(name="play-yt", description="Plays audio from a YouTube video.")
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

    if voice_client is None or not voice_client.is_connected():
        voice_client = await channel.connect(self_deaf=True)  # Make the bot deaf
        bot.custom_voice_clients[interaction.guild.id] = voice_client

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
                          after=lambda e: cleanup_after_playback(final_audio_file, interaction.guild))
        await interaction.followup.send(f"Now playing: {url}")
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {str(e)}")


def cleanup_after_playback(audio_file, guild):
    if os.path.exists(audio_file):
        os.remove(audio_file)  # Delete the audio file after playback
        print(f"Deleted audio file: {audio_file}")
    cleanup_ffmpeg()  # Kill FFmpeg processes if any
    voice_client = bot.custom_voice_clients.get(guild.id)
    if voice_client and not voice_client.is_playing():
        asyncio.run_coroutine_threadsafe(voice_client.disconnect(), bot.loop)
        bot.custom_voice_clients.pop(guild.id, None)
        print("Disconnected from the voice channel after playback.")


def sanitize_filename(filename):
    # Replace any character that is not a letter, number, hyphen, or underscore with an underscore
    return re.sub(r'[^a-zA-Z0-9-_]', '_', filename)


bot.run(TOKEN)
