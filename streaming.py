import yt_dlp
import discord
import music_queue

import fileManagement

def onStreamEnd(queue: music_queue.queue):
    fileManagement.cleanup_ffmpeg()
    queue.goto_next_song()

async def startStreaming(voice_client, interaction, channel, bot, queue: music_queue.queue):
    if voice_client is None or not voice_client.is_connected():
        voice_client = await channel.connect(self_deaf=True)  # Make the bot deaf
        bot.custom_voice_clients[interaction.guild.id] = voice_client

    with yt_dlp.YoutubeDL(ytdl_options) as ytdl:
        info = ytdl.extract_info(queue.get_current_song(), download=False)
        audio_url = info['url']

    voice_client.play(discord.FFmpegPCMAudio(audio_url, **ffmpeg_options),
                      after=lambda e: onStreamEnd(queue))


ytdl_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'default_search': 'auto',
    'quiet': True
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}