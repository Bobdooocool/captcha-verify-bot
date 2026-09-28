import discord
from discord import app_commands
from discord.ext import commands
from db import SessionLocal, ServerConfig, RaidLog
from datetime import datetime, timedelta
from config import RAID_MODE_USER_THRESHOLD, RAID_MODE_TIME_WINDOW
import logging

logger = logging.getLogger(__name__)

class Security(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.join_history = {}  # {guild_id: [(user_id, timestamp)]}
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Track new members for raid detection"""
        guild_id = member.guild.id
        
        if guild_id not in self.join_history:
            self.join_history[guild_id] = []
        
        # Add join event
        self.join_history[guild_id].append((member.id, datetime.utcnow()))
        
        # Clean old entries (older than raid detection window)
        cutoff = datetime.utcnow() - timedelta(seconds=RAID_MODE_TIME_WINDOW)
        self.join_history[guild_id] = [
            (uid, ts) for uid, ts in self.join_history[guild_id]
            if ts > cutoff
        ]
        
        # Check if raid is happening
        if len(self.join_history[guild_id]) >= RAID_MODE_USER_THRESHOLD:
            await self.trigger_raid_mode(member.guild)
    
    async def trigger_raid_mode(self, guild: discord.Guild):
        """Activate raid mode"""
        db = SessionLocal()
        try:
            config = db.query(ServerConfig).filter_by(guild_id=guild.id).first()
            if not config:
                return
            
            if config.raid_mode_enabled:
                return  # Already in raid mode
            
            config.raid_mode_enabled = True
            config.verification_locked = True
            db.commit()
            
            logger.warning(f"Raid mode activated on {guild.name}")
            
            # Send alert
            if config.log_channel_id:
                channel = guild.get_channel(config.log_channel_id)
                if channel:
                    embed = discord.Embed(
                        title="🚨 RAID MODE ACTIVATED",
                        description="Suspicious join activity detected. Verification is locked.",
                        color=discord.Color.red()
                    )
                    await channel.send(embed=embed)
        finally:
            db.close()
    
    @app_commands.command(name="raid-mode")
    @app_commands.checks.has_permissions(administrator=True)
    async def raid_mode(self, interaction: discord.Interaction, enable: bool):
        """Manually toggle raid mode"""
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            config = db.query(ServerConfig).filter_by(guild_id=guild_id).first()
            
            if not config:
                config = ServerConfig(guild_id=guild_id)
                db.add(config)
            
            config.raid_mode_enabled = enable
            if enable:
                config.verification_locked = True
            db.commit()
            
            status = "ACTIVATED" if enable else "DEACTIVATED"
            embed = discord.Embed(
                title=f"Raid Mode {status}",
                color=discord.Color.red() if enable else discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        finally:
            db.close()
    
    @app_commands.command(name="security-settings")
    @app_commands.checks.has_permissions(administrator=True)
    async def security_settings(self, interaction: discord.Interaction):
        """View security settings"""
        await interaction.response.defer()
        
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            config = db.query(ServerConfig).filter_by(guild_id=guild_id).first()
            
            if not config:
                embed = discord.Embed(
                    title="No Configuration",
                    description="Run `/setup-verification` first.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="Security Settings",
                color=discord.Color.blue()
            )
            embed.add_field(name="Verification Enabled", value=str(config.verification_enabled))
            embed.add_field(name="Raid Mode", value=str(config.raid_mode_enabled))
            embed.add_field(name="Verification Locked", value=str(config.verification_locked))
            embed.add_field(name="Anti-Raid Enabled", value=str(config.anti_raid_enabled))
            embed.add_field(name="Captcha Timeout", value=f"{config.captcha_timeout}s")
            embed.add_field(name="Max Attempts", value=str(config.captcha_max_attempts))
            embed.add_field(name="Cooldown", value=f"{config.captcha_cooldown}s")
            
            await interaction.followup.send(embed=embed)
        finally:
            db.close()
    
    @app_commands.command(name="anti-raid")
    @app_commands.checks.has_permissions(administrator=True)
    async def anti_raid(self, interaction: discord.Interaction, enable: bool):
        """Enable/disable anti-raid protection"""
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            config = db.query(ServerConfig).filter_by(guild_id=guild_id).first()
            
            if not config:
                config = ServerConfig(guild_id=guild_id)
                db.add(config)
            
            config.anti_raid_enabled = enable
            db.commit()
            
            status = "ENABLED" if enable else "DISABLED"
            embed = discord.Embed(
                title=f"Anti-Raid {status}",
                color=discord.Color.green() if enable else discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)
        finally:
            db.close()
    
    @app_commands.command(name="security-alerts")
    @app_commands.checks.has_permissions(administrator=True)
    async def security_alerts(self, interaction: discord.Interaction, limit: int = 10):
        """View recent security alerts"""
        await interaction.response.defer()
        
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            alerts = db.query(RaidLog).filter_by(guild_id=guild_id).order_by(RaidLog.timestamp.desc()).limit(limit).all()
            
            if not alerts:
                embed = discord.Embed(
                    title="No Alerts",
                    description="No security alerts found.",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="Security Alerts",
                color=discord.Color.red()
            )
            
            for alert in alerts:
                timestamp = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                embed.add_field(
                    name=f"{alert.username} - {alert.event_type.upper()}",
                    value=f"`{timestamp}`",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
        finally:
            db.close()

async def setup(bot):
    await bot.add_cog(Security(bot))
