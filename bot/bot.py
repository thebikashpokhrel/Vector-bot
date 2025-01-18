import discord
from discord.ext import commands
from bot.tasks.due_date_check import check_due_dates
from bot.utils.logging_setup import setup_logging

# Enable the message content intent
intents = discord.Intents.default()
intents.message_content = True

# Initialize the bot with a command prefix
bot = commands.Bot(command_prefix="$", intents=intents)

# Set up logging
setup_logging()


# Event: When the bot is ready
@bot.event
async def on_ready():
    print(f"Logged on as {bot.user}!")
    # Sync slash commands with Discord
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    # Start the background task
    check_due_dates.start(bot)


# Function to load extensions
async def load_extensions():
    await bot.load_extension("bot.commands.greet")
    await bot.load_extension("bot.commands.library")
    await bot.load_extension("bot.commands.classroom")
