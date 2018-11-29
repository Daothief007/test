import ujson
from datetime import datetime, date
import pytz

import logging.config

log = logging.getLogger(__name__)


def _fix_types(record, attributes):
    item = dict(record.items())
    d = {}
    for i in item:
        if type(item[i]) == datetime:
            prc = pytz.timezone('PRC')
            # print(dir(item[i]))
            # print(item[i].tzinfo)
            d[i] = item[i].astimezone(prc).strftime("%Y-%m-%d %H:%M:%S")
        elif attributes.get(i) == 'json':
            if item[i]:
                d[i] = ujson.decode(item[i])
        else:
            d[i] = item[i]
    return d


def _prepare_vaules(stmt, args_db):
    # print(stmt.get_parameters())
    values = []
    for i, params in enumerate(stmt.get_parameters()):
        # if params.name in ('int4', ''):
        print("trump:", params.name)
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
            # print(values)
    return values


def _prepare_vaules_write(attributes, key, value):
    if attributes.get(key) == 'json':
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
    # print("type==>",type(value),",value=",value)
    return value


async def get_items(db, table, args={}, roles=False, with_total=False, pager=False, uuid='-', uid='-'):
    async with db.acquire() as connection:
        stmt = await connection.prepare(f'SELECT * FROM {table}')

        # prepare where
        where = []
        args_db = []
        attributes = {s[0]: s[1][1] for s in stmt.get_attributes()}
        for arg_key in args:
            if arg_key in attributes:
                if args.get(arg_key) == None:
                    where.append(f'{arg_key} IS NULL')
                else:
                    where.append(f'{arg_key} = ${{}}')
                    args_db.append(args.get(arg_key))
            elif arg_key.split('-')[0] in attributes:
                key, op = arg_key.split('-')
                if op == 'in':
                    args_array = ','.join(['${}' for x in args.get(arg_key).split(',')])
                    where.append(f'{key} IN ({args_array})')
                    args_db.extend(args.get(arg_key).split(','))
                elif op == 'nein':
                    args_array = ','.join(['${}' for x in args.get(arg_key).split(',')])
                    where.append(f'{key} NOT IN ({args_array})')
                    args_db.extend(args.get(arg_key).split(','))
                elif op == 'contains':
                    where.append(f'${{}} = ANY({key})')
                    args_db.append(args.get(arg_key))
                elif op == 'necontains':
                    where.append(f'${{}} <> {key}')
                    args_db.append(args.get(arg_key).split(','))
                elif op == 'neoverlap':
                    where.append(f'not {key} && ${{}} ')
                    args_db.append(args.get(arg_key).split(','))
                elif op == 'gt':
                    where.append(f'{key} > ${{}}')
                    args_db.append(args.get(arg_key))
                elif op == 'lt':
                    where.append(f'{key} < ${{}}')
                    args_db.append(args.get(arg_key))
                elif op == 'ne':
                    where.append(f'{key} <> ${{}}')
                    args_db.append(args.get(arg_key))
                elif op == 'range':
                    # '(a > 1 and a < 10)'
                    _min_, _max_ = args.get(arg_key).split('|')
                    if _min_:
                        where.append(f'{key} >= ${{}}')
                        args_db.append(_min_)
                    if _max_:
                        where.append(f'{key} <= ${{}}')
                        args_db.append(_max_)
                elif op == 'overlap':
                    where.append(f'{key} && ${{}} ')
                    args_db.append(args.get(arg_key).split(','))
                elif op == 'like':
                    where.append(f'{key} LIKE ${{}}')
                    args_db.append('%' + args.get(arg_key) + '%')
                elif op == 'like_raw':
                    where.append(f'{key} LIKE ${{}}')
                    args_db.append(dict(args).get(arg_key))
        # permission
        if attributes.get('view_roles') and roles is not False:
            where.append('view_roles && ${}')
            args_db.append(roles)

        where_cause = 'WHERE ' + ' AND '.join(where) if where else ''

        values = []

        if with_total:
            sql = f'SELECT count(*) FROM {table} {where_cause}'
            sql = sql.format(*range(1, sql.count('{}') + 1))
            stmt = await connection.prepare(sql)
            values = _prepare_vaules(stmt, args_db)

            total = await stmt.fetchval(*values)

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

        limit = ''
        if pager:
            page_size = args.get('pagesize') if args.get('pagesize') else 10
            try:
                if args.get('page'):
                    int(args.get('page'))
                int(page_size)
                current_position = int(args.get('page')) * int(page_size) if args.get('page') else 0
                limit = f'LIMIT {page_size} OFFSET {current_position}'
            except Exception as e:
                print(e)
        sql = f'SELECT * FROM {table} {where_cause} {order} {limit}'
        sql = sql.format(*range(1, sql.count('{}') + 1))

        stmt = await connection.prepare(sql)

        if not with_total:
            values = _prepare_vaules(stmt, args_db)

        print("@@@@@@@@@@@@@@:", sql, args, *values)
        records = await stmt.fetch(*values)

        log.debug(f"{uuid} {uid} arg:{args}\nsql:{sql}\nval:{values}")
        if with_total:
            return (total, [_fix_types(r, attributes) for r in records])
        else:
            return [_fix_types(r, attributes) for r in records]


async def get_item(db, table, oid, roles=False, column='id', uuid='-', uid='-'):
    async with db.acquire() as connection:
        value = [oid]
        sql = f'SELECT * FROM {table} WHERE {column} = $1'
        stmt = await connection.prepare(sql)
        attributes = {s[0]: s[1][1] for s in stmt.get_attributes()}
        if attributes.get('view_roles') and roles is not False:
            sql += ' AND view_roles && $2'
            stmt = await connection.prepare(sql)
            value.append(roles)
        record = await stmt.fetchrow(*value)
        log.debug(f"{uuid} {uid} arg:{None}\nsql:{sql}\nval:{value}")
        if record:
            return _fix_types(record, attributes)


async def create_item(db, table, data, column='id', lock_table=False, uuid='-', uid='-'):
    if not data: return False
    async with db.acquire() as connection:
        sql = f'SELECT * FROM {table}'
        stmt = await connection.prepare(sql)
        attributes = {s[0]: s[1][1] for s in stmt.get_attributes()}
        # kv = [ (k, data[k]) for k in data ]
        retlist = []
        keys = []
        values = []
        val_col = ""
        val_colums = ""
        count = 0
        async with connection.transaction():
            if lock_table:
                await connection.execute(f'LOCK TABLE {table} IN EXCLUSIVE MODE')
            if type(data) == list:
                for item in data:
                    for key in item:
                        if key not in attributes: continue
                        count = count + 1
                        if key not in keys:
                            keys.append(key)
                        value = item[key]
                        if val_col:
                            val_col = val_col + ',' + f'${count}'
                        else:
                            val_col = f'${count}'
                        values.append(_prepare_vaules_write(attributes, key, value))
                    tuval = tuple(values)
                    values = []
                    val_col = "(" + val_col + ")"
                    val_colums = val_col
                    val_col = ""
                    count = 0
                    key_columns = ', '.join([k for k in keys])
                    sql = f"INSERT INTO {table} ({key_columns}) VALUES {val_colums} RETURNING {column};"
                    val_colums = ""
                    keys = []
                    log.debug(f"{uuid} {uid} arg:{data}\nsql:{sql}\nval:{tuval}")
                    stmt = await connection.prepare(sql)
                    retlist.append(await stmt.fetchval(*tuval))
                return retlist
            else:
                for key in data:
                    if key not in attributes: continue
                    count = count + 1
                    keys.append(key)
                    value = data[key]

                    if val_col:
                        val_col = val_col + ',' + f'${count}'
                    else:
                        val_col = f'${count}'
                    values.append(_prepare_vaules_write(attributes, key, value))
                tuval = tuple(values)
                val_col = "(" + val_col + ")"
                val_colums = val_col
                val_col = ""
                count = 0
                key_columns = ', '.join([k for k in keys])
                sql = f"INSERT INTO {table} ({key_columns}) VALUES {val_colums} RETURNING {column};"
                log.debug(f"{uuid} {uid} arg:{data}\nsql:{sql}\nval:{tuval}")
                stmt = await connection.prepare(sql)
                return await stmt.fetchval(*tuval)


async def modify_item(db, table, oid, data, column='id', uuid='-', uid='-'):
    # return json({'status': 1, 'message': 'not allowed'})
    # start = datetime.now()
    async with db.acquire() as connection:
        stmt = await connection.prepare(f'SELECT * FROM {table}')
        attributes = {s[0]: s[1][1] for s in stmt.get_attributes()}
        # print("PARAMETERS", stmt.get_parameters())
        params = []
        values = []
        for key in data:
            if key not in attributes: continue
            params.append(f'{key} = ${{}}')
            value = data[key]
            values.append(_prepare_vaules_write(attributes, key, value))
        values.append(int(oid))
        cause = ', '.join(params)
        sql = f"UPDATE {table} SET {cause} WHERE {column} = ${{}}"
        sql = sql.format(*range(1, sql.count('{}') + 1))
        log.debug(f"{uuid} {uid} arg:{data}\nsql:{sql}\nval:{values}")
        record = await connection.fetch(sql, *values)
        # print('PUT', record)
        # print(datetime.now()-start)
        return True


# 修改多条，data1为where条件例{'grade_id': int(params.get('grade_id'))}。data为修改内容，同modify_item
async def modify_items(db, table, data1, data, uuid='-', uid='-'):
    async with db.acquire() as connection:
        stmt = await connection.prepare(f'SELECT * FROM {table}')
        attributes = {s[0]: s[1][1] for s in stmt.get_attributes()}
        params = []
        values = []
        column = []
        for key in data:
            if key not in attributes: continue
            params.append(f'{key} = ${{}}')
            value = data[key]
            values.append(_prepare_vaules_write(attributes, key, value))
        for key1 in data1:
            if key1 not in attributes: continue
            column.append(f'{key1} = ${{}}')
            value = data1[key1]
            values.append(_prepare_vaules_write(attributes, key1, value))
        cause = ', '.join(params)
        condition = 'and '.join(column)
        sql = f"UPDATE {table} SET {cause} WHERE {condition}"
        sql = sql.format(*range(1, sql.count('{}') + 1))
        log.debug(f"{uuid} {uid} arg:{column}\nsql:{sql}\nval:{values}")
        record = await connection.fetch(sql, *values)
        return True


async def delete_item(db, table, oid, column='id', uuid='-', uid='-'):
    # return json({'status': 1, 'message': 'not allowed'})
    async with db.acquire() as conn:
        sql = f"DELETE FROM {table} WHERE {column} = $1"
        log.debug(f"{uuid} {uid} arg:{None}\nsql:{sql} values:{oid} column:{column}")
        record = await conn.fetch(sql, int(oid))
        return True
