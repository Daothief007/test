import pkgutil
import traceback
import uuid

import ujson
from sanic import Sanic
from sanic.exceptions import SanicException, INTERNAL_SERVER_ERROR_HTML
from sanic.handlers import ErrorHandler
from sanic.response import json, text, html
from sanic_session import InMemorySessionInterface
from sanic_session import RedisSessionInterface

import asyncio_redis
from asyncpg import connect, create_pool

from trump import db, utils
from trump import restapi

from config import DB_CONFIG
from config import ALLOW_MULTI_LOGIN

import pre_process
import post_process

import logging.config

from trump.utils import uuid_info

log = logging.getLogger(__name__)


class Redis:
    """
    A simple wrapper class that allows you to share a connection
    pool across your application.
    """
    _pool = None

    async def get_redis_pool(self):
        REDIS_CONFIG = {'host': 'localhost', 'port': 6379}
        try:
            from config import REDIS_CONFIG
        except:
            pass
        if not self._pool:
            self._pool = await asyncio_redis.Pool.create(
                host=REDIS_CONFIG['host'], port=REDIS_CONFIG['port'], poolsize=10
            )

        return self._pool

    async def close(self):
        if self._pool:
            self._pool.close()


class CustomHandler(ErrorHandler):
    def default(self, request, exception):
        log.error(exception)
        if request:
            response_message = (
                'Exception occurred while handling uri: "{}"\n{}'.format(request.url, traceback.format_exc()))
            log.error(f"{utils.get_uuid(request)} {utils.get_uid(request)} {response_message}")
        if issubclass(type(exception), SanicException):
            return text(
                'Error: {}'.format(exception),
                status=getattr(exception, 'status_code', 500),
                headers=getattr(exception, 'headers', dict())
            )
        elif self.debug:
            html_output = self._render_traceback_html(exception, request)
            return html(html_output, status=500)
        else:
            return html(INTERNAL_SERVER_ERROR_HTML, status=500)


session_interface = InMemorySessionInterface()

try:
    redis = Redis()
    session_interface = RedisSessionInterface(redis.get_redis_pool, expiry=115200)
    log.info('- - Use RedisSessionInterface')
except:
    log.info('- - Use InMemorySessionInterface')

app = Sanic(__name__, error_handler=CustomHandler())


# async def loaduser(request):
#     if request.get("session") and request["session"].get("login_source") and request["session"].get("login_source") == 'BROKER':
#         request['user'] = await db.query(app.pool, 'SELECT * FROM broker WHERE id = $1',           request["session"].get('uid'), fetch_type='fetchrow', **uuid_info(request))
#     else:
#         request['user'] = await db.query(app.pool, 'SELECT * FROM staff_login_view WHERE id = $1', request["session"].get('uid'), fetch_type='fetchrow', **uuid_info(request))
#     log.info(f"{utils.get_uuid(request)} {utils.get_uid(request)} {request['user']}")

###need call by start entry
def request_loader(callback):
    app.loaduser = callback


@app.listener('before_server_start')
async def register_db(app, loop):
    app.pool = await create_pool(**DB_CONFIG, loop=loop, max_size=30)
    async with app.pool.acquire() as connection:
        app.tables = {r[0]: r[1] for r in await connection.fetch(
            """SELECT table_name, table_type FROM INFORMATION_SCHEMA.tables WHERE table_schema='public' AND table_type IN ('BASE TABLE','VIEW');""")}
        matviews = await connection.fetch("SELECT matviewname FROM pg_matviews WHERE schemaname = 'public'")
        app.tables.update({x[0]: 'VIEW' for x in matviews})
    app.pre_process = {}
    for importer, modname, ispkg in pkgutil.iter_modules(pre_process.__path__):
        # print("Found submodule %s (is a package: %s)" % (modname, ispkg))
        m = importer.find_module('pre_process.' + modname).load_module('pre_process.' + modname)
        app.pre_process[modname] = m
    app.post_process = {}
    for importer, modname, ispkg in pkgutil.iter_modules(post_process.__path__):
        # print("Found submodule %s (is a package: %s)" % (modname, ispkg))
        m = importer.find_module('post_process.' + modname).load_module('post_process.' + modname)
        app.post_process[modname] = m


@app.listener('before_server_stop')
async def close_db(app, loop):
    await app.pool.close()
    await redis.close()


@app.middleware('request')
async def add_session_to_request(request):
    request["uuid"] = uuid.uuid1().hex
    # before each request initialize a session
    # using the client's request
    if request.cookies.get("session") and request.headers.get('Token'):
        request.cookies["session"] = request.headers.get('Token')
    elif request.cookies.get('session') and not request.headers.get('Token'):
        pass
    elif not request.cookies.get('session') and request.headers.get('Token'):
        request.cookies["session"] = request.headers.get('Token')
        
    await session_interface.open(request)
    # check token for current user
    token = request.headers.get('Token')
    if token is not None and not ALLOW_MULTI_LOGIN:
        login_source = request.get('session').get('login_source', 'BPMN')
        uid_key = f"token/{login_source}/{request.get('session').get('uid')}"
        _redis = await redis.get_redis_pool()
        online_token = await _redis.get(uid_key)
        if online_token is not None and online_token != token:
            request['session'].clear()
    # load user
    if request["session"].get('uid'):
        await app.loaduser(request)
        # if request['user'] is None or request.get('user').get('staff_role_name') is None:#handler for diffrent app's session confused
        if request['user'] is None:  # handler for diffrent app's session confused
            request['user'] = {'staff_role_name': ['ANONYMOUS']}
    else:
        request['user'] = {'staff_role_name': ['ANONYMOUS']}


@app.middleware('response')
async def save_session(request, response):
    # after each request save the session,
    # pass the response to set client cookies
    await session_interface.save(request, response)
    if request.get('login') and response.cookies.get('session'):
        user = dict(request.get('login').items())
        token = response.cookies.get('session').value
        response.body = json(
            {'status': 0, 'data': {'token': token, 'profile': {k: user[k] for k in user if k != 'password'}}}).body
        ###set token for current login user
        login_source = request.get('session').get('login_source', 'BPMN')
        uid_key = f"token/{login_source}/{request.get('session').get('uid')}"
        _redis = await redis.get_redis_pool()
        await _redis.setex(uid_key, 31536000, token)

# @app.exception(ServerError)
# #@app.exception(NameError)
# def catch_500(request, exception):
#     log.error(''.join(traceback.format_exception(*sys.exc_info())))
#     return text('500', status=500)
