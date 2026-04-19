import discord
from discord.ext import commands
import yt_dlp
import asyncio

# ================= BOT SETUP =================
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= YTDL =================
ytdl = yt_dlp.YoutubeDL({
    'format': 'bestaudio/best',
    'quiet': True
})

def get_audio(url):
    return discord.FFmpegPCMAudio(url, options='-vn')

# ================= SEARCH =================
async def search_song(query):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(
        None,
        lambda: ytdl.extract_info(f"ytsearch1:{query}", download=False)
    )
    return data["entries"][0]

# ================= GLOBAL =================
current_vc = None

# ================= UI BUTTONS =================
class MusicControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.secondary)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if current_vc and current_vc.is_playing():
            current_vc.pause()
            await interaction.response.send_message("⏸ Paused", ephemeral=True)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.primary)
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        if current_vc and current_vc.is_paused():
            current_vc.resume()
            await interaction.response.send_message("▶ Resumed", ephemeral=True)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if current_vc:
            current_vc.stop()
            await interaction.response.send_message("⏭ Skipped", ephemeral=True)

# ================= SELECT MENU =================
class SongSelectMenu(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Libaas Kaka"),
            discord.SelectOption(label="Tere Mere Pyar Ki"),
            discord.SelectOption(label="Mere Dil Ki Galiyon Mein"),
        ]
        super().__init__(placeholder="Select a song...", options=options)

    async def callback(self, interaction: discord.Interaction):
        global current_vc

        if not interaction.user.voice:
            return await interaction.response.send_message("Join VC first", ephemeral=True)

        channel = interaction.user.voice.channel

        vc = interaction.guild.voice_client
        if not vc:
            vc = await channel.connect()

        elif vc.channel != channel:
            await vc.move_to(channel)

        song_name = self.values[0]

        await interaction.response.defer()

        data = await search_song(song_name)

        if vc.is_playing():
            vc.stop()

        source = get_audio(data["url"])
        vc.play(source)

        current_vc = vc

        await interaction.followup.send(f"🎧 Playing: {song_name}")

# ================= MAIN VIEW =================
class MainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SongSelectMenu())
        self.add_item(MusicControlView().children[0])
        self.add_item(MusicControlView().children[1])
        self.add_item(MusicControlView().children[2])

# ================= PLAYER COMMAND =================
@bot.command()
async def player(ctx):

    embed = discord.Embed(
        title="🎧 DJ PLAYER",
        description="Select song & control music",
        color=discord.Color.teal()
    )

    embed.set_image(url="https://i.ytimg.com/vi/bY73vFGhSVk/maxresdefault.jpg")

    view = MainView()

    await ctx.send(embed=embed, view=view)

# ================= READY =================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# ================= RUN =================
import os
bot.run(os.getenv("DISCORD_TOKEN"))
