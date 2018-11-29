from utils.LFHelper import ok,fail,deleteKeys
from trump.query import get_item,get_items
import datetime
from config import SURROUNDING,FACILITIES,BASIC_INFORMATION,GRADE
async def ls(app,request):
    param = request.args
    xq_id = param.get("id")
    if not xq_id :
        return fail("id参数没有")
    try:
        xq_id = int(xq_id)
    except:
        return fail("id不为数字")
    dbXq = await get_item(app.pool, "sx_xqdetail", oid=xq_id, column="xq_id")
    if dbXq is None:
        return ok(dict())
    oriXq = deleteKeys(dbXq, ["create_at", "update_at"])
    xqResult = []
    reverseBasic = {value: key for key, value in BASIC_INFORMATION.items()}
    for key in oriXq:
        if key in reverseBasic.keys():
            if key == "mom" or key == "yoy":

                if  oriXq[key] is not None:

                    if oriXq[key].strip() == "%":
                        oriXq[key] = None
            item = dict()
            item["name"] = reverseBasic[key]
            item["content"] = oriXq[key]
            xqResult.append(item)

    mapInfo =[]
    if param.get("position") == "1":
        map = await get_item(app.pool,"sx_xqmap",oid=xq_id,column="xq_id")
        if map:
            if map.get("px") is not None and map.get("px") != "" and map.get("py") is not None and map.get("py") != "":
                mapInfo = [map.get("px").strip("\""),map.get("py").strip("\"")]
    trendInfo = dict()
    if param.get("trend") == "1":
        trend = await get_item(app.pool,"sx_xqtrend",oid=xq_id,column="xq_id")
        # print(trend)
        if trend:
            #处理价格趋势
            xq = await get_item(app.pool,"sx_xiaoqu",oid=xq_id,column="id")
            city = await get_item(app.pool,"sx_city",oid=xq.get("city_id"),column="city_id")
            area = await get_item(app.pool,"sx_area",oid=xq.get("area_id"),column="area_id")
            xqName = xq.get("name")
            cityName = city.get("name")
            areaName = area.get("name")
            trendInfo["date"] =handleDate(trend.get("during"))
            trendInfo["price_list"] = [
                {
                    "name":xqName,
                    "data":await clearTrendsLines(trend.get("xq_line"))
                },
                {
                    "name": areaName,
                    "data": await clearTrendsLines(trend.get("area_line"))
                },
                {
                    "name": cityName,
                    "data": await clearTrendsLines(trend.get("city_line"))
                },

            ]
            # print(trendInfo["price_list"])


    dbFacilities = await get_item(app.pool, "sx_xqfacilities", oid=xq_id, column="xq_id")
    dbSurrounding = await get_item(app.pool, "sx_xqsurrounding", oid=xq_id, column="xq_id")
    dbNearby = await get_items(app.pool,"sx_xqnearby",args={"xq_id":xq_id})
    dbGrade = await get_item(app.pool,"sx_xqgrade",oid=xq_id,column="xq_id")
    dbImage = await get_items(app.pool,"sx_xqimage",args={"xq_id":xq_id})

    trendInfo = deleteKeys(trendInfo, ["id", "create_at", "update_at", "xq_id"])
    oriSurrounding = deleteKeys(dbSurrounding, ["id", "create_at", "update_at", "xq_id"])
    oriFacilities = deleteKeys(dbFacilities, ["id", "create_at", "update_at", "xq_id"])
    oriGrade=deleteKeys(dbGrade,["id","month_price","mom","yoy","create_at","update_at","xq_id"])
    oriImage = []
    for item in dbImage:
        oriImage.append(deleteKeys(item,["id","create_at","update_at","xq_id"]))
    oriNearby = []
    for item in dbNearby:
         oriNearby.append(deleteKeys(item,["id", "create_at", "update_at", "xq_id"]))

    try:
        grade = []
        reverseGrade = {value:key for key ,value in GRADE.items()}
        for key in oriGrade:
            if key in reverseGrade.keys():
                item = dict()
                item["name"] = reverseGrade[key]
                item["content"] = oriGrade[key]
                grade.append(item)
    except Exception as e:
        print(e)
        grade = []
    try:
        surrounding = []
        reverseSurrounding = {value:key for key,value in SURROUNDING.items()}
        for key in oriSurrounding:
            if key in reverseSurrounding.keys():
                item = dict()
                item["name"] = reverseSurrounding[key]
                item["content"] = oriSurrounding[key]
                surrounding.append(item)
    except Exception as e:
        print(e)
        surrounding = []
    try:
        facilities = []
        reverseFacilities = {value: key for key, value in FACILITIES.items()}
        for key in oriFacilities:
            if key in reverseFacilities.keys():
                item = dict()
                item["name"] = reverseFacilities[key]
                item["content"] = oriFacilities[key]
                facilities.append(item)
    except Exception as e:
        print(e)
        facilities = []
    try:
        image = []
        for each in oriImage:
            item = dict()
            item["name"] = each.get("name")
            item["image"] = each.get("path")
            item["url"] = each.get("image_url")
            image.append(item)
    except Exception as e:
        print(e)
        image = []
    try:
        nearby = []
        for each in oriNearby:
            item = dict()
            item["name"] = each.get("near_name")
            item["price"] = each.get("near_price")
            nearby.append(item)
    except Exception as e:
        print(e)
        nearby = []
    result = dict()

    result['basic'] = xqResult
    result["trend"] = trendInfo
    result["map"] = mapInfo
    result["surrounding"] = surrounding
    result["facilities"] = facilities
    result["nearby"] = nearby
    result["grade"] = grade
    result["image"] = image


    return ok(result)


async def clearTrendsLines(line):
    if not line:
        return line
    try:
        line = line.lstrip("[").rstrip("]")
        itemList = line.split("],[")
        priceList = []
        for item in itemList:
            price  = item.split(",")[1]
            priceList.append(price)
        return priceList
    except Exception as e :
        print(e)
        return []
def month_delta(start_date, end_date):
    """
    返回 end_date  - start_date  的差值
        :param start_date:
        :param end_date:
        :return:  month_delta   int
    """
    flag = True
    if start_date > end_date:
        start_date, end_date = end_date, start_date
        flag = False
    year_diff = end_date.year - start_date.year
    end_month = year_diff * 12 + end_date.month
    delta = end_month - start_date.month
    return -delta if flag is False else delta
def handleDate(during):
    start,end = during.split("-")
    y="年"
    m="月"
    startTime = datetime.datetime.strptime(start,f"%Y{y}%m{m}")
    endTime = datetime.datetime.strptime(end,f"%Y{y}%m{m}")
    result = []
    result.append(start)
    while True:
        if startTime.year == endTime.year:
            if startTime.month < endTime.month:
                start = datetime.datetime(startTime.year,startTime.month+1,startTime.day).strftime(f"%Y{y}%m{m}")
                startTime = datetime.datetime(startTime.year,startTime.month+1,startTime.day)
                result.append(start)
                continue
            else:
                break
        elif startTime.year < endTime.year:
            if startTime.month + 1 <= 12:
                start = datetime.datetime(startTime.year, startTime.month + 1, startTime.day).strftime(f"%Y{y}%m{m}")
                startTime = datetime.datetime(startTime.year, startTime.month + 1, startTime.day)
                result.append(start)
                continue
            elif startTime.month+1 > 12:
                start = datetime.datetime(startTime.year+1, 1, startTime.day).strftime(f"%Y{y}%m{m}")
                startTime = datetime.datetime(startTime.year+1, 1, startTime.day)
                result.append(start)
                continue
    return result

if __name__ == "__main__":
    print(handleDate('2016年07月-2018年08月'))

