#!/usr/bin/env python
from sanic.response import json,text

from trump import db
from trump.app import app, request_loader
from trump import restapi
from trump.utils import uuid_info


from trump.query import get_items, get_item

restapi.app = app
restapi.bp.url_prefix = '/api/v1/sx'


restapi.bp.settings = {
        # 'ROLE_COLUMN': 'roles',
        'NO_PAGER_API': ['menu', 'users'],
        'ANONYMOUS_API': ['sx_xiaoqu', "sx_xqdetail","sx_xqdeal"],
        'INSERT_IN_LOCK_MODE': ['area'],
        'ACL_MODE': 'WHITE_LIST',
        'ACL': {
            'sx_xqdetail': {
                'LS': {'USER','ANONYMOUS'},
                'GET': {'USER'},
                },
            'sx_xiaoqu':{
                'LS': {'USER','ANONYMOUS'},
                'GET': {'USER'},
                },
            'sx_xqdeal':{
                'LS': {'USER',"ANONYMOUS"},
                'GET': {'USER'},
                'POST': {'USER'},
                'PUT': {'USER'}
                },
            'test':{
                'LS': {'USER',"ANONYMOUS"},
                'GET': {'USER'},
                'POST': {'USER'},
                'PUT': {'USER'}
                }
            },
        }

# @restapi.bp.post('/login')
# async def login(request):
#         data = await get_items(app.pool, 'users', {'account': request.json.get('account'), 'password': request.json.get('password')})
#         # set session, userid
#         if data:
#             request['login'] = data[0]
#             request['session']['uid'] = data[0]['id']
#             return json({'status': 0})
#         return json({'status': 1})
#
# @restapi.bp.route('/logout')
# async def logout(request):
#     request['session']['uid'] = None
#     return json({'status': 0})

@request_loader
async def loaduser(request):
    request['user'] = await get_item(app.pool, 'users', request["session"].get('uid'))
    #request['user'] = await db.query(app.pool, 'SELECT * FROM users WHERE id = $1', request["session"].get('uid'), fetch_type='fetchrow', **uuid_info(request))
@restapi.bp.get('/test')
async def weishenmea(request):
    return text("OK")
app.blueprint(restapi.bp)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9860, debug=True)
