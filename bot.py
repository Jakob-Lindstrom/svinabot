# bot.py

import discord
from discord.ext import commands
import logging
import asyncio
from config import DISCORD_TOKEN, INITIAL_EXTENSIONS
from utils.logger import setup_logger

# Setup logging
setup_logger()

# Define intents for the bot
intents = discord.Intents.default()
intents.message_content = True 

# Create the bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

# Load extensions asynchronously
async def load_extensions():
    for extension in INITIAL_EXTENSIONS:
        try:
            await bot.load_extension(extension)
            logging.info(f'Loaded extension {extension}')
        except Exception as e:
            logging.error(f'Failed to load extension {extension}: {e}')

# Event: on_ready
@bot.event
async def on_ready():
    logging.info(f"Loaded extensions: {list(bot.extensions.keys())}")
    logging.info(f"Registered commands: {[cmd.name for cmd in bot.commands]}")
    logging.info(f"Bot connected as {bot.user}")

# Main function to run the bot
async def main():
    async with bot:
        await load_extensions()
        await bot.start(DISCORD_TOKEN)

# Run the main function
if __name__ == '__main__':
    asyncio.run(main())
