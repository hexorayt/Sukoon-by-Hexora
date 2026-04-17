import os
import discord
from discord.ext import commands
import yt_dlp
import asyncio

# ================= INTENTS =================
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= YTDL =================
ytdl = yt_dlp.YoutubeDL({
    'format': 'bestaudio/best',
    'quiet': True,
    'noplaylist': True
})

ffmpeg_options = {'options': '-vn'}

# ================= AUDIO =================
def get_audio(url):
    return discord.FFmpegPCMAudio(url, **ffmpeg_options)

# ================= SEARCH (FAST) =================
async def search_song(query):
    loop = asyncio.get_event_loop()

    data = await loop.run_in_executor(
        None,
        lambda: ytdl.extract_info(f"ytsearch3:{query}", download=False)
    )

    return data.get("entries", [])

# ================= NOW PLAY NEXT =================
async def play_next(vc, url, title):
    vc.play(get_audio(url))

# ================= PLAY COMMAND =================
@bot.tree.command(name="play", description="Play music")
async def play(interaction: discord.Interaction, query: str):

    # FIX: avoid thinking stuck
    await interaction.response.defer()

    # voice check
    if not interaction.user.voice:
        return await interaction.followup.send("❌ Join voice channel first")

    channel = interaction.user.voice.channel

    if not interaction.guild.voice_client:
        await channel.connect()

    vc = interaction.guild.voice_client

    # search song
    results = await search_song(query)

    if not results:
        return await interaction.followup.send("❌ No song found")

    song = results[0]
    title = song["title"]
    url = song["url"]

    vc.stop()
    vc.play(get_audio(url))

    await interaction.followup.send(f"🎧 Now Playing: **{title}**")

# ================= NOW PLAYING =================
@bot.tree.command(name="nowplaying")
async def nowplaying(interaction: discord.Interaction):
    vc = interaction.guild.voice_client

    if vc and vc.is_playing():
        await interaction.response.send_message("🎶 Song is playing")
    else:
        await interaction.response.send_message("❌ Nothing playing")

# ================= READY =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

# ================= RUN =================
bot.run(os.getenv("DISCORD_TOKEN"))
