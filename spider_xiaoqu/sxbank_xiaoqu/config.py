# server
DB_CONFIG = {
    'host': '192.168.1.11',
    'user': 'postgres',
    'password': 'postgres',
    'port': '5401',
    'database': 'ftx_crawler'
}
# REDIS_CONFIG = {'host': 'redis', 'port': 6379}

# # dev
# DB_CONFIG = {
    # 'host': '192.168.1.11',
    # 'user': 'postgres',
    # 'password': 'postgres',
    # 'port': '5401',
    # 'database': 'ftx_crawler'
# }
REDIS_CONFIG = {'host': 'localhost', 'port': 6379}


LOG_CONFIG = {
    'name': 'exmaple-bpmn',
    'output': 'std'
}

#allow_multi_login
ALLOW_MULTI_LOGIN = False
BASIC_INFORMATION = {
    "小区名称": "name",
    "本月均价":"month_price",
    "环比上月":"mom",
    "同比上年":"yoy",
    "小区地址": "xq_address",
    "所属区域": "xq_area",
    "邮编": "post_code",
    "环线位置": "circle_position",
    "产权描述": "property_right",
    "物业类别": "estate_cate",
    "建筑年代": "when_build",
    "开发商": "developer",
    "建筑结构": "building_structure",
    "建筑类型": "building_type",
    "建筑面积": "building_area",
    "占地面积": "floor_area",
    "房屋总数": "house_total",
    "楼栋总数": "building_total",
    "物业公司": "estate_company",
    "绿化率": "green_rate",
    "容积率": "plot_ratio",
    "物业办公电话": "estate_phone",
    "物业费": "estate_price",
    "附加信息": "mark",
    "物业办公地点": "estate_address",
}

FACILITIES = {
    "供水": "water_supply",
    "供暖": "heating_supply",
    "供电": "electricity_supply",
    "燃气": "gas",
    "通讯设备": "ce",
    "电梯服务": "elevator_service",
    "安全管理": "security_manage",
    "卫生服务": "health_service",
    "小区入口": "xq_gate",
    "停车位": "parking",
    "写字楼":"office_building"
}

SURROUNDING = {
    "幼儿园": "kindergarten",
    "中小学": "junior",
    "大学": "college",
    "商场": "mall",
    "医院": "hospital",
    "邮局": "post_station",
    "银行": "bank",
    "其他": "other",
    "小区内部配套": "inxq",
    "公交线路": "bus_routes",
    "公交": "bus",
    "商业": "business",
    "住宅": "residential",
    "酒店": "hotel",
    "餐饮": "catering",
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
