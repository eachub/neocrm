# -*- coding: utf-8 -*-

from mtkext.xlsx import XLSXBook
import os
import time
import ujson
from collections import defaultdict, OrderedDict
from inspect import isawaitable, getabsfile
import functools
from datetime import datetime, timedelta, date
from sanic.log import logger
from sanic.kjson import json_loads, json_dumps
from mtkext.cut import cut2
from playhouse.shortcuts import model_to_dict
from mtkext.db import peewee_normalize_dict, pop_matched_dict
from mtkext.db import sql_printf, sql_execute, safe_string


def chrec_to_dict(rec, excludes=set()):
    result = OrderedDict()
    for k, v in rec.items():
        if k in excludes: continue
        result[k] = v
    return result


def chrec_build_distr(items, key, excludes):
    distr = defaultdict(list)
    for rec in items:
        one = chrec_to_dict(rec, excludes=excludes)
        distr[rec[key]].append(one)
    return distr


def model_build_distr(ordered_items, key, excludes):
    distr = defaultdict(list)
    for i in ordered_items:
        one = model_to_dict(i, exclude=excludes)
        distr[getattr(i, key)].append(one)
    return distr


def model_build_key_map(ordered_items, key, excludes=None, only=None):
    distr = defaultdict()
    for i in ordered_items:
        one = model_to_dict(i, exclude=excludes, only=only)
        distr[getattr(i, key)] = one
    return distr


def model_build_distr2(ordered_items, key1, key2, excludes):
    distr = defaultdict(list)
    for i in ordered_items:
        one = model_to_dict(i, exclude=excludes)
        key = getattr(i, key1) + "|" + getattr(i, key2)
        distr[key].append(one)
    return distr


"""
要求：被装饰的函数的第一个参数必须是app（已准备好redis），
其中还有一个keyword-only argument：to_date（date类型）
"""


def cache_to_date(ttl=120):
    def warpper_(func):
        @functools.wraps(func)
        async def handler(app, *args, to_date, **kwargs):
            key, use_cache = "", (to_date < date.today())
            if use_cache:
                key = f"{func.__name__}@{getabsfile(func)}={':'.join(map(str, args))}:{to_date}:{kwargs}"
                got = await app.redis.get(key)
                if got:
                    logger.info(f"cache-hit: {key}")
                    return json_loads(got)
            result = func(app, *args, to_date=to_date, **kwargs)
            got = await result if isawaitable(result) else result
            if use_cache:
                logger.info(f"cache-new: {key}")
                await app.redis.setex(key, ttl, json_dumps(got))
            return got

        return handler

    return warpper_


def make_time_range(from_date, to_date, use_timestamp=0):
    if use_timestamp:
        from_time = int(time.mktime(from_date.timetuple()))
        to_time = int(time.mktime(to_date.timetuple())) + 86400
    else:
        from_time = f"{from_date:%Y-%m-%d} 00:00:00"
        tdate = to_date + timedelta(days=1)
        to_time = f"{tdate:%Y-%m-%d} 00:00:00"
    return from_time, to_time


async def logical_remove_record(mgr, ThatModel, **kwargs):
    where = []
    for key, val in kwargs.items():
        where.append(getattr(ThatModel, key) == val)
    return await mgr.execute(ThatModel.update({
        ThatModel.removed: True,
        ThatModel.update_time: datetime.now(),
    }).where(*where))


def write_to_excel(filepath, sheet_list):
    book = XLSXBook()
    for sheet_name, header, rows in sheet_list:
        t = book.add_sheet(sheet_name)
        if header: t.append_row(*header)
        for row in rows: t.append_row(*row)
    book.finalize(to_file=filepath)


def gen_excel_fileinfo(prefix=None):
    if not prefix:
        prefix=""
    fname = f"{prefix}{datetime.now():%Y%m%d%H%M%S-%f}.xlsx"
    fpath = os.path.join("target", fname)
    return fname, fpath


# 当日期数据为空时，补0
def full_date(from_date, to_date):
    if (to_date - from_date).days < 2:
        t, tdate, thour = from_date, [], []
        while t <= to_date:  # 没有数据点的填0
            for h in range(24):
                tdate.append(str(t))
                thour.append(f"{h:02d}")
            t += timedelta(days=1)
        return dict(tdate=tdate, thour=thour)
    else:
        t, tdate = from_date, []
        while t <= to_date:  # 没有数据点的填0
            tdate.append(str(t))
            t += timedelta(days=1)
        return dict(tdate=tdate)


def result_by_hour(items, from_date, to_date, key_list):
    item_dict = {f"{i.tdate}:{i.thour:02d}": i for i in items}
    result = {key: [] for key in key_list}
    t, tdate, thour = from_date, [], []
    while t <= to_date:  # 没有数据点的填0
        for h in range(24):
            one = item_dict.get(f"{t}:{h:02d}")
            for key in key_list:
                result[key].append(getattr(one, key, 0) if one else 0)
            tdate.append(str(t))
            thour.append(f"{h:02d}")
        t += timedelta(days=1)
    return dict(result, tdate=tdate, thour=thour, mode="by_hour")


def result_by_day(items, from_date, to_date, key_list):
    item_dict = {f"{i.tdate}": i for i in items}
    result = {key: [] for key in key_list}
    t, tdate = from_date, []
    while t <= to_date:  # 没有数据点的填0
        one = item_dict.get(f"{t}")
        for key in key_list:
            result[key].append(getattr(one, key, 0) if one else 0)
        tdate.append(str(t))
        t += timedelta(days=1)
    return dict(result, tdate=tdate, mode="by_day")


def fix_dict_result(tdict, val, layer):
    if layer == 0:
        return list(tdict.keys()) if val is None else [f"{a}::{b}" for a, b in tdict.items()]
    result = OrderedDict()
    for k, v in tdict.items():
        result[k] = fix_dict_result(v, val, layer - 1)
    return result


def gen_event_no(sn_prefix="EACH"):
    """创建随机事件no"""
    import uuid
    _uid4 = str(uuid.uuid4()).replace('-', '')
    _str = ''
    for _u in _uid4:
        _str += str(ord(_u))
    return sn_prefix + datetime.now().strftime('%Y%m%d%H%M%S') + (str(int(time.process_time() * 1000000))[:-4] + _str)[:12]
