import asyncpg
from data.config import config


class Database:
    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def create_pool(self):
        self.pool = await asyncpg.create_pool(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            min_size=1,
            max_size=10,
        )

    async def close_pool(self):
        if self.pool:
            await self.pool.close()

    async def execute(
        self,
        query: str,
        *args,
        fetch: bool = False,
        fetchrow: bool = False,
        fetchval: bool = False,
    ):
        async with self.pool.acquire() as connection:
            connection: asyncpg.Connection
            if fetch:
                result = await connection.fetch(query, *args)
            elif fetchrow:
                result = await connection.fetchrow(query, *args)
            elif fetchval:
                result = await connection.fetchval(query, *args)
            else:
                result = await connection.execute(query, *args)
            return result

    async def create_tables(self):
        await self._create_table_movies()
        await self._create_table_users()
        await self._create_table_required_channels()
        await self._create_table_join_requests()

    async def _create_table_movies(self):
        """
        Barcha kinolar va serial qismlari shu bitta jadvalda:
        - Oddiy kino: episode_number = NULL
        - Serial qismlari: episode_number = 1, 2, 3...
        - archive_caption: arxiv kanalga yuboriladigan caption
        - user_caption: foydalanuvchiga yuboriladigan caption
        """
        query = """
        CREATE TABLE IF NOT EXISTS movies (
            id SERIAL PRIMARY KEY,
            code VARCHAR(50) NOT NULL,
            episode_number INTEGER DEFAULT NULL,
            archive_caption TEXT,
            user_caption TEXT,
            file_id TEXT NOT NULL,
            file_type VARCHAR(20) NOT NULL,
            added_by BIGINT,
            added_date TIMESTAMP DEFAULT NOW(),
            UNIQUE(code, episode_number)
        );
        """
        await self.execute(query)

    async def _create_table_users(self):
        query = """
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            full_name VARCHAR(255),
            joined_date TIMESTAMP DEFAULT NOW()
        );
        """
        await self.execute(query)

    async def _create_table_required_channels(self):
        query = """
        CREATE TABLE IF NOT EXISTS required_channels (
            id SERIAL PRIMARY KEY,
            channel_id BIGINT UNIQUE NOT NULL,
            channel_username VARCHAR(255),
            channel_name VARCHAR(255)
        );
        """
        await self.execute(query)

    async def _create_table_join_requests(self):
        query = """
        CREATE TABLE IF NOT EXISTS join_requests (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            channel_id BIGINT NOT NULL,
            requested_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, channel_id)
        );
        """
        await self.execute(query)


db = Database()