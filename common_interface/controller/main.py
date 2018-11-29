from sanic import Sanic
from sanic import Blueprint
import time, json as jsonbase, re,logging, sys
from logging import StreamHandler
from sanic.response import json
from controller.config import HOST_URL,DB_CONFIG_PRE
from controller.utils.db_conection.oracle_db.query import create_pools,get_items
from controller.utils.httputils.httputils import ClientRequest
from controller.utils.shilian import call_api,save_xujiadan
conf_format =  ' [ %(asctime)-15s ]  - %(name)s -   %(levelname)s -  %(pathname)s[line : %(lineno)d] - FUNNAME : [%(funcName)s]  -  MESSAGE : %(message)s  	'
app = Sanic(__name__)
url_prefix = '/api/common'
bp = Blueprint(__name__)
bp.url_prefix = url_prefix


logging.basicConfig(
    level=logging.INFO,
    format=conf_format)
logger = logging.getLogger(__name__)

httputils = ClientRequest()
request_method = {"POST": httputils.post, "GET": httputils.get}

# API detail
@bp.route('/<name:[A-Za-z0-9/._]+>', methods=["OPTIONS"])
async def detail(request, name):
    result = await get_items(app.pool, 'tp_api', {"name": name})
    return json({"status":0,"data":result})


# API unified call method
@bp.route('/<name:[A-Za-z0-9/._]+>', methods=["POST"])
async def detail(request, name):
    '''
    :param request: request info
    :param name: request api name
    :return: api response info
    '''

    result = await get_items(app.pool, 'tp_api', {"name": name})
    print('世聯估價',"------------------------"+name,result)
    if result:
        params = request.json
        result = result[0]
        x = len(result.get('params'))
        result.get('params').update(params)
        y = len(result.get('params'))
        if x > y:
            return json({"status": 1, "data": "", "msg": "传入参数有误"})
        try:

            print(result.get("name")[0:2], 'result.get("name")[0:2]')
            if result.get("name")[0:2]=="sl":
                url=result.get("url")
                if result.get("name")=="sl_loupan" and x==2:
                    url=url+'/{}/{}'.format(params.get("city_id"), params.get("name"))
                if result.get("name")=="sl_gujia" and x==5:
                    url=url+'/{}/{}/{}/{}/{}'.format(params.get("cid"),params.get("bid"),params.get("hid"),params.get("area"),params.get("case_id"))
                if result.get("name")=="sl_loudong" and x==1:
                    url=url+'/{}'.format(params.get("cid"))
                if result.get("name")=="sl_fanghao" and x==1:
                    url=url+'/{}'.format(params.get("bid"))
                print('------------main',url)
                data=await call_api(url,method="get")
                return json(data)
            else:
                result = await request_method[result['http_method']](HOST_URL+result.get("url"), data=jsonbase.dumps(params), headers={"Content-Type": "application/json"})
        except Exception as e:
            return json({"status": 1, "msg": f"访问出错:{e}", "data": None})
        if result and result.headers['Content-Type'] in ["text/html","text/html; charset=utf-8"] :
            pattern = re.compile('.*?<center><h1>(.*?)<.*?')
            html_page =  await result.text()
            print(type(html_page), html_page)
            match = re.findall(pattern,html_page)
            if match:
                return json({"status":1, "msg":match[0],"data":None})
            pattern = re.compile('.*?<b>InterfaceError(.*?)<.*?')
            match = re.findall(pattern, html_page)
            if match:
                return json({"status": 1, "msg": match[0], "data": None})

            return json({"status": 1, "msg": html_page, "data": None})
        elif result and result.headers['Content-Type'] in ["application/json", "text/plain; charset=utf-8"]:
            temp_v = await result.text()
            print(await result.text())
            logger.info(await result.text(),'------------------======',result.headers['Content-Type'],  result)
            response_data = await result.json()
            return json({"status": 0, "msg":"获取成功","data":response_data})

        else:
            return json({"status": 0, "msg": f"不支持的返回数据类型,:{result.headers['Content-Type']}", "data": None})
    else:

        return json({"status":1,"data":None, "msg":"该接口不存在"})


@app.listener('before_server_start')
async def register_db(app, loop):
    '''
    :param app: sanic main start
    :param loop: uvloop
    :return: None
    '''
    app.pool = await create_pools(loop, **DB_CONFIG_PRE)
    print(app.pool)


# async def is_xunjiadan(case_id):
#     result = await sl_get_price(case_id)
#     if not result:
#         return False
#     if result.get("ReturnCode") not in (16, 17, 18):
#         await is_xunjiadan(case_id)
#     # if result.get("ReturnCode") == 18:
#     #     return False
#     return True






app.blueprint(bp)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9881, debug=True)
    print('xxxx')