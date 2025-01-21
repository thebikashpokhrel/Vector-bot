from discord.ext import commands
from discord import app_commands
import discord
from bot.utils.google_auth import get_credentials, delete_token
from bot.utils.classroom_api import list_classrooms, list_announcements


class ClassroomCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Login to Google Classroom
    @app_commands.command(
        name="login", description="Authorize access to Google Classroom"
    )
    async def login(self, interaction: discord.Interaction):
        client_id = str(interaction.user.id)

        try:
            await interaction.response.defer()  # To avoid interaction timeout
            data = get_credentials(client_id)

            # Check if the response contains an auth_url
            if isinstance(data, dict) and "auth_url" in data:
                await interaction.followup.send(
                    f"Please authorize the app by visiting this link: {data['auth_url']}"
                )
            elif isinstance(data, dict) and "error" in data:
                await interaction.followup.send(data["error"])
            else:
                await interaction.followup.send(
                    "Already authorized Google Classroom access!"
                )

        except Exception as e:
            await interaction.followup.send(f"Failed to authorize: {e}")

    # Logout of Google Classroom
    @app_commands.command(
        name="logout", description="Revoke access to Google Classroom"
    )
    async def logout(self, interaction: discord.Interaction):
        client_id = str(interaction.user.id)

        try:
            await interaction.response.defer()  # To avoid interaction timeout
            res = delete_token(client_id)

            # Check if the response contains an error
            if isinstance(res, dict) and "error" in res:
                await interaction.followup.send(res["error"])
            else:
                await interaction.followup.send(
                    "Successfully revoked Google Classroom access."
                )

        except Exception as e:
            await interaction.followup.send(f"Failed to revoke access: {e}")

    # List all the Google Classrooms
    @app_commands.command(
        name="classrooms", description="Get the list of your Google Classrooms"
    )
    async def classrooms(self, interaction: discord.Interaction):
        client_id = str(interaction.user.id)

        try:
            await interaction.response.defer()  # To avoid interaction timeout
            courses = list_classrooms(client_id)

            # Check if the user needs to authorize first
            if isinstance(courses, dict) and "error" in courses:
                await interaction.followup.send(courses["error"])
                return

            # Check if no classrooms were found
            if not courses:
                await interaction.followup.send("No classrooms found.")
                return

            # Format the list of classrooms
            classrooms_list = "\n".join(
                [f"- {course['name']} (ID: {course['id']})" for course in courses]
            )
            await interaction.followup.send(
                f"Your Google Classrooms:\n{classrooms_list}"
            )

        except Exception as e:
            await interaction.followup.send(f"Failed to fetch classrooms: {e}")

    # Get the top 3 announcements for a specific Google Classroom
    @app_commands.command(
        name="classroom_announcements",
        description="Get the top 3 announcements for a specific Google Classroom",
    )
    @app_commands.describe(course_id="The ID of the Google Classroom course")
    async def classroom_announcements(
        self, interaction: discord.Interaction, course_id: str
    ):
        client_id = str(interaction.user.id)

        try:
            await interaction.response.defer()  # Defer the response to avoid timeout
            announcements = list_announcements(course_id, client_id)

            # Check if the response contains an error
            if isinstance(announcements, dict) and "error" in announcements:
                await interaction.followup.send(announcements["error"])
                return

            # Check if no announcements were found
            if not announcements:
                await interaction.followup.send(
                    f"No announcements found for course {course_id}."
                )
                return

            # Format the list of announcements
            announcements_list = "\n\n".join(
                [
                    f"**Title**: {ann['title']}\n"
                    f"**Description**:{ann["description"] if ann['description'] else 'No description'}\n"
                    f"**Content**: {ann['content'] if ann['content'] else 'No content'}\n"
                    f"**Posted On**: {ann['posted_date']}\n"
                    for ann in announcements
                ]
            )

            await interaction.followup.send(
                f"Top 3 Announcements for Course {course_id}:\n{announcements_list}"
            )

        except Exception as e:
            await interaction.followup.send(
                "Failed to fetch announcements. Please try again later."
            )


async def setup(bot):
    await bot.add_cog(ClassroomCog(bot))
