import logging
import discord
from discord.ext import tasks
from bot.utils.library_api import login_and_get_cookie, get_book_issue_info

# Registered users
registered_users = {
    "BIKASH": {
        "username": "078BEI010",
        "password": "078BEI010",
        "user_id": "748162601237872682",
        "notified": False,
    },
}


# Background task to check due dates daily
@tasks.loop(hours=24)
async def check_due_dates(bot):
    logging.info("Starting daily due date check...")
    for user, data in registered_users.items():
        password = data["password"]
        username = data["username"]
        user_id = data["user_id"]
        session_cookie = login_and_get_cookie(username, password)

        if session_cookie:
            library_details = get_book_issue_info(session_cookie)
            if library_details:
                for book in library_details:
                    try:
                        # Extract the number of days from the "Over Due" field
                        over_due_days = int(book["Over Due"].split()[0])
                    except (KeyError, ValueError, IndexError) as e:
                        logging.error(
                            f"Error parsing 'Over Due' field for user {username}: {e}"
                        )
                        continue

                    # Check if the book is due in 3 days or less
                    if -3 <= over_due_days <= 0 and not data["notified"]:
                        try:
                            user = await bot.fetch_user(user_id)
                            await user.send(
                                f"📚 **Library Due Date Alert**\n"
                                f"Your book **{book['Title']}** is due in **{abs(over_due_days)} days** (Due Date: {book['Return Date']}).\n"
                                f"Please return or renew it soon!"
                            )
                            logging.info(
                                f"Notification sent to user {user_id} for book {book['Title']}."
                            )
                        except discord.errors.DiscordException as e:
                            logging.error(
                                f"Failed to send notification to user {user_id}: {e}"
                            )
            data["notified"] = True

    # Reset the "notified" flag for all users at the end of the day
    for data in registered_users.values():
        data["notified"] = False
    logging.info("Daily due date check completed.")
