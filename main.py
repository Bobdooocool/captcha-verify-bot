import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
from db import init_db
from config import DISCORD_TOKEN, LOG_LEVEL
import logging

# Setup logging
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    """Bot startup event"""
    logger.info(f"✅ Bot is online as {bot.user}")
    try:
        synced = await bot.tree.sync()
        logger.info(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")

async def load_cogs():
    """Load all cogs from cogs directory"""
    cogs_dir = "cogs"
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py"):
            cog_name = filename[:-3]
            try:
                await bot.load_extension(f"cogs.{cog_name}")
                logger.info(f"✅ Loaded cog: {cog_name}")
            except Exception as e:
                logger.error(f"❌ Failed to load cog {cog_name}: {e}")

async def main():
    """Main startup function"""
    # Initialize database
    init_db()
    logger.info("✅ Database initialized")
    
    # Load cogs
    await load_cogs()
    
    # Start bot
    try:
        await bot.start(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
