from bot.bot import bot, load_extensions
import os
from dotenv import load_dotenv
import asyncio
import threading
import uvicorn

# To keep the bot alive since I am hosting it in the render haha
from server.main import app


def run_fastapi():
    """Run the FastAPI server on port 8000."""
    uvicorn.run(app, host="0.0.0.0", port=8001)


# Load environment variables
load_dotenv()


async def main():
    # Load the extensions (cogs)
    await load_extensions()

    # Start the bot
    await bot.start(os.getenv("BOT_TOKEN"))


# Start the FastAPI server in a separate thread
fastapi_thread = threading.Thread(target=run_fastapi)
fastapi_thread.daemon = (
    True  # Daemonize the thread so it exits when the main program exits
)
fastapi_thread.start()

# Run the bot
asyncio.run(main())
