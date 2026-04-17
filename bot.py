import sys
sys.stdout.reconfigure(encoding='utf-8')

import discord
from discord.ext import commands
import yt_dlp
import asyncio
from collections import deque

# ================= INTENTS =================
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= DATA =================
queues = {}
now_playing = {}

# ================= YTDL =================
ytdl = yt_dlp.YoutubeDL({
    'format': 'bestaudio/best',
    'quiet': True,
    'noplaylist': True
})

ffmpeg_options = {'options': '-vn'}

# ================= SONG =================
class Song:
    def __init__(self, url, title):
        self.url = url
        self.title = title

# ================= SEARCH =================
async def search_song(query):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(
        None,
        lambda: ytdl.extract_info(f"ytsearch5:{query}", download=False)
    )
    return data.get("entries", [])

# ================= AUDIO =================
def get_audio(url, seek=0):
    if seek > 0:
        return discord.FFmpegPCMAudio(
            url,
            before_options=f"-ss {seek}",
            options='-vn'
        )
    return discord.FFmpegPCMAudio(url, **ffmpeg_options)

# ================= PLAY NEXT =================
async def play_next(guild_id):
    try:
        vc = now_playing[guild_id]["vc"]

        if guild_id not in queues or len(queues[guild_id]) == 0:
            now_playing.pop(guild_id, None)
            return

        song = queues[guild_id].popleft()

        now_playing[guild_id] = {
            "vc": vc,
            "song": song.title,
            "url": song.url,
            "time": 0
        }

        def after_play(e):
            asyncio.run_coroutine_threadsafe(play_next(guild_id), bot.loop)

        vc.play(get_audio(song.url), after=after_play)

    except Exception as e:
        print("play_next error:", e)

# ================= READY =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot Ready 🔥", bot.user)

# ================= JOIN =================
async def join_voice(interaction):
    if not interaction.user.voice:
        return None

    channel = interaction.user.voice.channel

    if not interaction.guild.voice_client:
        await channel.connect()

    return interaction.guild.voice_client

# ================= BUTTONS =================
class MusicControls(discord.ui.View):
    def __init__(self, vc, guild_id):
        super().__init__(timeout=None)
        self.vc = vc
        self.guild_id = guild_id

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.gray)
    async def pause(self, interaction, button):
        self.vc.pause()
        await interaction.response.send_message("⏸ Paused", ephemeral=True)

    @discord.ui.button(label="Resume", style=discord.ButtonStyle.green)
    async def resume(self, interaction, button):
        self.vc.resume()
        await interaction.response.send_message("▶ Resumed", ephemeral=True)

    @discord.ui.button(label="⏩ +10s", style=discord.ButtonStyle.secondary)
    async def forward(self, interaction, button):

        data = now_playing.get(self.guild_id)

        if not data:
            return await interaction.response.send_message("No song playing", ephemeral=True)

        url = data["url"]
        current = data.get("time", 0)
        new_time = current + 10

        self.vc.stop()

        # 🔥 FIXED SEEK SYSTEM
        source = get_audio(url, seek=new_time)

        self.vc.play(source)

        now_playing[self.guild_id]["time"] = new_time

        await interaction.response.send_message(
            f"⏩ Forwarded +10 sec (Now at {new_time}s)",
            ephemeral=True
        )

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red)
    async def stop(self, interaction, button):

        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()

        await interaction.response.send_message("⛔ Stopped", ephemeral=True)

# ================= PLAY =================
@bot.tree.command(name="play", description="Play music")
async def play(interaction: discord.Interaction, query: str):

    await interaction.response.defer()

    vc = await join_voice(interaction)
    if not vc:
        return await interaction.followup.send("Join voice channel first")

    guild_id = interaction.guild.id

    results = await search_song(query)
    if not results:
        return await interaction.followup.send("No song found")

    song_data = results[0]
    song = Song(song_data["url"], song_data["title"])

    queues.setdefault(guild_id, deque())
    queues[guild_id].append(song)

    if guild_id not in now_playing:

        current = queues[guild_id].popleft()

        now_playing[guild_id] = {
            "vc": vc,
            "song": current.title,
            "url": current.url,
            "time": 0
        }

        vc.play(
            get_audio(current.url),
            after=lambda e: asyncio.run_coroutine_threadsafe(play_next(guild_id), bot.loop)
        )

        view = MusicControls(vc, guild_id)

        await interaction.followup.send(
            f"🎧 Now Playing: **{current.title}**",
            view=view
        )

    else:
        await interaction.followup.send(f"➕ Added to queue: {song.title}")

# ================= NOW PLAYING =================
@bot.tree.command(name="nowplaying")
async def nowplaying(interaction: discord.Interaction):

    song = now_playing.get(interaction.guild.id, {}).get("song", "Nothing")
    await interaction.response.send_message(f"🎶 Now Playing: {song}")

# ================= RUN =================

import os
bot.run(os.getenv("DISCORD_TOKEN"))