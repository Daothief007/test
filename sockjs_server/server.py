# -*- coding: utf-8 -*-
"""
    sockjs server.

    :author: weiee.
    :date: 2017.02.13
"""

import json
import tornado.ioloop
import tornado.web

import sockjs.tornado

ADDRESS = None
PORT = 18080
RT = 'iU0OukcfBqafG7i9hchPzd'

clients_id_token = {}
clients_token_id = {}
clients_session = {}


class ConnInit(tornado.web.RequestHandler):
    def post(self):
        global clients_id_token
        global clients_token_id
        try:
            data = json.loads(self.request.body.decode('utf-8'))
        except ValueError:
            self.write({'status': 1, 'data': 'invalid json.'})
            return
        if not ('rt' in data and data.get('rt') == RT):
            self.write({'status': 2, 'data': 'Without authorization.'})
            return
        if not ('user_id' in data and 'token' in data):
            self.write({'status': 3, 'data': '"user_id" and "token" is requried.'})
            return
        uid = str(data.get('user_id'))
        if uid not in clients_id_token:
            clients_id_token[uid] = set()
        clients_id_token[uid].add(data.get('token'))
        clients_token_id[data.get('token')] = uid
        self.write({'status': 0})


class PushMsg(tornado.web.RequestHandler):
    def post(self):
        global clients_id_token
        global clients_session
        try:
            data = json.loads(self.request.body.decode('utf-8'))
        except ValueError:
            self.write({'status': 1, 'data': 'invalid json.'})
            return
        if not ('rt' in data and data.get('rt') == RT):
            self.write({'status': 2, 'data': 'Without authorization.'})
            return
        if not ('user_id' in data and 'content' in data):
            self.write({'status': 3, 'data': '"user_id" and "content" is requried.'})
            return
        if str(data.get('user_id')) not in clients_id_token:
            self.write({'status': 4, 'data': 'user with this user_id is not init.'})
            return
        user_current_sessions = set()
        for i in clients_id_token[str(data.get('user_id'))]:
            if i in clients_session:
                user_current_sessions.add(clients_session[i])
        user_current_sessions = list(user_current_sessions)
        if len(user_current_sessions) > 0:
            user_current_sessions[0].broadcast(user_current_sessions, data.get('content'))
        self.write({'status': 0})


class ChatConnection(sockjs.tornado.SockJSConnection):
    global clients_token_id
    global clients_session

    def on_open(self, info):
        if self.session.session_id not in clients_token_id:
            return False
        clients_session[self.session.session_id] = self

    def on_message(self, message):
        pass

    def on_close(self):
        if self.session.session_id in clients_token_id:
            uid = clients_token_id[self.session.session_id]
            clients_id_token[uid].remove(self.session.session_id)
            del clients_session[self.session.session_id]


if __name__ == "__main__":
    import logging
    logging.getLogger().setLevel(logging.DEBUG)

    ChatRouter = sockjs.tornado.SockJSRouter(ChatConnection, '/sockjs/conn')

    app = tornado.web.Application(
            [(r"/sockjs/init", ConnInit), (r"/sockjs/push", PushMsg)] + ChatRouter.urls
    )

    logging.info("socksjs server is started.")
    
    app.listen(PORT, address=ADDRESS or '127.0.0.1')
    tornado.ioloop.IOLoop.instance().start()

