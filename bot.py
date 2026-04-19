import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# UI Components: Buttons & Select Menu
class MusicControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Previous song...", ephemeral=True)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.primary)
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Play/Pause toggled!", ephemeral=True)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Skipping song...", ephemeral=True)

class SongSelectMenu(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Libaas", description="By Kaka", emoji="🎵"),
            discord.SelectOption(label="Tere Mere Pyar Ki", description="Banjaran", emoji="🎵"),
            discord.SelectOption(label="Mere Dil Ki Galiyon Mein", description="Alka Yagnik", emoji="🎵"),
        ]
        super().__init__(placeholder="Select a song to play...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Selected: {self.values[0]}", ephemeral=True)

class MainView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(SongSelectMenu())
        # The buttons are added here via a separate class or by adding them directly

# Command to show the Player (Like your Screenshot)
@bot.command()
async def player(ctx):
    embed = discord.Embed(
        title="ANACONDA - PLAYING UNTIL YOUR LAST BREATH",
        description="**Now Playing:** Libaas\n**Artist:** Kaka\n**Platform:** YouTube Music",
        color=discord.Color.teal()
    )
    embed.set_image(url="https://i.ytimg.com/vi/bY73vFGhSVk/maxresdefault.jpg") # Use actual song thumbnail
    embed.add_field(name="Duration", value="04:28", inline=True)
    embed.add_field(name="Volume", value="110%", inline=True)
    embed.set_footer(text="Requester: HexoraYT")

    view = MusicControlView()
    view.add_item(SongSelectMenu())
    
    await ctx.send(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

bot.run('YOUR_TOKEN')
