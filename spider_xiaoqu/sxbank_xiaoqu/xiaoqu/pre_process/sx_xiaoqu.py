from utils.LFHelper import ok,fail
from trump.query import get_items,get_item
async def ls(app,request):
    param = request.args
    if param.get("name"):
        param["name-like"] = param.pop("name")
    res = await get_items(app.pool,"sx_xiaoqu",args=param,with_total=True,pager=True)
    result = list()
    for each in res[1]:
        item = dict()
        for key in each:
            if key == 'id' or key == "name" or key=="onsell" or key == "onrent" or key == "house_type" or key == "price_image":
                item[key] = each[key]
        xq = await get_item(app.pool,"sx_xqdetail",oid=each['id'],column="xq_id")
        if xq:
            item["price"] = xq.get("month_price") if xq.get("month_price") else None
        else:
            item["price"] = None
        result.append(item)
    return ok((res[0],result))
