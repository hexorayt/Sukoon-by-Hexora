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

# ================= SAFE VOICE CONNECT =================
async def safe_connect(interaction, channel):
    vc = interaction.guild.voice_client

    try:
        if not vc or not vc.is_connected():
            vc = await channel.connect(timeout=30, reconnect=True)

        elif vc.channel != channel:
            await vc.move_to(channel)

        return vc

    except Exception as e:
        print("VOICE CONNECT ERROR:", e)
        return None

# ================= READY =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✔ Bot Ready: {bot.user}")

# ================= PLAY =================
@bot.tree.command(name="play")
async def play(interaction: discord.Interaction, query: str):

    await interaction.response.defer(thinking=True)

    if not interaction.user.voice:
        return await interaction.followup.send("❌ Join voice channel first")

    channel = interaction.user.voice.channel

    vc = await safe_connect(interaction, channel)

    if not vc:
        return await interaction.followup.send("❌ Voice connect failed (Discord issue)")

    try:
        results = await search_song(query)

        if not results:
            return await interaction.followup.send("❌ No song found")

        song = results[0]
        url = song["url"]

        if vc.is_playing():
            vc.stop()

        source = discord.FFmpegPCMAudio(url, options='-vn')
        vc.play(source)

        await interaction.followup.send(f"🎧 Now Playing: **{song['title']}**")

    except Exception as e:
        print("PLAY ERROR:", e)
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
            await vc.disconnect(force=True)

        await interaction.response.send_message("⛔ Stopped")

    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")

# ================= VOICE RECOVERY =================
@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id and after.channel is None:
        try:
            for vc in bot.voice_clients:
                await vc.disconnect(force=True)
        except:
            pass

# ================= RUN =================
bot.run(os.getenv("DISCORD_TOKEN"))
