import os
from dotenv import load_dotenv

load_dotenv()

# Discord Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_PREFIX = os.getenv('DISCORD_PREFIX', '/')
GUILD_ID = int(os.getenv('GUILD_ID', 0))

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./verification.db')

# Captcha Configuration
CAPTCHA_TIMEOUT = int(os.getenv('CAPTCHA_TIMEOUT', 300))
CAPTCHA_MAX_ATTEMPTS = int(os.getenv('CAPTCHA_MAX_ATTEMPTS', 5))
CAPTCHA_COOLDOWN = int(os.getenv('CAPTCHA_COOLDOWN', 30))
CAPTCHA_LENGTH = int(os.getenv('CAPTCHA_LENGTH', 6))

# Security Settings
ANTI_RAID_ENABLED = os.getenv('ANTI_RAID_ENABLED', 'true').lower() == 'true'
RAID_MODE_USER_THRESHOLD = int(os.getenv('RAID_MODE_USER_THRESHOLD', 10))
RAID_MODE_TIME_WINDOW = int(os.getenv('RAID_MODE_TIME_WINDOW', 60))

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Validation
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is required")

if GUILD_ID == 0:
    raise ValueError("GUILD_ID environment variable is required")
