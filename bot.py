import os
import discord
from discord.ext import commands
import yt_dlp
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

ytdl = yt_dlp.YoutubeDL({
    "format": "bestaudio/best",
    "quiet": True
})

def source(url):
    return discord.FFmpegPCMAudio(url, options="-vn")

async def search(query):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(
        None,
        lambda: ytdl.extract_info(f"ytsearch1:{query}", download=False)
    )
    return data["entries"]

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot Ready:", bot.user)

@bot.tree.command(name="play")
async def play(interaction: discord.Interaction, query: str):

    await interaction.response.defer()

    if not interaction.user.voice:
        return await interaction.followup.send("Join voice channel first")

    channel = interaction.user.voice.channel

    try:
        vc = interaction.guild.voice_client

        if not vc:
            vc = await channel.connect()

        elif vc.channel != channel:
            await vc.move_to(channel)

        results = await search(query)

        song = results[0]
        url = song["url"]

        if vc.is_playing():
            vc.stop()

        vc.play(source(url))

        await interaction.followup.send(f"Now Playing: {song['title']}")

    except Exception as e:
        await interaction.followup.send(f"Error: {e}")
        print("VOICE ERROR:", e)

@bot.tree.command(name="stop")
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        await vc.disconnect()
    await interaction.response.send_message("Stopped")

bot.run(os.getenv("DISCORD_TOKEN"))
