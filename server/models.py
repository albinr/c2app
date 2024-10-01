from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from flask_bcrypt import Bcrypt
from flask_login import UserMixin

bcrypt = Bcrypt()

Base = declarative_base()

DATABASE_URL = "sqlite+aiosqlite:///sqlite.db"
async_engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

class Device(Base):
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True)
    hardware_id = Column(String(200), nullable=False, index=True, unique=True)
    device_name = Column(String(50), nullable=False)
    os_version = Column(String(100), nullable=False)
    geo_location = Column(String(100))
    installed_apps = Column(Text)
    timestamp = Column(DateTime, default=func.current_timestamp())
    last_heartbeat = Column(DateTime)

    def __repr__(self):
        return f"<Device {self.device_name}>"

class User(Base, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(150), nullable=False)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
