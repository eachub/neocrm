# -*- coding: utf-8 -*-

URL_PREFIX = "/api/crm/cam"
OMNI_GATEWAY_URL = 'http://app-omni.default'
WOA_TOKEN_CLIENT_URL = ""
CRM_CLIENT_URL = "http://crm-app.default"
CAM_CLIENT_URL = "http://crm-cam-app.default"
ACCESS_TOKEN_URL = "http://127.0.0.1:52080/token/matrix/fetch?appid={}"


PARAM_FOR_MYSQL = dict(
    database="db_neocam_adapt",
    host='',
    port=3306,
    user='',
    password='',
    charset='utf8mb4',
    max_connections=5,
    ssl=None,
)

PARAM_FOR_REDIS = dict(
    address=("", 6379),
    db=0,
    password="",
    minsize=1,
    maxsize=4,
    ssl=None,
)
