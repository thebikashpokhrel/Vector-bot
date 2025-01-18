from bot.utils.library_api import (
    login_and_get_cookie,
    get_book_issue_info,
    format_book_issue_data,
)
from discord.ext import commands
from discord import app_commands
import discord


class LibraryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="library", description="Get the details of your library books"
    )
    async def library(self, interaction: discord.Interaction, username: str):
        """A slash command to fetch and display library book details."""
        session_cookie = login_and_get_cookie(username, username)

        if session_cookie:
            book_issue_data = get_book_issue_info(session_cookie)
            if book_issue_data:
                await interaction.response.send_message(
                    format_book_issue_data(book_issue_data)
                )
            else:
                await interaction.response.send_message(
                    "No book issue information received."
                )
        else:
            await interaction.response.send_message(
                f"Incorrect username. {username} is not a correct username"
            )


# Setup function (must be at the module level)
async def setup(bot):
    await bot.add_cog(LibraryCog(bot))
