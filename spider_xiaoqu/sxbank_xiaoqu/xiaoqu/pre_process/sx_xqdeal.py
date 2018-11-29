from utils.LFHelper import ok,fail,deleteKeys
from trump.query import get_items
async def ls(app,request):
    params = request.args
    if not params.get("id"):return fail("没有小区id")
    params["xq_id"] = params.pop("id")
    total,res = await get_items(app.pool,"sx_xqdeal",args=params,with_total=True,pager=True)
    for index,item in enumerate(res):
        houseInfo = dict()
        houseInfo["struc"] = item.pop("struc")
        houseInfo["high"] = item.pop("high")
        houseInfo["face"] = item.pop("face")
        item["house_info"] = houseInfo
        res[index] = deleteKeys(item, ["create_at", "update_at"])
    return ok((total,res))
