from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

class VerificationRecord(Base):
    """Stores member verification records"""
    __tablename__ = 'verification_records'
    
    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False, unique=True)
    username = Column(String(255), nullable=False)
    verified = Column(Boolean, default=False)
    verification_date = Column(DateTime, nullable=True)
    failed_attempts = Column(Integer, default=0)
    last_attempt = Column(DateTime, nullable=True)
    on_cooldown = Column(Boolean, default=False)
    blacklisted = Column(Boolean, default=False)
    whitelisted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class VerificationLog(Base):
    """Stores verification events for audit logging"""
    __tablename__ = 'verification_logs'
    
    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    username = Column(String(255), nullable=False)
    event_type = Column(String(50), nullable=False)  # success, fail, timeout, manual_verify, unverify, blacklist
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ServerConfig(Base):
    """Stores per-server configuration"""
    __tablename__ = 'server_config'
    
    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, nullable=False, unique=True)
    verify_channel_id = Column(Integer, nullable=True)
    verify_role_id = Column(Integer, nullable=True)
    unverified_role_id = Column(Integer, nullable=True)
    log_channel_id = Column(Integer, nullable=True)
    verification_enabled = Column(Boolean, default=True)
    raid_mode_enabled = Column(Boolean, default=False)
    verification_locked = Column(Boolean, default=False)
    captcha_timeout = Column(Integer, default=300)
    captcha_max_attempts = Column(Integer, default=5)
    captcha_cooldown = Column(Integer, default=30)
    anti_raid_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RaidLog(Base):
    """Stores raid-related events"""
    __tablename__ = 'raid_logs'
    
    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    username = Column(String(255), nullable=False)
    event_type = Column(String(50), nullable=False)  # multiple_failures, suspicious_join, raid_mode_triggered
    timestamp = Column(DateTime, default=datetime.utcnow)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
