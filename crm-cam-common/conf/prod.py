# -*- coding: utf-8 -*-

PARAM_FOR_MYSQL = dict(
    database="db_neocam",
    host='',
    port=3306,
    user='',
    password='',
    charset='utf8mb4',
    max_connections=5,
    ssl=None,
)

PARAM_FOR_VIEW = dict(
    database="db_neocam",
    host='',
    port=3306,
    user='',
    password='',
    charset='utf8mb4',
    max_connections=5,
    ssl=None,
)


PARAM_FOR_MYSQL_CRM = dict(
    database="db_neocrm",
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
