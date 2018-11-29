
房天下二手房小区查询接口
==========================
本项目是基于`sanic`的框架项目，通过`爬虫`抓取房天下小区信息

----
### 第三方库

 `详见requirements.txt`

**以上第三方库，均可使用`pip install - r requirements.txt`进行安装**


----

### 接口详情

#### 1.小区列表获取接口(根据名字可模糊查询)

**接口功能**

获取各省市区小区的简单信息，可以模糊查询

**URL**

` /api / v1 / xiaoqu / sx_xiaoqu `

**支持格式**

JSON

**HTTP请求方式**

 GET

**请求参数**


|  参数         | 必选        | 类型       | 说明      |
|--------------- | :-----------: |:-----------:|:-----------:|
|  prov_id    | 否 | string | 省id |
|  city_id      | 否 | string | 市id |
|  area_id     | 否 | string | 区id |
|  page        | 是 | string | 页数 |
|  pagesize   | 否 | string | 每页多少数据(默认10条) |
|  name       | 否 | string | 模糊查询信息 |


**返回字段**

**success结构**
``` python
  {
            data: {
                 list: [
                        {
                            id: 21,
                            name: "安宁庭院",
                            onsell: "25",
                            onrent: "1",
                            house_type: "住宅",
                            price_image: null,
                            price: "15678"
                         }，
                            ...
                     ]
                total: 10  # 总数
            }
            status: 0  # 0为正常 1为错误 当为错误时 data中有错误提示
        }

  ```
**fail结构**

 ```python
 {
   "status": 1,
   "data": "错误信息"
 }
 请根据status判断data为对象或字符串
```

#### 2.小区详情

**接口功能**

获取指定小区详情

**URL**

` /api / v1 / xiaoqu / sx_xqdetail `

**支持格式**

 JSON

**HTTP请求方式**

GET

**请求参数**

|  参数         | 必选        | 类型       | 说明      |
|--------------- | :-----------: |:-----------:|:-----------:|
| id | 是 | string | 小区id |
| position | 否 | string | 是否需要小区地理位置 为1 则代表需要 无此字段或者不为1 则代表不要 |
| trend | 否 | string | 是否需要价格走势 为1 则返回此小区房价走势 无此字段或者不为1 则代表不要 |



```
参数说明: id为必要参数，只有id则提供小区基本信息，小区配套设施，小区周边信息 。
如果带有position，则提供地理位置坐标，如果带有trend，则返回走势信息。
```

**返回字段**

success结构
  ``` python
 {
    data: {
        basic: [
                {
                    name: "小区名称",
                    content: "中海·河山郡"
                },
                {
                    name: "小区地址",
                    content: "安宁区银滩大桥以西5分钟车程(武警甘肃..."
                },
                ....
                ],
        trend: {},
        map: [],
        surrounding: [
                {
                    name: "幼儿园",
                    content: "小博士幼儿园"
                },
                {
                    name: "中小学",
                    content: null
                },
                {
                    name: "大学",
                    content: null
                },
                {
                    name: "商场",
                    content: null
                },
                {
                    name: "医院",
                    content: null
                },
                {
                    name: "邮局",
                    content: null
                },
                {
                    name: "银行",
                    content: null
                },
                {
                    name: "其他",
                    content: null
                },
                {
                    name: "小区内部配套",
                    content: "1、中心园林的主题花园"
                },

        ],
        nearby: [...]
        facilities:[...]
        grade:[
                    {
                        name: "总评级",
                        content: "A"
                    },
                    {
                        name: "总评分",
                        content: "5"
                    },
                    {
                        name: "物业评级",
                        content: "B"
                    },
                    {
                        name: "物业评分",
                        content: "3"
                    }
                ],
       image[
               {
                   name:"小区名称"
                   path:"图片url"
                   url:"图片原地址"
               }


            ]

      },
      status: 0
}
     返回参数说明：basic, surrounding, facilities 内的参数较多，放在下方的附录帮助查看，
```

fail结构
 ```python
 {
   "status": 1,
   "data": "错误信息"
 }
 请根据status判断data为对象或字符串
```

#### 3.小区房屋出售成交信息
**接口功能**

 根据小区id查看小区历史成交信息

**URL**

` /api/v1/xiaoqu/sx_xqdeal`

**支持格式**

 JSON

**HTTP请求方式**

 POST

**请求参数**

|  参数         | 必选        | 类型       | 说明      |
|--------------- | :-----------: |:-----------:|:-----------:|
| id | 是 | string | 小区id |
| page | 是 | string | 页索引 |
| pagesize | 是 | string | 页数 |


**返回字段**

 success结构

```python
   {
            data:{
                list:[
                        {
                            house_info:
                                {struc:三室两厅,high:高层(共25)，face:南}
                            area:159.59
                            sign_time:2016-11-08
                            price:92万
                            per_price:5875元/m
                        }
                            ...
                     ]
                total:10 #总数
            }
            status:0 #0为正常 1为错误 当为错误时 data中有错误提示
        }
 ```
fail结构

```python
 {
   "status": 1,
   "data": "错误信息"
 }
```

# 附录
**小区返回值对照表**

```
basic = {
    "小区地址":"xq_address","所属区域":"xq_area","邮编":"post_code","环线位置":"circle_position",
    "产权描述":"property_right","物业类别":"estate_cate","建筑年代":"when_build","开发商":"developer","建筑结构":"building_structure",
    "建筑类型":"building_type","建筑面积":"building_area","占地面积":"floor_area","房屋总数":"house_total","楼栋总数":"building_total",
    "物业公司":"estate_company","绿化率":"green_rate","容积率":"plot ratio","物业办公电话":"estate_phone","物业费":"estate_price",
    "附加信息":"mark","物业办公地点":"estate_address",
}
```
 小区配套设施参数
```
facilities= {
    "供水":"water_supply","供暖":"heating_supply","供电":"electricity_supply","燃气":"gas","通讯设备":"CE","电梯服务":"elevator_service",
    "安全管理":"security_manage","卫生服务":" health_service","小区入口":"xq_gate","停车位":"parking",
}
```
周边信息
```
surrounding= {
    "幼儿园":"kindergarten","中小学":"junior","大学":"college","商场":"mall","医院":"hospital","邮局":"post_station","银行":"bank",
    "其他":"other","小区内部配套":"inxq","公交线路":"bus_routes","公交":"bus","商业":"business",
}
GRADE={
    "总评级":"grade",
    "总评分":"grade_score",
    "物业评级":"wuye_grade",
    "物业评分":"wuye_grade_score",
    "物业描述":"wuye_describe",
    "活跃度评级":"inactive_grade",
    "活跃度评分":"inactive_grade_score",
    "活跃度描述":"inactive_describe",
    "教育评级":"education_grade",
    "教育评分":"education_grade_score",
    "教育描述":"education_describe",
    "板块评级":"mapboard_grade",
    "板块评分":"mapboard_grade_score",
    "板块描述":"mapboard_describe",
}
```
