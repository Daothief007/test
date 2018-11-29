import asyncio
import cx_Oracle
import os

import functools

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
class Pool:

    def __init__(self, loop, **DB_CONFIG):
        self._loop = loop
        self.db_config = DB_CONFIG
        pass

    def __await__(self):
        return self._init().__await__()

    async def _init(self):
        self._pool = await self._loop.run_in_executor(None, functools.partial(cx_Oracle.SessionPool,
                                                      self.db_config['user'], self.db_config['password'],
                                                      f"{self.db_config['host']}:{self.db_config['port']}/{self.db_config['sid']}", 2, 100, 1, threaded=True))
        # print(self._pool)
        return self

    def acquire(self, *, timeout=None):
        return PoolAcquireContext(self, timeout)

    async def _acquire(self, timeout):
        conn = await self._loop.run_in_executor(None, self._pool.acquire)
        return Connection(self._loop, conn)

    async def release(self, conn):
        await self._loop.run_in_executor(None, self._pool.release, conn)

class PoolAcquireContext:

    __slots__ = ('timeout', 'connection', 'done', 'pool')

    def __init__(self, pool, timeout):
        self.pool = pool
        self.timeout = timeout
        self.connection = None
        self.done = False

    async def __aenter__(self):
        if self.connection is not None or self.done:
            raise exceptions.InterfaceError('a connection is already acquired')
        self.connection = await self.pool._acquire(self.timeout)
        return self.connection

    async def __aexit__(self, *exc):
        self.done = True
        con = self.connection
        self.connection = None
        await self.pool.release(con._conn)



    def __await__(self):
        self.done = True
        return self.pool._acquire(self.timeout).__await__()


class Connection:
    def __init__(self, loop, conn):
        self._conn = conn
        self._loop = loop
        return

    async def cursor(self):
        return Cursor(self._loop, await self._loop.run_in_executor(None, self._conn.cursor))

    async def commit(self):
        return Cursor(self._loop, await self._loop.run_in_executor(None, self._conn.commit))

    async def close(self):
        return Cursor(self._loop, await self._loop.run_in_executor(None, self._conn.close))
    async def ltxid(self):
        return Cursor(self._loop,await self._loop.run_in_executor(None, self._conn.ltxid))

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self.done = True
        await self._loop.run_in_executor(None, self._conn.close)
        # print("cursor close")


class Cursor:

    def __init__(self, loop, cursor):
        self._loop = loop
        self._cursor = cursor

    async def execute(self, *args, **kargs):
        return await self._loop.run_in_executor(None, functools.partial(self._cursor.execute, *args, **kargs))

    async def executemany(self, *args, **kargs):
        return await self._loop.run_in_executor(None, functools.partial(self._cursor.executemany, *args, **kargs))

    async def fetchmany(self, *args, **kargs):
        return await self._loop.run_in_executor(None, functools.partial(self._cursor.fetchmany, *args, **kargs))

    async def fetchall(self, *args, **kargs):
        return await self._loop.run_in_executor(None, functools.partial(self._cursor.fetchall, *args, **kargs))

    async def setinputsizes(self, *args, **kargs):
        return await self._loop.run_in_executor(None, functools.partial(self._cursor.setinputsizes, *args, **kargs))

    async def var(self, *args, **kargs):
        return await self._loop.run_in_executor(None, functools.partial(self._cursor.var, *args, **kargs))

    async def fetchone(self):
        return self._cursor.fetchone()

    def description(self):
        return self._cursor.description

    def rowcount(self):
        return self._cursor.rowcount

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self.done = True
        await self._loop.run_in_executor(None, self._cursor.close)
        # print("conn close")


def create_pool(loop, **DB_CONFIG):
    return Pool(loop, **DB_CONFIG)


async def main():
    DCONFIG = {'user': 'mymall', 'password': '123456', 'host': '192.168.1.12', 'port': '1520', 'sid': 'XE'}
    pool = await create_pool(loop, **DCONFIG)
    print(pool)
    async with await pool.acquire() as conn:
        async with await conn.cursor() as cursor:
            await cursor.execute("select * from users")
            rows = await cursor.fetchmany()
            print(rows)
    async with await pool.acquire() as conn:
        async with await conn.cursor() as cursor:
            await cursor.execute("select * from users")
            rows = await cursor.fetchmany()
            print(rows)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
