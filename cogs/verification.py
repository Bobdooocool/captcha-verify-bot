import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from captcha_generator import CaptchaGenerator
from db import SessionLocal, VerificationRecord, VerificationLog, ServerConfig, RaidLog
from config import CAPTCHA_LENGTH, CAPTCHA_TIMEOUT, CAPTCHA_MAX_ATTEMPTS, CAPTCHA_COOLDOWN
import logging

logger = logging.getLogger(__name__)

class VerificationView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=CAPTCHA_TIMEOUT)
        self.cog = cog
    
    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green)
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.start_verification(interaction)
    
    @discord.ui.button(label="Get Help", style=discord.ButtonStyle.blurple)
    async def help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Verification Help",
            description="Complete the captcha challenge to verify your identity",
            color=discord.Color.blue()
        )
        embed.add_field(name="How it works", value="1. Click the Verify button\n2. Solve the captcha\n3. Get verified!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.captcha_gen = CaptchaGenerator(length=CAPTCHA_LENGTH)
        self.active_captchas = {}  # {user_id: (captcha_text, timestamp)}
    
    async def start_verification(self, interaction: discord.Interaction):
        """Start captcha verification process"""
        db = SessionLocal()
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        
        try:
            # Check if user is already verified
            record = db.query(VerificationRecord).filter_by(user_id=user_id, guild_id=guild_id).first()
            
            if record and record.verified:
                embed = discord.Embed(
                    title="Already Verified",
                    description="You are already verified!",
                    color=discord.Color.green()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if user is blacklisted
            if record and record.blacklisted:
                embed = discord.Embed(
                    title="Verification Blocked",
                    description="You are not allowed to verify on this server.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                await self.log_event(guild_id, user_id, str(interaction.user), "blocked_attempt", "User attempted verification while blacklisted")
                return
            
            # Check cooldown
            if record and record.on_cooldown:
                cooldown_end = record.last_attempt + timedelta(seconds=CAPTCHA_COOLDOWN)
                remaining = (cooldown_end - datetime.utcnow()).total_seconds()
                if remaining > 0:
                    embed = discord.Embed(
                        title="On Cooldown",
                        description=f"Please wait {int(remaining)} seconds before trying again.",
                        color=discord.Color.orange()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
            
            # Generate captcha
            captcha_text, captcha_image = self.captcha_gen.generate_with_image()
            
            # Store active captcha
            self.active_captchas[user_id] = (captcha_text, datetime.utcnow())
            
            # Send captcha image
            file = discord.File(captcha_image, filename="captcha.png")
            embed = discord.Embed(
                title="Captcha Verification",
                description=f"Enter the text from the image below. You have {CAPTCHA_TIMEOUT} seconds.",
                color=discord.Color.blurple()
            )
            embed.set_image(url="attachment://captcha.png")
            
            await interaction.response.send_message(embed=embed, file=file, ephemeral=True)
            
            # Wait for captcha response
            def check(msg):
                return msg.author.id == user_id and msg.guild is None
            
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=CAPTCHA_TIMEOUT)
                await self.verify_captcha(interaction, msg.content, user_id, guild_id, db)
            except:
                await self.handle_captcha_timeout(user_id, guild_id, db)
                
        except Exception as e:
            logger.error(f"Error in start_verification: {e}")
            await interaction.followup.send("An error occurred during verification.", ephemeral=True)
        finally:
            db.close()
    
    async def verify_captcha(self, interaction: discord.Interaction, user_input: str, user_id: int, guild_id: int, db):
        """Verify captcha answer"""
        if user_id not in self.active_captchas:
            embed = discord.Embed(
                title="Captcha Expired",
                description="Your captcha has expired. Please try again.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        captcha_text, timestamp = self.active_captchas[user_id]
        
        # Check timeout
        if (datetime.utcnow() - timestamp).total_seconds() > CAPTCHA_TIMEOUT:
            del self.active_captchas[user_id]
            await self.handle_captcha_timeout(user_id, guild_id, db)
            return
        
        # Check answer
        if user_input.upper() == captcha_text:
            del self.active_captchas[user_id]
            await self.mark_verified(interaction, user_id, guild_id, db)
        else:
            await self.handle_failed_attempt(user_id, guild_id, db)
    
    async def mark_verified(self, interaction: discord.Interaction, user_id: int, guild_id: int, db):
        """Mark user as verified"""
        try:
            # Update database
            record = db.query(VerificationRecord).filter_by(user_id=user_id, guild_id=guild_id).first()
            if not record:
                record = VerificationRecord(
                    guild_id=guild_id,
                    user_id=user_id,
                    username=str(interaction.user),
                    verified=True,
                    verification_date=datetime.utcnow()
                )
                db.add(record)
            else:
                record.verified = True
                record.verification_date = datetime.utcnow()
                record.failed_attempts = 0
                record.on_cooldown = False
            
            db.commit()
            
            # Assign verified role
            config = db.query(ServerConfig).filter_by(guild_id=guild_id).first()
            if config and config.verify_role_id:
                role = interaction.guild.get_role(config.verify_role_id)
                if role:
                    await interaction.user.add_roles(role)
            
            # Remove unverified role
            if config and config.unverified_role_id:
                role = interaction.guild.get_role(config.unverified_role_id)
                if role:
                    try:
                        await interaction.user.remove_roles(role)
                    except:
                        pass
            
            # Send success message
            embed = discord.Embed(
                title="Verification Successful",
                description="You have been verified!",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Log event
            await self.log_event(guild_id, user_id, str(interaction.user), "success", None)
            
        except Exception as e:
            logger.error(f"Error marking user verified: {e}")
    
    async def handle_failed_attempt(self, user_id: int, guild_id: int, db):
        """Handle failed captcha attempt"""
        try:
            record = db.query(VerificationRecord).filter_by(user_id=user_id, guild_id=guild_id).first()
            if not record:
                record = VerificationRecord(
                    guild_id=guild_id,
                    user_id=user_id,
                    username="Unknown",
                    failed_attempts=1
                )
                db.add(record)
            else:
                record.failed_attempts += 1
                record.last_attempt = datetime.utcnow()
            
            # Apply cooldown if max attempts exceeded
            if record.failed_attempts >= CAPTCHA_MAX_ATTEMPTS:
                record.on_cooldown = True
                record.last_attempt = datetime.utcnow()
                await self.log_event(guild_id, user_id, "Unknown", "max_attempts_exceeded", f"Failed attempts: {record.failed_attempts}")
            else:
                await self.log_event(guild_id, user_id, "Unknown", "failed_attempt", f"Failed attempts: {record.failed_attempts}")
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error handling failed attempt: {e}")
    
    async def handle_captcha_timeout(self, user_id: int, guild_id: int, db):
        """Handle captcha timeout"""
        if user_id in self.active_captchas:
            del self.active_captchas[user_id]
        
        await self.log_event(guild_id, user_id, "Unknown", "timeout", "Captcha expired")
    
    async def log_event(self, guild_id: int, user_id: int, username: str, event_type: str, details: str):
        """Log verification event"""
        db = SessionLocal()
        try:
            log = VerificationLog(
                guild_id=guild_id,
                user_id=user_id,
                username=username,
                event_type=event_type,
                details=details
            )
            db.add(log)
            db.commit()
        finally:
            db.close()

async def setup(bot):
    await bot.add_cog(Verification(bot))
