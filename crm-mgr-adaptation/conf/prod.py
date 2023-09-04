URL_PREFIX = "/api/crm/mgr"

CRM_SERVER_URL = "http://eros-crm-mgr.default"
CRM_APP_SERVER_URL = "http://eros-crm-app.default"

COOKIE_NAME = '__neoeros_uuid__'

CMS_CLIENT = dict(
    host='http://127.0.0.1:52870',
    prefix='/api/cms',
)

CAM_CLIENT = dict(
    host='http://127.0.0.1:21600/mn',
    prefix='/api/cam/mgr',
)

WSM_DOMAIN = 'http://127.0.0.1:12001/api/transfer'

WX_DATA_HOST = "http://127.0.0.1:9100"


# 为CRM打标签使用
CRM_PARAM_MYSQL = dict(
    database="db_neocrm",
    user='',
    password='',
    host='',
    port=3306,
    charset='utf8mb4',
    max_connections=1,
)

OMNI_GATEWAY_URL = "http://127.0.0.1:31300"

PARAM_FOR_MYSQL = dict(
    database="db_neocrm_adapt",
    user='',
    password='',
    host='',
    port=3306,
    charset='utf8mb4',
    max_connections=1,
)

PARAM_FOR_REDIS = dict(
    address=("", 6379),
    db=0,
    password="",
    minsize=1,
    maxsize=2,
)

CRM_URL_PREFIX = 'https://dev.eachub.cn'
CRM_H5_PREVIEW = "/vendor/mtsdk/pages/web-view/index?url=https%3A%2F%2Fdev.quickshark.cn%2Fcrmh5%3F"
ACCESS_TOKEN_URL = "http://127.0.0.1:33101/omni/tools/fetch_token?appid={}"

KC_CLIENT_PARAM = dict(
    server_url="https://dev.eachub.cn/keycloak/",
    realm_name="",
    user_realm_name="",
    client_id="CRM",
    client_secret_key='',
    redirect_uri=f""
)

HOME_PATH = "/console/neocrm"
UPLOAD_DIR = "/opt/nfs/neocrm"

MQ_CRM_TASK = "neocrm_queue"

MQ_CRM_ADAPT_TASK = "neocrm_adapt"