COMMON_DB = "db_neocrm"

PARAM_FOR_VIEW = dict(
    database="db_neocrm",
    user='',
    password='',
    host='',
    port=3306,
    charset='utf8mb4',
    max_connections=4,
)

PARAM_FOR_MYSQL = dict(
    database="db_neocrm",
    user='',
    password='',
    host='',
    port=3306,
    charset='utf8mb4',
    max_connections=4,
)

PARAM_FOR_REDIS = dict(
    address=("", 6379),
    db=0,
    password="",
    minsize=1,
    maxsize=4,
)
# 券码队列 前缀
CRM_COUPON_CODE_QUEUE_FORMAT = "CRM_{crm_id}_COUPON_{card_id}_CODE"

WSM_DOMAIN = 'http://127.0.0.1:11011/api/transfer'

SUPPORT_PLATFORM = ["wechat", "alipay", "douyin", 'tmall']

MQ_CRM_TASK = "neocrm_queue"

MQ_CRM_ADAPT_TASK = "neocrm_adapt"
OMNI_GATEWAY_URL = "http://127.0.0.1:31300"

INSTANCE_ID = "neocrm001"

# 拉取商品地址
PARAMS_FOR_MALL_CLIENT = dict(
    url_prefix="http://app-mall.default",
    mall_id=18000
)

# cam-app 服务 获取活动信息
CAM_CLIENT = dict(
    url_prefix='http://neocrm-cam-app.default/mn',
    sub_url='/api/cam/mgr',
    instance_id='neocrm001',
)

# 获取小程序名称使用
CMS_CLIENT = dict(
    host='http://neocrm-mgr-cms.default',
    prefix='/api/cms',
    instance_id="neocrm001",
)