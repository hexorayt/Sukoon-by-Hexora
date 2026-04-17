import os
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
        lambda: ytdl.extract_info(f"ytsearch10:{query}", download=False)
    )
    return data.get("entries", [])

# ================= AUTO NEXT =================
async def play_next(vc, guild_id):
    if guild_id in queues and queues[guild_id]:
        song = queues[guild_id].popleft()

        vc.play(
            get_audio(song["url"]),
            after=lambda e: asyncio.run_coroutine_threadsafe(
                play_next(vc, guild_id),
                bot.loop
            )
        )

# ================= SELECT MENU =================
class SongSelect(discord.ui.Select):
    def __init__(self, results, vc, guild_id):

        options = [
            discord.SelectOption(
                label=s["title"][:100],
                description="Click to play",
                value=str(i)
            )
            for i, s in enumerate(results)
        ]

        super().__init__(placeholder="🎧 Select a song", options=options)
        self.results = results
        self.vc = vc
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):

        song = self.results[int(self.values[0])]

        queues.setdefault(self.guild_id, deque())

        self.vc.stop()

        self.vc.play(
            get_audio(song["url"]),
            after=lambda e: asyncio.run_coroutine_threadsafe(
                play_next(self.vc, self.guild_id),
                bot.loop
            )
        )

        await interaction.response.send_message(
            f"🎧 Now Playing: **{song['title']}**",
            ephemeral=False
        )

class SongView(discord.ui.View):
    def __init__(self, results, vc, guild_id):
        super().__init__(timeout=60)
        self.add_item(SongSelect(results, vc, guild_id))

# ================= CONTROL BUTTONS =================
class MusicControls(discord.ui.View):
    def __init__(self, vc):
        super().__init__(timeout=None)
        self.vc = vc

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.gray)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.vc.pause()
        await interaction.response.send_message("⏸ Paused", ephemeral=True)

    @discord.ui.button(label="Resume", style=discord.ButtonStyle.green)
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.vc.resume()
        await interaction.response.send_message("▶ Resumed", ephemeral=True)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.blurple)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.vc.stop()
        await interaction.response.send_message("⏭ Skipped", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.vc.disconnect()
        await interaction.response.send_message("⛔ Stopped", ephemeral=True)

# ================= READY =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"DJ ULTRA READY ✔ {bot.user}")

# ================= PLAY =================
@bot.tree.command(name="play")
async def play(interaction: discord.Interaction, query: str):

    await interaction.response.defer(thinking=True)

    if not interaction.user.voice:
        return await interaction.followup.send("❌ Join voice channel first")

    channel = interaction.user.voice.channel

    vc = interaction.guild.voice_client

    if not vc:
        vc = await channel.connect()

    results = await search_song(query)

    if not results:
        return await interaction.followup.send("❌ No songs found")

    # dropdown menu
    view = SongView(results, vc, interaction.guild.id)

    await interaction.followup.send("🎧 Select a song:", view=view)

# ================= NOW PLAYING CONTROLS =================
@bot.tree.command(name="controls")
async def controls(interaction: discord.Interaction):

    vc = interaction.guild.voice_client

    if not vc:
        return await interaction.response.send_message("❌ Nothing playing")

    view = MusicControls(vc)

    await interaction.response.send_message("🎛 DJ Controls:", view=view)

# ================= RUN =================
bot.run(os.getenv("DISCORD_TOKEN"))
