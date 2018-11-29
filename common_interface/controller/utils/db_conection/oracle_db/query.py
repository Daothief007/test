import ujson
from datetime import datetime, date

import cx_Oracle

from controller.utils.db_conection.oracle_db.pool import create_pool

import logging.config

log = logging.getLogger(__name__)

app = None

cx_Oracle.__future__.dml_ret_array_val = True

async def create_pools(loop, **DB_CONFIG):
   pool = await create_pool(**DB_CONFIG, loop=loop)
   return pool

async def get_check_acl(acl,pool,method,name):
    data = await get_items(pool, 'acl_white', {"method": method, "name": name})
    for i in data:
        if acl.get(i.get("name")):
            acl[i.get("name")][i.get("method")] = set(i.get("rolename"))
        else:
            acl[i.get("name")] = {i.get("method"): {}}
            acl[i.get("name")][i.get("method")] = set(i.get("rolename"))
    return acl

async def get_all_tables(pool, **DB_CONFIG):
    async with await pool.acquire() as connection:
        tables = {}
        async with await connection.cursor() as cur:
            await cur.execute("""SELECT object_name,object_type FROM user_objects WHERE object_type IN ('TABLE','VIEW')""")

            r = await cur.fetchall()
            tables.update({x[0].lower(): x[1].lower() for x in r})
            return tables

def _fix_types(record, attributes):
    d = {}
    for i in record:
        if attributes.get(i) == 'timestamp':
            if record[i]:
                d[i] = record[i].strftime("%Y-%m-%d %H:%M:%S")
        elif record[i] and attributes.get(i) == 'clob':
            d[i] = ujson.loads(record[i].read())
        else:
            d[i] = record[i]
    return d


def _prepare_vaules(stmt, args_db):
    values = []
    for i, params in enumerate(stmt.get_parameters()):
        log.info(f"trump:{params.name}")
        if params.name.startswith('int') and params.kind == 'array':
            values.append([int(x) for x in args_db[i]])
        elif params.name.startswith('int') and params.kind != 'array':
            values.append(int(args_db[i]))
        elif params.name == 'timestamptz' or params.name == 'timestamp' or params.name == 'date':
            n = args_db[i].count(':')
            fmt = "%Y-%m-%d"
            if n == 1:
                fmt = "%Y-%m-%d %H:%M"
            elif n == 2:
                fmt = "%Y-%m-%d %H:%M:%S"
            values.append(datetime.strptime(args_db[i], fmt))
        elif params.name == 'bool':
            values.append(bool(args_db[i]))
        else:
            values.append(args_db[i])
    return values


def _prepare_vaules_write(attributes, key, value):
    if attributes.get(key) == 'clob':
        if type(value) != str:
            value = ujson.encode(value)
    elif attributes.get(key) == 'timestamptz' or attributes.get(key) == 'timestamp' or attributes.get(key) == 'date':
        n = value.count(':')
        fmt = "%Y-%m-%d"
        if n == 1:
            fmt = "%Y-%m-%d %H:%M"
        elif n == 2:
            fmt = "%Y-%m-%d %H:%M:%S"
        value = datetime.strptime(value, fmt)
    return value

async def get_items(db, table, args={}, roles=False, with_total=False, pager=False, uuid='-', uid='-'):
    async with await db.acquire() as connection:
        async with await connection.cursor() as cur:
            sql = f"SELECT * FROM {table} WHERE rownum = 0"
            await cur.execute(sql)
            row = await cur.fetchmany()
            where = []
            args_db = []
            total = 0
            times = []
            field = '*'
            attributes = {s[0].lower(): s[1] for s in cur.description()}
            for k,v in attributes.items():
                if attributes.get(k).__name__ == 'TIMESTAMP' or attributes.get(k).__name__ == 'date':
                    times.append(k)
            for arg_key in args:
                if arg_key in attributes:
                    if args.get(arg_key) is None:
                        where.append(f'{arg_key} IS NULL')
                    else:
                        where.append(f'{arg_key} = :s')
                        args_db.append(args.get(arg_key))

                elif arg_key.split('-')[0] in attributes:
                    key, op = arg_key.split('-')
                    param = f"to_date(:s, 'YYYY-MM-DD HH24:MI:SS')"
                    if op == 'in':
                        args_array = ','.join([':s' for x in args.get(arg_key).split(',')])
                        where.append(f'{key} IN ({args_array})')
                        args_db.extend(args.get(arg_key).split(','))
                    elif op == 'nein':
                        args_array = ','.join([':s' for x in args.get(arg_key).split(',')])
                        where.append(f'{key} NOT IN ({args_array})')
                        args_db.extend(args.get(arg_key).split(','))
                    elif op == 'gt':
                        if key in times:
                            where.append(f"{key} > {param}")
                        else:
                            where.append(f'{key} > :s')
                        args_db.append(args.get(arg_key))
                    elif op == 'gte':
                        if key in times:
                            where.append(f"{key} >= {param}")
                        else:
                            where.append(f'{key} >= :s')
                        args_db.append(args.get(arg_key))
                    elif op == 'lt':
                        if key in times:
                            where.append(f"{key} < {param}")
                        else:
                            where.append(f'{key} < :s')
                        args_db.append(args.get(arg_key))
                    elif op == 'lte':
                        if key in times:
                            where.append(f"{key} <= {param}")
                        else:
                            where.append(f'{key} <= :s')
                        args_db.append(args.get(arg_key))
                    elif op == 'ne':
                        if key in times:
                            where.append(f"{key} <> {param}")
                        else:
                            where.append(f'{key} <> :s')
                        args_db.append(args.get(arg_key))
                    elif op == 'no':
                        where.append(f'{key} IS NOT NULL')
                    elif op == 'range':
                        # '(a > 1 and a < 10)'
                        _min_, _max_ = args.get(arg_key).split('|')
                        if _min_:
                            if key in times:
                                where.append(f"{key} >= {param}")
                            else:
                                where.append(f'{key} >= :s')
                            args_db.append(_min_)
                        if _max_:
                            if key in times:
                                where.append(f"{key} <= {param}")
                            else:
                                where.append(f'{key} <= :s')
                            args_db.append(_max_)
                    elif op == 'overlap':
                        where.append(f'dbms_lob.instr({key}，:s) > 0')
                        args_db.append(args.get(arg_key))
                    elif op == 'like':
                        where.append(f'{key} LIKE :s')
                        args_db.append('%' + args.get(arg_key) + '%')
                    elif op == 'like_raw':
                        where.append(f'{key} LIKE :s')
                        args_db.append(dict(args).get(arg_key))

            if attributes.get('view_roles') and roles is not False:
                roles = ''.join(roles)
                where.append(f'dbms_lob.instr(view_roles，:s) > 0')
                args_db.append(roles)

            where_cause = 'WHERE ' + ' AND '.join(where) if where else ''

            new_list = []
            if with_total:
                sql = f'SELECT count(*) FROM {table} {where_cause}'
                await cur.execute(sql, args_db)
                r = await cur.fetchmany()
                total = r[0][0]
                new_list = []
                columns = [i[0].lower() for i in cur.description()]
                log.info(f"columns:{columns}")
                lists = []
                for rows in r:
                    lists.append(list(rows))
                for row in lists:
                    row_dict = dict()
                    for col in columns:
                        row_dict[col] = row[columns.index(col)]
                    new_list.append(row_dict)

            if args.get('field'):
                field = args.get('field')
            order = ''
            sort = args.get('sort')
            if sort:
                sort_list = sort.split(',')
                order_list = []
                for item_sort in sort_list:
                    order_column = item_sort.strip('-')
                    if order_column in attributes:
                        order_type = 'ASC' if item_sort.startswith('-') else 'DESC'
                        order_list.append(f'{order_column} {order_type}')
                if order_list:
                    order_cause = ', '.join(order_list)
                    order = f'ORDER by {order_cause}'
            sql = f'SELECT {field} FROM {table} {where_cause} {order}'

            if pager:
                page_size = args.get('pagesize') if args.get('pagesize') else 10
                try:
                    page = int(args.get('page')) if args.get('page') else 0
                    int(page_size)
                    current_position = (page + 1) * int(page_size)
                    min_position = int(current_position) - int(page_size) if args.get('page') else 0
                    log.info(f"current_position:{current_position}")
                    sql = f'SELECT {field} FROM (SELECT ROWNUM rn,e.* FROM (SELECT * FROM {table} {where_cause} {order})e ' \
                          f'WHERE ROWNUM<={current_position}) t2 WHERE t2.rn >{min_position}'
                except Exception as e:
                    pass
            log.info(f"sql===={sql} \n args_db:{args_db}")
            await cur.execute(sql, args_db)
            r = await cur.fetchall()
            attributes = {s[0].lower(): s[1].__name__.lower() for s in cur.description()}
            new_list = []
            columns = [i[0].lower() for i in cur.description()]
            lists = []
            for rows in r:
                lists.append(list(rows))
            for row in lists:
                row_dict = dict()
                for col in columns:
                    row_dict[col] = row[columns.index(col)]
                new_list.append(row_dict)
            if with_total:
                return (total, [_fix_types(item, attributes) for item in new_list])
            else:
                return [_fix_types(item, attributes) for item in new_list]

async def get_item(db, table, oid, roles=False, column='id', uuid='-', uid='-'):
    async with await db.acquire() as connection:
        async with await connection.cursor() as cur:
            value = [oid]
            times = []
            row = []
            sql = f"SELECT * FROM {table} WHERE rownum = 0"
            await cur.execute(sql)
            attributes = {s[0].lower(): s[1] for s in cur.description()}
            for k,v in attributes.items():
                if attributes.get(k).__name__ == 'TIMESTAMP' or attributes.get(k).__name__ == 'date':
                    times.append(k)
            if column in times:
                sql = f"SELECT * FROM {table} WHERE {column} = to_date(:s, 'YYYY-MM-DD HH24:MI:SS')"
            else:
                sql = f'SELECT * FROM {table} WHERE {column} = :s'
            if attributes.get('view_roles') and roles is not False:
                sql += ' AND dbms_lob.instr(view_roles，:s) > 0'
                value.append(''.join(roles))
            sql += ' AND rownum = 1'
            log.info(f"sql===={sql} \n value={value}")
            await cur.execute(sql, value)
            stmt = await cur.fetchone()
            if stmt:
                columns = [i[0].lower() for i in cur.description()]
                row = list(stmt)
                row_dict = dict()
                for col in columns:
                    row_dict[col] = row[columns.index(col)]
            attributes = {s[0].lower(): s[1].__name__.lower() for s in cur.description()}
            if stmt:
                return _fix_types(row_dict, attributes)

async def create_item(db, table, data, column='id', lock_table=False, uuid='-', uid='-'):
    async with await db.acquire() as connection:
        async with await connection.cursor() as cur:
            sql = f"SELECT * FROM {table} WHERE rownum = 0"
            await cur.execute(sql)
            r = await cur.fetchmany()
            attributes = {s[0].lower(): s[1].__name__.lower() for s in cur.description()}
            result = []
            keys = []
            val_col = []
            count = 0
            if type(data) == list:
                vals = []
                for item in data:
                    values = {}
                    count += 1
                    val_col = []
                    keys = []
                    for key in item:
                        if key not in attributes: continue
                        if key not in keys:
                            keys.append(key)
                        value = item[key]
                        if attributes.get(key) == 'clob':
                            await cur.setinputsizes(**{key: cx_Oracle.CLOB})
                        val_col.append(":" + key)
                        values[key] = _prepare_vaules_write(attributes, key, value)
                        if attributes.get("id") == 'string':
                            idVar = await cur.var(cx_Oracle.STRING, arraysize=len(data))
                        elif attributes.get("id") == 'number':
                            idVar = await cur.var(cx_Oracle.NUMBER, arraysize=len(data))
                        values["idVar"] = idVar
                    vals.append(values)
                    val_colums = "(" + ','.join(val_col) + ")"
                    key_columns = ', '.join([k for k in keys])
                sql = f"INSERT INTO {table} ({key_columns}) VALUES {val_colums}" \
                      f" returning {column} into :idVar"
                log.info(f"sql===={sql}")
                await cur.executemany(sql, vals)
                await connection.commit()
                idlist = idVar.values
                result = [int(i) if attributes.get("id") == 'number' else i for item in idlist for i in item]
                return result
            else:
                values = {}
                for key in data:
                    if key not in attributes: continue
                    keys.append(key)
                    value = data[key]
                    if attributes.get(key) == 'clob':
                        await cur.setinputsizes(**{key: cx_Oracle.CLOB})
                    val_col.append(":" + key)
                    values[key] = _prepare_vaules_write(attributes, key, value)
                val_colums = "(" + ','.join(val_col) + ")"
                key_columns = ', '.join([k for k in keys])
                if attributes.get("id") == 'string':
                    idVar = await cur.var(cx_Oracle.STRING)
                elif attributes.get("id") == 'number':
                    idVar = await cur.var(cx_Oracle.NUMBER)
                sql = f"INSERT INTO {table} ({key_columns}) VALUES {val_colums} returning {column} into :idVar"
                log.info(f"sql===={sql}")
                values["idVar"] = idVar
                await cur.execute(sql, values)
                if attributes.get("id") == 'number':
                    id = int(idVar.getvalue()[0])
                else:
                    id = idVar.getvalue()[0]
                await connection.commit()
                return id


async def modify_item(db, table, oid, data, column='id', uuid='-', uid='-'):
    async with await db.acquire() as connection:
        async with await connection.cursor() as cur:
            sql = f"SELECT * FROM {table} WHERE rownum = 0"
            await cur.execute(sql)
            r = await cur.fetchmany()
            attributes = {s[0].lower(): s[1].__name__.lower() for s in cur.description()}
            params = []
            values = []
            log.info(f"data:{data}")
            for key in data:
                if key not in attributes: continue
                params.append(f'{key} = :s')
                value = data[key]
                values.append(_prepare_vaules_write(attributes, key, value))

            args_array = ','.join([':s' for x in oid.split(',')])
            values.extend(oid.split(','))
            cause = ', '.join(params)
            sql = f"UPDATE {table} SET {cause} WHERE {column} in ({args_array})"
            log.info(f"sql===={sql}")
            await cur.execute(sql, values)
            result = cur.rowcount()
            await connection.commit()
            return result


# 修改多条，data1为where条件例{'grade_id': int(params.get('grade_id'))}。data为修改内容，同modify_item
async def modify_items(db, table, data1, data, uuid='-', uid='-'):
    async with await db.acquire() as connection:
        async with await connection.cursor() as cur:
            sql = f"SELECT * FROM {table} WHERE rownum = 0"
            await cur.execute(sql)
            r = await cur.fetchmany()
            attributes = {s[0].lower(): s[1].__name__.lower() for s in cur.description()}
            params = []
            values = []
            column = []
            for key in data:
                if key not in attributes: continue
                params.append(f'{key} = :s')
                value = data[key]
                values.append(_prepare_vaules_write(attributes, key, value))
            for key1 in data1:
                if key1 not in attributes: continue
                column.append(f'{key1} = :s')
                value = data1[key1]
                values.append(_prepare_vaules_write(attributes, key1, value))
            cause = ', '.join(params)
            condition = ' and '.join(column)
            sql = f"UPDATE {table} SET {cause} WHERE {condition}"
            log.info(f"sql===={sql}")
            await cur.execute(sql, values)
            result = cur.rowcount()
            await connection.commit()
            return result

async def delete_item(db, table, oid, column='id', uuid='-', uid='-'):
    async with await db.acquire() as conn:
        async with await conn.cursor() as cur:
            oids = []
            args_array = ','.join([':s' for x in oid.split(',')])
            oids.extend(oid.split(','))
            sql = f"DELETE FROM {table} WHERE {column} in ({args_array})"
            await cur.execute(sql, oids)
            await conn.commit()
            return True

async def query(pool, sql, *args, fetch_type = 'fetch', uuid='-', uid='-'):
    async with await pool.acquire() as connection:
        async with await connection.cursor() as cur:
            log.info(f"sql===={sql} \n args:{args}")
            await cur.execute(sql,(*args,))
            attributes = {s[0].lower(): s[1].__name__.lower() for s in cur.description()}
            columns = [i[0].lower() for i in cur.description()]
            lists = []
            new_list = []
            if fetch_type == 'fetch':
                result = await cur.fetchall()
                for rows in result:
                    lists.append(list(rows))
                for row in lists:
                    row_dict = dict()
                    for col in columns:
                        row_dict[col] = row[columns.index(col)]
                    new_list.append(row_dict)
                return [_fix_types(item, attributes) for item in new_list]
            elif fetch_type == 'fetchrow':
                result = await cur.fetchone()
                row_dict = dict()
                if result:
                    lists.append(list(result))
                    for row in lists:
                        for col in columns:
                            row_dict[col] = row[columns.index(col)]
                return _fix_types(row_dict, attributes)
            elif fetch_type == 'fetchval':
                result = await cur.fetchone()
                if result:
                    result = result[0]
                    if type(result) == datetime:
                        return result.strftime("%Y-%m-%d %H:%M:%S")
                return result
            elif fetch_type == 'attributes':
                return {s[0].lower(): s[1].__name__.lower() for s in cur.description()}

# async def execute(pool, sql, *args, table, uuid='-', uid='-'):
#     async with pool.acquire() as connection:
#         statement = await connection.prepare(sql.format(*range(1, sql.count('{}')+1)))
#         updestmt = await connection.prepare("SELECT * FROM %s"%(table))
#         attributes = {s[0]: s[1][1] for s in updestmt.get_attributes()}
#         values = _prepare_vaules(updestmt, args)
#         log.debug(f"{uuid} {uid} arg:{args}\nsql:{sql}\nval:{values}")
#         result = await connection.fetch(sql, *values)

async def execute(pool, sql, *args, uuid='-', uid='-'):
    log.info(f"sql===={sql} \n args:{args}")
    async with pool.acquire() as conn:
        async with await conn.cursor() as cur:
            await cur.execute(sql, (*args,))
            await conn.commit()

