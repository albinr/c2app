import os
import logging
from quart import Quart
from quart_auth import QuartAuth
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import async_engine, Base, AsyncSession, User
from config import Config
from routes import routes

app = Quart(__name__)
app.config.from_object(Config)

auth_manager = QuartAuth(app)


if not os.path.exists('logs'):
    os.makedirs('logs')

# verify/check if logging is async!!!!
logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('logs/server.log')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.before_serving
async def startup():
    await init_db()

app.register_blueprint(routes)

if __name__ == '__main__':
    import asyncio
    import hypercorn.asyncio
    from hypercorn.config import Config as HyperConfig

    async def run():
        config = HyperConfig()
        config.bind = ["0.0.0.0:5000"]
        
        await hypercorn.asyncio.serve(app, config)

    asyncio.run(run())
