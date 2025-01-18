from discord.ext import commands
from discord import app_commands
import discord
from bot.utils.google_auth import (
    get_credentials,
    list_announcements_by_course,
    list_classrooms,
    delete_credentials,
)


class ClassroomCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="subscribe_classroom", description="Authorize access to Google Classroom"
    )
    async def subscribe_classroom(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        try:
            creds = get_credentials(user_id)
            await interaction.response.send_message(
                "Successfully authorized Google Classroom access!"
            )
        except Exception as e:
            if "refresh_token" in str(e):
                delete_credentials(user_id)
                await interaction.response.send_message(
                    "Credentials were invalid, please try authorizing again."
                )
            else:
                await interaction.response.send_message(f"Failed to authorize: {e}")

    @app_commands.command(
        name="classrooms", description="Get the list of your Google Classrooms"
    )
    async def classrooms(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        try:
            courses = list_classrooms(user_id)
            if not courses:
                await interaction.response.send_message("No classrooms found.")
                return

            classrooms_list = "\n".join(
                [f"- {course['name']} (ID: {course['id']})" for course in courses]
            )
            await interaction.response.send_message(
                f"Your Google Classrooms:\n{classrooms_list}"
            )
        except Exception as e:
            if "refresh_token" in str(e):
                delete_credentials(user_id)
                await interaction.response.send_message(
                    "Credentials were invalid, please try authorizing again."
                )
            else:
                await interaction.response.send_message(
                    f"Failed to fetch classrooms: {e}"
                )

    @app_commands.command(
        name="unsubscribe_classroom", description="Revoke access to Google Classroom"
    )
    async def unsubscribe_classroom(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        try:
            delete_credentials(user_id)
            await interaction.response.send_message(
                "Successfully revoked Google Classroom access."
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to revoke access: {e}")

    @app_commands.command(
        name="classroom_announcements",
        description="Get the top 3 announcements for a specific Google Classroom",
    )
    @app_commands.describe(course_id="The ID of the Google Classroom course")
    async def classroom_announcements(
        self, interaction: discord.Interaction, course_id: str
    ):
        user_id = str(interaction.user.id)

        try:
            announcements = list_announcements_by_course(course_id, user_id)
            if not announcements:
                await interaction.response.send_message(
                    f"No announcements found for course {course_id}."
                )
                return

            # Format the announcements for display
            announcements_list = "\n".join(
                [
                    f"**Title**: {ann['title']}\n"
                    f"**Content**: {ann['content'] if ann['content'] else 'No content'}\n"
                    f"**Posted On**: {ann['posted_date']}\n"
                    for ann in announcements
                ]
            )

            await interaction.response.send_message(
                f"Top 3 Announcements for Course {course_id}:\n{announcements_list}"
            )

        except Exception as e:
            await interaction.response.send_message(
                f"Failed to fetch announcements: {e}"
            )


async def setup(bot):
    await bot.add_cog(ClassroomCog(bot))
