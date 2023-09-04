# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '..')

from common.biz.utils import make_time_range

from common.models.analyze import *
from common.models.analyze import StatUser as raw_model

from stats.member import *

from stats.points import *
from biz.sqltask import MySQLTaskBase, main


async def fetch_data_execute_function(mgv, from_time, to_time, tdate, thour, dim_sql_li, **params):

    pass


async def mysql_gen_customer_data(mgv, from_time, to_time, tdate, thour, dim_sql_li=None, extra_conds=None, **kwargs):
    # 查询多个sql 然后把指标汇总在一块
    if not extra_conds:
        extra_conds = safe_string("1=1")
    else:
        extra_conds = safe_string(extra_conds)
    rows_list = []
    for tmp_sql in dim_sql_li or []:
        sql = sql_printf(tmp_sql, tdate=tdate, thour=thour, from_time=from_time, to_time=to_time,
                         extra_conds=extra_conds)
        logger.info(f'客户分析-sql:{sql}')
        items = await mgv.execute(raw_model.raw(sql).dicts())
        logger.info(items)
        logger.info(len(items))
        for i in items:
            rows_list.append(i)

    return rows_list


async def mysql_gen_points_data(mgv, from_time, to_time, tdate, thour, dim_sql_li=None, extra_conds=None, **kwargs):
    if not extra_conds:
        extra_conds = safe_string("1=1")
    else:
        extra_conds = safe_string(extra_conds)
    rows_list = []
    for tmp_sql in [q_points_total1, q_points_total2, q_points_total3, q_points_total4,
                    q_points_total5, q_points_total6, q_points_total7, q_points_total8, q_points_total9]:
        sql = sql_printf(tmp_sql, tdate=tdate, thour=thour,
                        from_time=from_time, to_time=to_time, extra_conds=extra_conds)
        logger.info(f'积分分析-sql:{sql}')
        items = await mgv.execute(raw_model.raw(sql).dicts())
        logger.info(len(items))
        for i in items:
            rows_list.append(i)

    return rows_list


async def mysql_gen_campaign_data(mgv, from_time, to_time, tdate, thour, dim_sql_li=None, extra_conds=None, **kwargs):
    # 构造sql获取数据
    if not extra_conds:
        extra_conds = safe_string("1=1")
    else:
        extra_conds = safe_string(extra_conds)
    rows_list = []
    for tmp_sql in dim_sql_li or []:
        sql = sql_printf(tmp_sql, tdate=tdate, thour=thour,
                         from_time=from_time, to_time=to_time, extra_conds=extra_conds)
        logger.info(f'汇总-sql:{sql}')
        items = await mgv.execute(raw_model.raw(sql).dicts())
        logger.info(len(items))
        for i in items:
            rows_list.append(i)

    return rows_list


class StatTask(MySQLTaskBase):

    async def make_tasks(self):
        return [
            (mysql_gen_points_data, StatPoints, dict()),
            (mysql_gen_customer_data, StatUser, dict(dim_sql_li=[q_member_dim1, q_member_dim2,
                                                                 q_member_dim3, q_member_dim4])),
        ]


if __name__ == '__main__':
    main(StatTask, parallel=False)
