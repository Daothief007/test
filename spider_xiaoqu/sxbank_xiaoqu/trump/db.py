from datetime import datetime

from trump.query import _fix_types, _prepare_vaules
import logging.config
log = logging.getLogger(__name__)


async def query(pool, sql, *args, fetch_type = 'fetch', uuid='-', uid='-'):
    async with pool.acquire() as connection:
        #print(sql.format(*range(1, sql.count('{}')+1)))
        stmt = await connection.prepare(sql.format(*range(1, sql.count('{}')+1)))
        attributes = {s[0]: s[1][1] for s in stmt.get_attributes()}
        values = _prepare_vaules(stmt, args)
        #print(stmt.get_attributes())
        log.debug(f"{uuid} {uid} arg:{args}\nsql:{sql}\nval:{values}\nfetch_type:{fetch_type}")
        if fetch_type == 'fetch':
            results = await stmt.fetch(*values)
            return [ _fix_types(r, attributes) for r in results]
        elif fetch_type == 'fetchrow':
            result = await stmt.fetchrow(*values)
            if result:
                return _fix_types(result, attributes)
        elif fetch_type == 'fetchval':
            result = await stmt.fetchval(*values)
            if type(result) == datetime:
                return result.strftime("%Y-%m-%d %H:%M:%S")
            return result
        elif fetch_type == 'attributes':
            return {s[0]: s[1][1] for s in stmt.get_attributes()}


async def execute(pool, sql, *args, table, uuid='-', uid='-'):
    async with pool.acquire() as connection:
        statement = await connection.prepare(sql.format(*range(1, sql.count('{}')+1)))
        updestmt = await connection.prepare("SELECT * FROM %s"%(table))
        attributes = {s[0]: s[1][1] for s in updestmt.get_attributes()}
        values = _prepare_vaules(updestmt, args)
        log.debug(f"{uuid} {uid} arg:{args}\nsql:{sql}\nval:{values}")
        result = await connection.fetch(sql, *values)