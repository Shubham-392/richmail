import asyncio
from mysql.connector.aio import connect
from contextlib import asynccontextmanager

from .settings import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

class AsyncMySQLConnectionPool:
    def __init__(self, pool_size, **db_config):
        self._pool_size = pool_size
        self._db_config = db_config
        self._pool = asyncio.Queue()
        self._connections = []
        self._connection_count = 0  # Track live connections

    async def get_connection(self):
            """Get a connection from the pool."""
            # See if there is an immediately available connection:
            try:
                conn = self._pool.get_nowait()
            except asyncio.QueueEmpty:
                pass
            else:
                return conn

            # Here if there are no immediately available pool connections
            if self._connection_count < self._pool_size:
                # We must increment first since we might have a task switch
                # trying to acquire a new connectionL
                self._connection_count += 1
                conn = await connect(**self._db_config)
                self._connections.append(conn)
                return conn

            # pool size is at its maximum size, so we may have to
            # wait a while:
            return await self._pool.get()

    @asynccontextmanager
    async def get_db_connection(self):
        conn = await self.get_connection()
        try:
            yield conn
        except Exception as e :
            print(f'Error: {str(e)}')
        finally:
            await self.release_connection(conn)


    async def release_connection(self, conn):
            """Returns a connection to the pool."""
            # But first do a rollback:
            await conn.rollback()
            await conn.cmd_reset_connection()
            await self._pool.put(conn)

    async def close(self):
            """Closes all connections in the pool."""

            # Empty the pool of any connections that have been returned.
            # Ideally, this should be all the connections.
            while not self._pool.empty():
                self._pool.get_nowait()

            # Now shutdown all of the connections
            while self._connections:
                conn = self._connections.pop()
                self._connection_count -= 1
                # close() can and usually does result in stack traces being
                # printed on stderr even though no exception is raised. Better
                # to use shutdown, which does not try to send a QUIT command:
                await conn.shutdown()



pool = AsyncMySQLConnectionPool(
        pool_size=6,
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
)
