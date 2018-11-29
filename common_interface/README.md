#  common_interface 外部接口整合项目



`项目说明`: 整合如 小区查询,世联查询,身份证识别,大数据查询等接口的调用方式, 用通用的方式取调用无关业务的接口.

`项目名称`: **common_interface**

`git地址`: **[链接](http://git.yaoyingli.cn/kangruide/common_interface.git "git地址")**


------------



------------


`调用方式`:

|  接口名称 | 调用方式(HTTP_METHOD)  | 调用效果 | 参数 |
| ------------ | ------------ | ------------ | ------------ |
| /api/common/<接口名称>  | POST  |  返回调用接口数据 | {} |
| /api/common/<接口名称>  | OPTIONS  | 返回调用接口使用说明 | 无 |

`备注`: 所有接口调用方式为POST方式,详情查看方式为 OPTIONS方式


------------


------------


`现有接口列表`:

|  接口名称 | 接口说明  | 传入参数 |
| ------------ | ------------ | ------------ |
| sx_xiaoqu  | 网查评估小区列表接口  | {"city_id":"城市行政编码","area":"住房面积","provid":"省会行政编码"} |   |
| sx_xqdetail | 网查评估小区详情接口  | {"id":"住房ID"} |   |
| sx_xqdeal  | 网查评估小区信息接口  | {"id":"住房ID"} |   |
| idcard_ocr  |  推送接口 |  {"rt":"iU0OukcfBqafG7i9hchPzd","user_id":"用户ID","token":"生成的uuid"} |   |
| add_user  | 身份证识别接口  | {"正面"：{"url":"base-64编码","card_type":0},"反面"：{"url":"base-64编码","card_type":1}}|   |
| sx_xqdeal  |  大数据add接口 | {"mobile":"手机号码","idcard":"身份证号码","name":"姓名"} |   |
| raw_api_data  | 大数据raw接口  | {"mobile":"手机号码","idcard":"身份证号码"} |   |


