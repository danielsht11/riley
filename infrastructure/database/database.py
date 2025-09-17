import asyncpg
import logging
from typing import Optional, List, Any
from contextlib import asynccontextmanager

from core.config.settings import settings


class DatabaseClient:
    """PostgreSQL database client for the Voice Agent system."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Create the async connection pool."""
        if self._pool is not None:
            return
        try:
            self._pool = await asyncpg.create_pool(
                host=settings.database_host,
                port=settings.database_port,
                user=settings.database_user,
                password=settings.database_password,
                database=settings.database_name,
                min_size=1,
                max_size=10,
            )
            self.logger.info("✅ Database connection pool created successfully")
        except Exception as error:
            self.logger.error(f"❌ Failed to create database connection pool: {error}")
            raise

    async def disconnect(self) -> None:
        """Close the async connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            self.logger.info("🔌 Database connection pool closed")

    @asynccontextmanager
    async def get_connection(self):
        """Yield a connection from the pool."""
        if self._pool is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        async with self._pool.acquire() as connection:
            yield connection

    async def execute(self, query: str, *args) -> str:
        async with self.get_connection() as connection:
            return await connection.execute(query, *args)

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        async with self.get_connection() as connection:
            return await connection.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        async with self.get_connection() as connection:
            return await connection.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        async with self.get_connection() as connection:
            return await connection.fetchval(query, *args)

    async def execute_many(self, query: str, args_list: List[tuple]) -> None:
        async with self.get_connection() as connection:
            await connection.executemany(query, args_list)

    async def health_check(self) -> bool:
        try:
            result = await self.fetchval("SELECT 1")
            return result == 1
        except Exception as error:
            self.logger.error(f"Database health check failed: {error}")
            return False


# Singleton instance and helpers (FastAPI-style usage)
database_client = DatabaseClient()


async def init_db() -> None:
    """Initialize the global database client (called on app startup)."""
    await database_client.connect()


async def shutdown_db() -> None:
    """Shutdown the global database client (called on app shutdown)."""
    await database_client.disconnect()


async def get_db():
    """FastAPI dependency that yields a live connection.

    Usage:
        async def route(conn = Depends(get_db)):
            row = await conn.fetchrow("SELECT 1")
    """
    # Ensure pool exists even if init_db wasn't called for some reason
    if database_client._pool is None:
        await database_client.connect()
    async with database_client.get_connection() as connection:
        yield connection