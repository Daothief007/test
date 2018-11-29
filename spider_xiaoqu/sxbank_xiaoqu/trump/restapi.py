import traceback, sys
from sanic import Sanic, Blueprint
from sanic.response import json, text
from trump.utils import uuid_info
from trump import utils
from trump.query import create_item, get_items, get_item, modify_item, delete_item
import logging.config
log = logging.getLogger(__name__)

bp = Blueprint('restapi')

app = None
bp.settings = {
        'NO_PAGER_API': ['menu'],
        'ANONYMOUS_API': ['area'],
        'INSERT_IN_LOCK_MODE': ['area'],
        'ACL_MODE': 'BLACK_LIST',
        'ACL': {
            'asset': {
                'LS': {'SYSTEM'},
                'GET': {'SYSTEM'},
                },
            },
        }


def _get_role_column(request):
    return bp.settings.get('ROLE_COLUMN', 'staff_role_name')

def _get_roles(request):
    return set(request['user'][_get_role_column(request)])

def check_login(request, name):
    if not bp.settings.get('ANONYMOUS_API'):    # for init test
        return True
    elif name in bp.settings.get('ANONYMOUS_API'):
        return True
    else:
        #if request.get('user') and request.get('user').get('staff_role_name') != 'ANONYMOUS':
        if request.get('user'):
            return request.get('user').get(_get_role_column(request), ['ANONYMOUS']) != ['ANONYMOUS']
        else:
            return False


def check_acl(request, method, name):
    if not bp.settings.get('ANONYMOUS_API'):    # for init test
        return True
    # elif name in bp.settings.get('ANONYMOUS_API'):
    #     return True
    roles =  _get_roles(request)
    acl_mode = bp.settings.get('ACL_MODE')
    acl = bp.settings.get('ACL')
    acl_rule = acl.get(name, {}).get(method) if acl else {}
    #print(roles, method, name, acl_mode, acl, acl_rule)
    if acl_mode == 'BLACK_LIST':
        if acl_rule and roles.intersection(acl_rule):
                return False
    elif acl_mode == 'WHITE_LIST':
        if acl_rule and roles.intersection(acl_rule):
            return True
        else:
            return False
    return True


async def ls(request, name):
    name = name+'_view' if app.tables.get(name+'_view') else name
    if name not in app.tables: return text('404', status=404)
    # print(request['user']['staff_role_name'] if request['user'] else [])
    total, data = await get_items(app.pool, name, request.args, _get_roles(request), True, name not in bp.settings['NO_PAGER_API'], **uuid_info(request))
    if dir(app.post_process.get(name)).count('ls') == 1:
        new_data = await app.post_process.get(name).ls(app, request, data)
        if new_data:
            data = new_data
    return json({'status': 0, 'data': {'total': total, 'list': data}})

async def get(request, name, oid):
    name = name+'_view' if app.tables.get(name+'_view') else name
    if name not in app.tables: return text('404', status=404)
    data = await get_item(app.pool, name, int(oid), _get_roles(request), **uuid_info(request))
    if data:
        if dir(app.post_process.get(name)).count('get') == 1:
            new_data = await app.post_process.get(name).get(app, request, data, oid)
            if new_data:
                data = new_data
        return json({'status': 0, 'data': data})
    else:
        return text('Not found', status=404)

async def post(request, name):
    async with app.pool.acquire() as conn:
        try:
            data = []
            # if type(request.json) == list:
            #     # for item in request.json:
            #     #     try:
            #     #         data.append(await create_item(app.pool, name, item, lock_table=name in bp.settings['INSERT_IN_LOCK_MODE']))
            #     #     except:
            #     #         data.append(-1)
            #     data = await create_item(app.pool, name, request.json, lock_table=name in bp.settings['INSERT_IN_LOCK_MODE'], uuid=utils.get_uuid(request), uid=utils.get_uid(request))
            # else:
            data = await create_item(app.pool, name, request.json, lock_table=name in bp.settings['INSERT_IN_LOCK_MODE'], **uuid_info(request))
            if dir(app.post_process.get(name)).count('post') == 1:
                new_data = await app.post_process.get(name).post(app, request, data)
                if new_data:
                    data = new_data
            return json({'status': 0, 'data': data})
        except Exception as err:
            #traceback.print_exc()
            log.warning(f"{utils.get_uuid(request)} {utils.get_uid(request)} {''.join(traceback.format_exception(*sys.exc_info()))}")
            return json({'status': 1, 'data': err.message if dir(err).count('message') else 'err'})

async def put(request, name, oid):
    #return json({'status': 1, 'message': 'not allowed'})
    try:
        data = await modify_item(app.pool, name, oid, request.json, **uuid_info(request))
        if dir(app.post_process.get(name)).count('put') == 1:
            new_data = await app.post_process.get(name).put(app, request, data, oid)
            if new_data:
                return new_data
        return json({'status': 0})
    except:
        #traceback.print_exc()
        log.warning(f"{utils.get_uuid(request)} {utils.get_uid(request)} {''.join(traceback.format_exception(*sys.exc_info()))}")
        return json({'status': 1})

async def delete(request, name, oid):
    #return json({'status': 1, 'message': 'not allowed'})
    data = await delete_item(app.pool, name, oid, **uuid_info(request))
    if dir(app.post_process.get(name)).count('delete') == 1:
        new_data = await app.post_process.get(name).delete(app, request, data, oid)
        if new_data:
            return new_data
    return json({'status': 0})


@bp.route(f'/<name>', methods=['GET', 'POST', 'OPTIONS'])
async def process_dir(request, name):
    if request.method == 'OPTIONS':
        return text(None)
    if not check_login(request, name):
        return text('Login required', status=401)
    method = request.method if request.method != 'GET' else 'LS'
    if not check_acl(request, method, name):
        return text('Forbidden', status=403)
    if request.method == 'GET':

        if dir(app.pre_process.get(name)).count('ls') == 1:
            data = await app.pre_process.get(name).ls(app, request)
            if data:
                return data
        return await ls(request, name)
    elif request.method == 'POST':
        if dir(app.pre_process.get(name)).count('post') == 1:
            data = await app.pre_process.get(name).post(app, request)
            if data:
                return data
        if name not in app.tables: return text('404', status=404)
        return await post(request, name)

@bp.route(f'/<name>/<oid>', methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])
async def process_item(request, name, oid):
    if request.method == 'OPTIONS':
        return text(None)
    if not check_login(request, name):
        return text('Login required', status=401)
    method = request.method
    if not check_acl(request, method, name):
        return text('Forbidden', status=403)
    if request.method == 'GET':
        if dir(app.pre_process.get(name)).count('get') == 1:
            data = await app.pre_process.get(name).get(app, request, oid)
            if data:
                return data
        return await get(request, name, oid)
    elif request.method == 'PUT':
        if dir(app.pre_process.get(name)).count('put') == 1:
            data = await app.pre_process.get(name).put(app, request, oid)
            if data:
                return data
        if name not in app.tables: return text('404', status=404)
        return await put(request, name, oid)
    elif request.method == 'DELETE':
        if dir(app.pre_process.get(name)).count('delete') == 1:
            data = await app.pre_process.get(name).delete(app, request, oid)
            if data:
                return data
        if name not in app.tables: return text('404', status=404)
        return await delete(request, name, oid)


# @bp.post('/login')
# async def login(request):
#         data = await get_items(app.pool, 'staff_login_view', {'mobile': request.json.get('account'), 'password': request.json.get('password')})
#         # set session, userid
#         if data:
#             request['login'] = data[0]
#             request['session']['uid'] = data[0]['id']
#             return json({'status': 0})
#         return json({'status': 1})

# @bp.route('/logout')
# async def logout(request):
#     request['session']['uid'] = None
#     return json({'status': 0})


@bp.middleware('request')
async def preprocess(request):
    url = request.url
    if hasattr(request, "path"):
        url = request.path
    #api = request.url[len(bp.url_prefix) if bp.url_prefix else 0:].strip('/').split('/')[0]
    api = url[len(bp.url_prefix) if bp.url_prefix else 0:].strip('/').split('/')[0]
    body = None
    try:
        body = request.json
    except Exception:
        pass
    log.debug(f"{utils.get_uuid(request)} {utils.get_uid(request)} {request.method} {api}:{request.args}:{body}")

    if app.pre_process.get(api):
        if dir(app.pre_process.get(api)).count('process') == 1:
            result = await app.pre_process.get(api).process(app, request)
            if result:
                return result

@bp.middleware('response')
async def postprocess(request, response):
    url = request.url
    if hasattr(request, "path"):
        url = request.path
    #api = request.url[len(bp.url_prefix) if bp.url_prefix else 0:].strip('/').split('/')[0]
    api = url[len(bp.url_prefix) if bp.url_prefix else 0:].strip('/').split('/')[0]
    if app.post_process.get(api):
        if dir(app.post_process.get(api)).count('process') == 1:
            result = await app.post_process.get(api).process(app, request, response)

