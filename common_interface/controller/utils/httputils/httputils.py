import aiohttp
import asyncio
import uuid
import logging
from logging.handlers import RotatingFileHandler
import os
import traceback
import datetime,json

# 60 seconds default timeout
DEFAULT_TIMEOUT = 60


class ClientRequest:
    def __init__(self,
                 name=None,
                 log_file='/srv/log/httputils.log',
                 log_maxbytes=104857600,
                 log_backup_count=10,
                 log_level=logging.INFO,
                 log_formatter=logging.Formatter(fmt='%(asctime)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S')):
        if name is None:
            name = uuid.uuid1().hex
        dir = os.path.dirname(log_file)
        if not os.path.isdir(dir):
            os.makedirs(dir)
        logger = logging.getLogger(name)
        # logger.propagate = False  # 设置禁止发送日志到RootLogger
        logger.setLevel(logging.INFO)
        ch = RotatingFileHandler(log_file, maxBytes=log_maxbytes, backupCount=log_backup_count)
        ch.setLevel(log_level)
        ch.setFormatter(log_formatter)
        logger.addHandler(ch)
        self.logger = logger

    async def post(self, url, data, headers=None, timeout=DEFAULT_TIMEOUT):
        req_id = uuid.uuid1().hex
        current = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.info(f"post[{req_id}]:begin:{current}\t{url}\t{data}\t{headers}")
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                result = await session.post(url, timeout=timeout, data=data)
                result_text = await result.text()
            except asyncio.TimeoutError as e:
                self.logger.info(f"post[{req_id}]:end: err:[Connection timeout(timeout={timeout})]")
                raise (e)
            except Exception as e:
                self.logger.error(f"post[{req_id}]:end: err:[{traceback.format_exc()}]")
                raise (e)
            current = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.logger.info(f"post[{req_id}]:end:{current}, content=[{result_text}], result=[{result}] ")
            return result

    async def get(self, url,data=None, headers=None, timeout=DEFAULT_TIMEOUT, **kwargs):
        req_id = uuid.uuid1().hex
        current = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.info(f"get[{req_id}]:begin: {current}\t{url}\t{headers}")
        print('xxxxxxxxxxxxxxxxxx')

        if data:
            url_params = ""
            data = json.loads(data)
            # print(data)
            for x in data:
                url_params = url_params + x + "=" + data[x]
                url_params = url_params + "&"
            if url_params:
                url = url+"?"+url_params[:-1]
            print(url, '--------------------------', data)
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                print(url,'============')
                result = await session.get(url, data=kwargs, timeout=timeout)
                result_text = await result.text()
            except asyncio.TimeoutError as e:
                self.logger.info(f"get[{req_id}]:end: err:[Connection timeout(timeout={timeout})]")
                raise (e)
            except Exception as e:
                self.logger.error(f"get[{req_id}]:end: err:[{traceback.format_exc()}]")
                raise (e)
            current = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.logger.info(f"get[{req_id}]:end: {current}, content=[{result_text}], result=[{result}] ")
            return result

    async def put(self, url, data, headers=None, timeout=DEFAULT_TIMEOUT):
        req_id = uuid.uuid1().hex
        self.logger.info(f"put[{req_id}]:begin: {url}\t{data}\t{headers}")
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                result = await session.put(url, timeout=timeout, data=data)
                result_text = await result.text()
            except asyncio.TimeoutError as e:
                self.logger.info(f"put[{req_id}]:end: err:[Connection timeout(timeout={timeout})]")
                raise (e)
            except Exception as e:
                self.logger.error(f"put[{req_id}]:end: err:[{traceback.format_exc()}]")
                raise (e)
            self.logger.info(f"put[{req_id}]:end: content=[{result_text}], result=[{result}] ")
            return result

    async def options(self, url, data, headers=None, timeout=DEFAULT_TIMEOUT):
        req_id = uuid.uuid1().hex
        self.logger.info(f"put[{req_id}]:begin: {url}\t{data}\t{headers}")
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                result = await session.options(url, timeout=timeout, data=data)
                result_text = await result.text()
            except asyncio.TimeoutError as e:
                self.logger.info(f"options[{req_id}]:end: err:[Connection timeout(timeout={timeout})]")
                raise (e)
            except Exception as e:
                self.logger.error(f"options[{req_id}]:end: err:[{traceback.format_exc()}]")
                raise (e)
            self.logger.info(f"options[{req_id}]:end: content=[{result_text}], result=[{result}] ")
            return result