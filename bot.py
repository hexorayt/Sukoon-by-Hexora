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

ffmpeg_options = {
    'options': '-vn'
}

def get_audio(url):
    return discord.FFmpegPCMAudio(url, **ffmpeg_options)

# ================= SEARCH =================
async def search_song(query):
    loop = asyncio.get_event_loop()

    data = await loop.run_in_executor(
        None,
        lambda: ytdl.extract_info(f"ytsearch3:{query}", download=False)
    )

    return data.get("entries", [])

# ================= READY =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user} ✔ BOT STABLE READY")

# ================= PLAY COMMAND (FIXED CORE ISSUE) =================
@bot.tree.command(name="play")
async def play(interaction: discord.Interaction, query: str):

    await interaction.response.defer(thinking=True)

    # voice check
    if not interaction.user.voice:
        return await interaction.followup.send("❌ Join voice channel first")

    channel = interaction.user.voice.channel

    vc = interaction.guild.voice_client

    try:
        # CONNECT / MOVE FIX
        if not vc:
            vc = await channel.connect()

        elif vc.channel != channel:
            await vc.move_to(channel)

        # SEARCH
        results = await search_song(query)

        if not results:
            return await interaction.followup.send("❌ No song found")

        song = results[0]
        url = song["url"]

        # STOP OLD AUDIO SAFELY
        if vc.is_playing():
            vc.stop()

        # PLAY AUDIO SAFE (NO CRASH)
        source = discord.FFmpegPCMAudio(url, options='-vn')
        vc.play(source)

        await interaction.followup.send(f"🎧 Now Playing: **{song['title']}**")

    except Exception as e:
        print("VOICE ERROR:", e)
        try:
            await interaction.followup.send(f"❌ Error: {e}")
        except:
            pass

# ================= STOP =================
@bot.tree.command(name="stop")
async def stop(interaction: discord.Interaction):

    vc = interaction.guild.voice_client

    try:
        if vc:
            await vc.disconnect()

        await interaction.response.send_message("⛔ Stopped")

    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")

# ================= RUN =================
bot.run(os.getenv("DISCORD_TOKEN"))
