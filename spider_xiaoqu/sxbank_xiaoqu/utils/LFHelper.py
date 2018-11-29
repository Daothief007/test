from sanic.response import json
def ok(data):
    if type(data) == tuple:
        return json({'data':{'list':data[1],'total':data[0]},'status':0})
    elif type(data) == list:
        return json({"data": {"list": data}, "status": 0})
    else:
        return json({"data": data, "status": 0})


def fail(data):
    return json({"data": data, "status": 1})

def deleteKeys(param,keys):
    if param is None:
        return param
    param = param.copy()
    if type(keys) != list or type(param) != dict:
        raise TypeError(f"{keys} is not list or param is not dict")
    for key in keys:
        if key in param.keys():
            del param[key]
    return param

