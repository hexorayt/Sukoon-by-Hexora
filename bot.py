import os
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
    'quiet': True,
    'noplaylist': True,

    'http_headers': {
        'User-Agent': 'Mozilla/5.0'
    },

    'extractor_args': {
        'youtube': {
            'player_client': ['android']
        }
    }
})

def get_audio(url):
    return discord.FFmpegPCMAudio(url, options='-vn')

'http_headers': {
    'User-Agent': 'Mozilla/5.0'
},
'socket_timeout': 10,

# ================= SEARCH =================
async def search_song(query):
    loop = asyncio.get_event_loop()

    try:
        data = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: ytdl.extract_info(f"ytsearch3:{query}", download=False)
            ),
            timeout=15  # 🔥 timeout fix
        )

        return data.get("entries", [])

    except asyncio.TimeoutError:
        print("Search Timeout ❌")
        return []

# ================= GLOBAL =================
current_vc = None

# ================= BUTTONS =================
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

# ================= DROPDOWN =================
class SongSelectMenu(discord.ui.Select):
    def __init__(self, songs):
        options = [
            discord.SelectOption(label=s["title"][:100], value=str(i))
            for i, s in enumerate(songs)
        ]
        super().__init__(placeholder="🎧 Select a song", options=options)
        self.songs = songs

    async def callback(self, interaction: discord.Interaction):
        global current_vc

        if not interaction.user.voice:
            return await interaction.response.send_message("❌ Join VC first", ephemeral=True)

        channel = interaction.user.voice.channel
        vc = interaction.guild.voice_client

        if not vc:
            vc = await channel.connect()
        elif vc.channel != channel:
            await vc.move_to(channel)

        song = self.songs[int(self.values[0])]

        if vc.is_playing():
            vc.stop()

        vc.play(get_audio(song["url"]))
        current_vc = vc

        await interaction.response.send_message(f"🎧 Playing: **{song['title']}**")

# ================= VIEW =================
class MainView(discord.ui.View):
    def __init__(self, songs):
        super().__init__(timeout=None)
        self.add_item(SongSelectMenu(songs))
        controls = MusicControlView()
        for item in controls.children:
            self.add_item(item)

# ================= PLAY COMMAND =================
@bot.tree.command(name="play", description="Play music")
async def play(interaction: discord.Interaction, query: str):

    await interaction.response.defer(thinking=True)

    songs = await search_song(query)

    if not songs:
        return await interaction.followup.send("❌ No songs found")

    view = MainView(songs)

    await interaction.followup.send("🎧 Select a song:", view=view)

await interaction.response.defer(thinking=True)

try:
    songs = await search_song(query)

    if not songs:
        return await interaction.followup.send("❌ Timeout / No result")

except Exception as e:
    return await interaction.followup.send("❌ Server busy, try again")

# ================= READY =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✔ Logged in as {bot.user}")

# ================= RUN =================
bot.run(os.getenv("DISCORD_TOKEN"))
