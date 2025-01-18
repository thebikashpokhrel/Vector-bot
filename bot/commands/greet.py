from discord.ext import commands
from discord import app_commands
import discord  # Import discord for Interaction


class GreetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="greet", description="Greet the user"
    )  # Slash command decorator
    async def greet(self, interaction: discord.Interaction):
        """A simple slash command that greets the user."""
        await interaction.response.send_message(f"Hello, {interaction.user.name}!")


# Setup function (must be at the module level)
async def setup(bot):
    await bot.add_cog(GreetCog(bot))
