# 世联接口
# coded by weiee.
# 2017.04.01
import redis
import requests
import datetime
import json
import logging
import shutil
from redis import Redis
import aiohttp
from sanic_session import RedisSessionInterface
import asyncio_redis
# from config import UPLOAD_PATH
import base64

# from controller.config import UPLOAD_PATH, UPLOAD_PATH_ORIGINAL

logging.basicConfig(
    format='%(asctime)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S',
    level=logging.INFO,
)
logging.getLogger("requests").setLevel(logging.WARNING)
# redis_pool = redis.ConnectionPool(host='redis', port=6379, db=0)
# redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0)



class SL:
    # URL = "http://test.worldunion.cn:8620/"
    # USER = "Test"
    # PASSWORD = "Test123"
    token = None
    URL = "http://io.worldunion.cn:8620/"
    USER = "KangRDUser"
    PASSWORD = "KangRDUserPwd"
    # token = None
class Redis:
    """
    A simple wrapper class that allows you to share a connection
    pool across your application.
    """
    _pool = None

    async def get_redis_pool(self):
        try:
            from controller.config import REDIS_CONFIG
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
try:
    redis = Redis()
    session_interface = RedisSessionInterface(redis.get_redis_pool)
except:
    print('- - Use InMemorySessionInterface')
async def get_token(refresh_token=False):
    # rds = redis.StrictRedis(connection_pool=redis_pool)
    rds = await redis.get_redis_pool()
    if not refresh_token:
        t = await rds.get('sl/token')
        if t:
            return t
    try:
        res = await post(SL.URL + 'QueryPrice/Login', {
            "UserName": SL.USER,
            "Password": SL.PASSWORD,
        })
    except Exception as e:
        logging.info(e)
        return
    t = res.get('Token')
    if not t:
        logging.info(res)
        return
    await rds.setex(
        'sl/token',
        2592000,
        t,
    )
    return t






async def call_api(api_name, method='post', params=None, refresh_token=False):
    print(api_name, method, params,'nnnnnnnnnnnnnnnnnnnnnnnnn')
    headers = {"Authorization": 'Basic {}'.format(await get_token(refresh_token=refresh_token))}
    ret = None
    try:
        if method == 'get':
            ret = await get(SL.URL + api_name, headers=headers)
            print(ret,'''';;;;;;;;;;;;;;;;;;;;;;;;''')
        elif method == 'post':
            ret = await  post(SL.URL + api_name, params, headers=headers)
            print(ret)
    except Exception as e:
        print(e)
        return
    if "Message" in ret and ret.get("Message") == "Authorization has been denied for this request.":
        print(api_name, method, params)
        call_api(api_name, method, refresh_token=True)
    return ret


# 根据楼盘名称查询楼盘
async def loupan_list(city_id, name):
    print(city_id, name,'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
    return await call_api('QueryPrice/GetConstruction/{}/{}'.format(city_id, name), method='get')


# 根据楼盘ID查询楼栋
async def loudong_list(construction_id):
    return await call_api('QueryPrice/GetBuild/{}'.format(construction_id), method='get')


# 根据楼栋ID 获取该楼栋的全部房号信息
async def fanghao_list(build_id):
    return await call_api('QueryPrice/GetHouse/{}'.format(build_id), method='get')


# 估价， 根据楼盘ID，楼栋ID，房号ID 建筑面积
async def gujia(cid, bid, hid, area, case_id):
    return await call_api('QueryPrice/AutoPrice/{}/{}/{}/{}/{}'.format(cid, bid, hid, area, case_id), method='get')


# 人工估价
async def rg_gujia(case_id, address, build_area, city_id, area_id, type_code, house_card_no, project_name, house_type,
                   end_date, remark, total_floor, on_floor):
    data = {"CaseID": case_id, "Address": address, "BuildArea": build_area, "CityID": city_id, "AreaID": area_id,
            "TypeCode": type_code, "HouseCardNo": house_card_no, "ProjectName": project_name, "HouseType": house_type,
            "EndDate": end_date, "Remark": remark, "TotalFloor": total_floor, "OnFloor": on_floor}
    print(data)
    return await call_api('QueryPrice/GetQueryPrice', params=data, method='post')


async def get_price(case_id):
    return await call_api(f'QueryPrice/GetQueryPriceData?CaseId={case_id}', method='get')


# 询价单
async def xujiadan(case_id):
    r = requests.get(SL.URL + 'QueryPrice/PrintInfo/{}'.format(case_id),
                     headers={"Authorization": 'Basic {}'.format(await get_token())})
    # r = await aiohttp_fetch.get(SL.URL + 'QueryPrice/PrintInfo/{}'.format(case_id), headers={"Authorization": 'Basic {}'.format(await get_token())})
    # async with aiohttp.ClientSession(headers={"Authorization": 'Basic {}'.format(await get_token())}) as session:
    #     result = await session.get(SL.URL + 'QueryPrice/PrintInfo/{}'.format(case_id))
    #     print(result)
    #     return await result.content
    return r.content

async def save_xujiadan(case_id):
    chunk_size = 1024
    ls_f = ''
    # today = datetime.datetime.now()
    # filepath = os.path.join(UPLOAD_PATH, today.strftime('%Y%m%d'))
    # if not os.path.isdir(filepath):
    #     os.mkdir(filepath)
    # ori_filepath = os.path.join('', today.strftime('%Y%m%d'))
    # if not os.path.isdir(ori_filepath):
    #     os.mkdir(ori_filepath)
    # filename = f'{filepath}/{case_id}.'
    try:
        async with aiohttp.ClientSession(headers={"Authorization": 'Basic {}'.format(await get_token())}) as session:
            result = await session.get(SL.URL + 'QueryPrice/PrintInfo/{}'.format(case_id))
            # print(await result.content.read(chunk_size))
            # print(await get_token())
            with open('./file.' + "tmp", 'wb+') as fd:
                while True:
                    chunk = await result.content.read(chunk_size)
                    if not chunk:
                        break
                    fd.write(chunk)
            with open('./file.' + "tmp",'rb') as fb:
                ls_f = base64.b64encode(fb.read())
                print('ls_f', ls_f)
                fb.close()
                return ls_f

            # shutil.copyfile('file' + 'tmp', os.path.join(
            #     ori_filepath,
            #     case_id + ".jpg"),
            #                 )
            # shutil.copyfile(filename + 'tmp', filename + "jpg")
            # url = os.path.join(today.strftime('%Y%m%d'), f'{case_id}.jpg')
            # print('url',url)


    except Exception as e:
        logging.info(e)
        return


async def area_id(city_id):
    # r = requests.get(SL.URL + 'QueryPrice/Areas/{}'.format(city_id),
    #                  headers={"Authorization": 'Basic {}'.format(await get_token())})
    r = await get(SL.URL + 'QueryPrice/Areas/{}'.format(city_id),
                                headers={"Authorization": 'Basic {}'.format(await get_token())})
    return r.content


async def sl_province_export():
    items = []
    for province in await call_api('QueryPrice/Provinces', method='get'):
        items.append(province)
    return items


async def sl_city_export():
    items = []
    for province in await call_api('QueryPrice/Provinces', method='get'):
        for city in await call_api('QueryPrice/Citys/{}'.format(province.get('Id')), method='get'):
            items.append(city)
    return items


async def sl_area_export(city_id):
    items = []
    # for province in await call_api('QueryPrice/Provinces', method='get'):
    #     for city in await call_api('QueryPrice/Citys/{}'.format(province.get('Id')), method='get'):
    #         for area in await call_api('QueryPrice/Areas/{}'.format(city.get('Id')), method='get'):
    #             items.append(area)
    for area in await call_api('QueryPrice/Areas/{}'.format(city_id), method='get'):
        items.append(area)
    return items


# GET QueryPrice/GetHouse/{id}
# GET QueryPrice/GetBuild/{id} 根据楼盘ID获取楼栋列表
# GET QueryPrice/GetConstruction/{city}/{name}
# 更具楼盘名称，城市ID 获取该城市的楼盘列表
# GET QueryPrice/Provinces
# 获取所有省份信息
# GET QueryPrice/Citys
# 获取所有城市信息
# GET QueryPrice/Citys/{id}
# 根据省份获取城市
# GET QueryPrice/AutoPrice/{cid}/{bid}/{hid}/{area}/{caseId} 获取自动估价结果 根据楼盘ID，楼栋ID，房号ID 建筑面积，
# GET QueryPrice/GetConstrutionViewInfoById/{conid}   根据楼盘ID获取楼盘详情
# GET QueryPrice/GetBuild/{id} 根据楼盘ID获取楼栋列表
# GET QueryPrice/GetHouse/{id} 根据楼栋ID 获取该楼栋的全部房号信息
if __name__ == '__main__':
    for p in call_api('QueryPrice/Provinces', method='get'):

        # print(p.get('Name'))
        for c in call_api('QueryPrice/Citys/{}'.format(p.get('Id')), method='get'):
            for a in call_api('QueryPrice/Areas/{}'.format(c.get('Id')), method='get'):
                print("({}, '{}', {}, {}, {}),".format(a.get('Id'), a.get('Name'), a.get('GBCode'), a.get('PId'),
                                                       a.get('Type')))
    # x = call_api('QueryPrice/GetConstruction/1/金园', method='get')
    # print(x)
    # print(SL.token)
    # call_api('QueryPrice/GetConstrutionViewInfoById/262146', method='get')
    # call_api('QueryPrice/GetBuild/262146', method='get')
    # call_api('QueryPrice/GetHouse/2129235', method='get')

    # call_api('QueryPrice/AutoPrice/262146/2129235/80650181/100.8/1', method='get')
    # call_api('QueryPrice/GetConstruction/74/昌运大厦', method='get')
    # call_api('QueryPrice/GetConstrutionViewInfoById/262146', method='get')
    # call_api('QueryPrice/GetBuild/261142', method='get')
    # call_api('QueryPrice/GetHouse/2133324', method='get')
    # call_api('QueryPrice/AutoPrice/261142/2133324/80783056/400.8/1', method='get')
    # call_api('QueryPrice/GetConstruction/74/昌运大厦', method='get')
    # call_api('QueryPrice/GetConstrutionViewInfoById/262146', method='get')
    # call_api('QueryPrice/GetBuild/241', method='get')
    # call_api('QueryPrice/GetHouse/695', method='get')
    x = call_api('QueryPrice/AutoPrice/1/695/1045801/400.8/1', method='get')
    print(x)



async def post(url, data, headers=None):
    async with aiohttp.ClientSession(headers=headers) as session:
        result = await session.post(url, data=data)
        return await result.json()


async def get(url, headers=None, **kwargs):
    async with aiohttp.ClientSession(headers=headers) as session:
        result = await session.get(url, data=kwargs)
        print(result,'sssssssssssssssssssssssssssssssss')
        result = await result.read()
        print('----------------------await result.read()',url,result)
        return json.loads(result)
        # return await result.json()
