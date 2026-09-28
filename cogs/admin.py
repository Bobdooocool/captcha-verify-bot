import discord
from discord import app_commands
from discord.ext import commands
from db import SessionLocal, ServerConfig, VerificationRecord, VerificationLog, RaidLog
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # SETUP COMMANDS
    
    @app_commands.command(name="setup-verification")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_verification(self, interaction: discord.Interaction):
        """Setup verification system for the server"""
        await interaction.response.defer()
        
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            
            # Check if already configured
            config = db.query(ServerConfig).filter_by(guild_id=guild_id).first()
            if not config:
                config = ServerConfig(guild_id=guild_id)
                db.add(config)
            
            # Create verification channel
            verify_channel = await interaction.guild.create_text_channel("verify")
            config.verify_channel_id = verify_channel.id
            
            # Create verified role
            verified_role = await interaction.guild.create_role(name="Verified")
            config.verify_role_id = verified_role.id
            
            # Create unverified role
            unverified_role = await interaction.guild.create_role(name="Unverified")
            config.unverified_role_id = unverified_role.id
            
            # Create log channel
            log_channel = await interaction.guild.create_text_channel("verification-logs")
            config.log_channel_id = log_channel.id
            
            db.commit()
            
            # Send verification panel to verify channel
            from cogs.verification import VerificationView
            embed = discord.Embed(
                title="Server Verification",
                description="Click the button below to verify and access the server.",
                color=discord.Color.green()
            )
            view = VerificationView(self.bot.get_cog("Verification"))
            await verify_channel.send(embed=embed, view=view)
            
            embed = discord.Embed(
                title="Setup Complete",
                description=f"Verification system has been set up!\n\n✅ Verify Channel: {verify_channel.mention}\n✅ Verified Role: {verified_role.mention}\n✅ Unverified Role: {unverified_role.mention}\n✅ Log Channel: {log_channel.mention}",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in setup_verification: {e}")
            await interaction.followup.send(f"Error during setup: {str(e)}")
        finally:
            db.close()
    
    @app_commands.command(name="set-verify-channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_verify_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the verification channel"""
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            config = db.query(ServerConfig).filter_by(guild_id=guild_id).first()
            
            if not config:
                config = ServerConfig(guild_id=guild_id)
                db.add(config)
            
            config.verify_channel_id = channel.id
            db.commit()
            
            embed = discord.Embed(
                title="Channel Updated",
                description=f"Verification channel set to {channel.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        finally:
            db.close()
    
    @app_commands.command(name="set-verified-role")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_verified_role(self, interaction: discord.Interaction, role: discord.Role):
        """Set the verified role"""
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            config = db.query(ServerConfig).filter_by(guild_id=guild_id).first()
            
            if not config:
                config = ServerConfig(guild_id=guild_id)
                db.add(config)
            
            config.verify_role_id = role.id
            db.commit()
            
            embed = discord.Embed(
                title="Role Updated",
                description=f"Verified role set to {role.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        finally:
            db.close()
    
    @app_commands.command(name="set-unverified-role")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_unverified_role(self, interaction: discord.Interaction, role: discord.Role):
        """Set the unverified role"""
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            config = db.query(ServerConfig).filter_by(guild_id=guild_id).first()
            
            if not config:
                config = ServerConfig(guild_id=guild_id)
                db.add(config)
            
            config.unverified_role_id = role.id
            db.commit()
            
            embed = discord.Embed(
                title="Role Updated",
                description=f"Unverified role set to {role.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        finally:
            db.close()
    
    @app_commands.command(name="set-log-channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_log_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the verification log channel"""
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            config = db.query(ServerConfig).filter_by(guild_id=guild_id).first()
            
            if not config:
                config = ServerConfig(guild_id=guild_id)
                db.add(config)
            
            config.log_channel_id = channel.id
            db.commit()
            
            embed = discord.Embed(
                title="Log Channel Updated",
                description=f"Log channel set to {channel.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        finally:
            db.close()
    
    # VERIFICATION CONTROL COMMANDS
    
    @app_commands.command(name="verification-enable")
    @app_commands.checks.has_permissions(administrator=True)
    async def verification_enable(self, interaction: discord.Interaction):
        """Enable verification"""
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            config = db.query(ServerConfig).filter_by(guild_id=guild_id).first()
            
            if not config:
                config = ServerConfig(guild_id=guild_id)
                db.add(config)
            
            config.verification_enabled = True
            db.commit()
            
            embed = discord.Embed(
                title="Verification Enabled",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        finally:
            db.close()
    
    @app_commands.command(name="verification-disable")
    @app_commands.checks.has_permissions(administrator=True)
    async def verification_disable(self, interaction: discord.Interaction):
        """Disable verification"""
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            config = db.query(ServerConfig).filter_by(guild_id=guild_id).first()
            
            if not config:
                config = ServerConfig(guild_id=guild_id)
                db.add(config)
            
            config.verification_enabled = False
            db.commit()
            
            embed = discord.Embed(
                title="Verification Disabled",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)
        finally:
            db.close()
    
    @app_commands.command(name="lock-verification")
    @app_commands.checks.has_permissions(administrator=True)
    async def lock_verification(self, interaction: discord.Interaction):
        """Lock verification (pause all attempts)"""
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            config = db.query(ServerConfig).filter_by(guild_id=guild_id).first()
            
            if not config:
                config = ServerConfig(guild_id=guild_id)
                db.add(config)
            
            config.verification_locked = True
            db.commit()
            
            embed = discord.Embed(
                title="Verification Locked",
                description="Verification is now locked. New verification attempts are paused.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
        finally:
            db.close()
    
    @app_commands.command(name="unlock-verification")
    @app_commands.checks.has_permissions(administrator=True)
    async def unlock_verification(self, interaction: discord.Interaction):
        """Unlock verification"""
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            config = db.query(ServerConfig).filter_by(guild_id=guild_id).first()
            
            if not config:
                config = ServerConfig(guild_id=guild_id)
                db.add(config)
            
            config.verification_locked = False
            db.commit()
            
            embed = discord.Embed(
                title="Verification Unlocked",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        finally:
            db.close()
    
    # MEMBER MANAGEMENT COMMANDS
    
    @app_commands.command(name="verify-member")
    @app_commands.checks.has_permissions(administrator=True)
    async def verify_member(self, interaction: discord.Interaction, member: discord.Member):
        """Manually verify a member"""
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            user_id = member.id
            
            record = db.query(VerificationRecord).filter_by(user_id=user_id, guild_id=guild_id).first()
            if not record:
                record = VerificationRecord(
                    guild_id=guild_id,
                    user_id=user_id,
                    username=str(member),
                    verified=True,
                    verification_date=datetime.utcnow()
                )
                db.add(record)
            else:
                record.verified = True
                record.verification_date = datetime.utcnow()
            
            db.commit()
            
            # Assign role
            config = db.query(ServerConfig).filter_by(guild_id=guild_id).first()
            if config and config.verify_role_id:
                role = interaction.guild.get_role(config.verify_role_id)
                if role:
                    await member.add_roles(role)
            
            embed = discord.Embed(
                title="Member Verified",
                description=f"{member.mention} has been manually verified.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        finally:
            db.close()
    
    @app_commands.command(name="unverify-member")
    @app_commands.checks.has_permissions(administrator=True)
    async def unverify_member(self, interaction: discord.Interaction, member: discord.Member):
        """Remove verification from a member"""
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            user_id = member.id
            
            record = db.query(VerificationRecord).filter_by(user_id=user_id, guild_id=guild_id).first()
            if record:
                record.verified = False
                db.commit()
            
            # Remove role
            config = db.query(ServerConfig).filter_by(guild_id=guild_id).first()
            if config and config.verify_role_id:
                role = interaction.guild.get_role(config.verify_role_id)
                if role:
                    try:
                        await member.remove_roles(role)
                    except:
                        pass
            
            embed = discord.Embed(
                title="Member Unverified",
                description=f"{member.mention} verification has been removed.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)
        finally:
            db.close()
    
    @app_commands.command(name="verification-blacklist")
    @app_commands.checks.has_permissions(administrator=True)
    async def verification_blacklist(self, interaction: discord.Interaction, member: discord.Member):
        """Blacklist a member from verification"""
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            user_id = member.id
            
            record = db.query(VerificationRecord).filter_by(user_id=user_id, guild_id=guild_id).first()
            if not record:
                record = VerificationRecord(
                    guild_id=guild_id,
                    user_id=user_id,
                    username=str(member),
                    blacklisted=True
                )
                db.add(record)
            else:
                record.blacklisted = True
            
            db.commit()
            
            embed = discord.Embed(
                title="Member Blacklisted",
                description=f"{member.mention} can no longer verify.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
        finally:
            db.close()
    
    @app_commands.command(name="verification-whitelist")
    @app_commands.checks.has_permissions(administrator=True)
    async def verification_whitelist(self, interaction: discord.Interaction, member: discord.Member):
        """Whitelist a member (trust bypass)"""
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            user_id = member.id
            
            record = db.query(VerificationRecord).filter_by(user_id=user_id, guild_id=guild_id).first()
            if not record:
                record = VerificationRecord(
                    guild_id=guild_id,
                    user_id=user_id,
                    username=str(member),
                    whitelisted=True,
                    verified=True
                )
                db.add(record)
            else:
                record.whitelisted = True
                record.verified = True
            
            db.commit()
            
            embed = discord.Embed(
                title="Member Whitelisted",
                description=f"{member.mention} has been whitelisted.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        finally:
            db.close()
    
    # LOGGING COMMANDS
    
    @app_commands.command(name="verification-logs")
    @app_commands.checks.has_permissions(administrator=True)
    async def verification_logs(self, interaction: discord.Interaction, limit: int = 10):
        """View recent verification logs"""
        await interaction.response.defer()
        
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            logs = db.query(VerificationLog).filter_by(guild_id=guild_id).order_by(VerificationLog.timestamp.desc()).limit(limit).all()
            
            if not logs:
                embed = discord.Embed(
                    title="No Logs",
                    description="No verification logs found.",
                    color=discord.Color.greyple()
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="Verification Logs",
                color=discord.Color.blurple()
            )
            
            for log in logs:
                timestamp = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                embed.add_field(
                    name=f"{log.username} - {log.event_type.upper()}",
                    value=f"`{timestamp}`\n{log.details or 'No details'}",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
        finally:
            db.close()
    
    @app_commands.command(name="verification-stats")
    @app_commands.checks.has_permissions(administrator=True)
    async def verification_stats(self, interaction: discord.Interaction):
        """View verification statistics"""
        await interaction.response.defer()
        
        db = SessionLocal()
        try:
            guild_id = interaction.guild.id
            
            total = db.query(VerificationRecord).filter_by(guild_id=guild_id).count()
            verified = db.query(VerificationRecord).filter_by(guild_id=guild_id, verified=True).count()
            failed = db.query(VerificationLog).filter_by(guild_id=guild_id, event_type="failed_attempt").count()
            blacklisted = db.query(VerificationRecord).filter_by(guild_id=guild_id, blacklisted=True).count()
            
            embed = discord.Embed(
                title="Verification Statistics",
                color=discord.Color.blurple()
            )
            embed.add_field(name="Total Members", value=str(total))
            embed.add_field(name="Verified", value=str(verified))
            embed.add_field(name="Failed Attempts", value=str(failed))
            embed.add_field(name="Blacklisted", value=str(blacklisted))
            
            await interaction.followup.send(embed=embed)
        finally:
            db.close()

async def setup(bot):
    await bot.add_cog(Admin(bot))
