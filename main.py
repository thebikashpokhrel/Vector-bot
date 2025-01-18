from bot.bot import bot, load_extensions
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()


async def main():
    # Load the extensions (cogs)
    await load_extensions()

    # Start the bot
    await bot.start(os.getenv("BOT_TOKEN"))


# Run the bot
asyncio.run(main())
