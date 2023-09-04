# -*- coding: utf-8 -*-
import sys
from collections import defaultdict
from mtkext.db import safe_string, sql_printf
sys.path.insert(0, '..')

from datetime import datetime, date
from common.utils.check import date_slice

from common.models.cam import CampaignInfo as raw_model
from common.models.cam import StatCalData, StatRegionData
from stats.analyze_mysql import *

from biz.sqltask import MySQLTaskBase, main
from sanic.log import logger



async def mysql_gen_campaign_data(mgv, from_time, to_time, tdate, thour, dim_sql_li=None, extra_conds=None, **kwargs):
    # 构造sql获取数据
    if not extra_conds:
        extra_conds = safe_string("1=1")
    else:
        extra_conds = safe_string(extra_conds)
    rows_list = []
    tdate_str = datetime.strftime(tdate, "%Y-%m-%d")
    table_date = tdate_str.replace('-', '')
    table_date = safe_string(table_date)
    for tmp_sql in dim_sql_li or []:
        sql = sql_printf(tmp_sql, tdate=tdate, thour=thour, table_date=table_date,
                         from_time=from_time, to_time=to_time, extra_conds=extra_conds)
        logger.info(f'汇总-sql:{sql}')
        try:
            items = await mgv.execute(raw_model.raw(sql).dicts())
            logger.info(len(items))
        except Exception as ex:
            logger.info(ex)
            logger.info(f"{sql} execute error")
            items = []
        for i in items:
            cid = i.get('cid')
            if cid:
                rows_list.append(i)

    return rows_list


class StatTask(MySQLTaskBase):

    async def make_tasks(self):
        return [
            (mysql_gen_campaign_data, StatCalData, dict(dim_sql_li=[
                q_visit_user,
                q_join_user,
                q_accept_user,
                q_share_user, q_register_user_cid
            ])),
            (mysql_gen_campaign_data, StatRegionData, dict(dim_sql_li=[q_province_city_by_cid])),
        ]


if __name__ == '__main__':
    main(StatTask, parallel=False)
