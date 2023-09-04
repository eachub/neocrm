#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import time
import ujson
from datetime import datetime, timedelta


def is_valid_date(s):
    """校验是否是合法的日期"""
    try:
        time.strptime(s, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def is_valid_time(s):
    """校验是否是合法的时间"""
    try:
        time.strptime(s, '%Y-%m-%d %H:%M:%S')
        return True
    except ValueError:
        return False


def start_less_end(s, e, t='time'):
    """校验开始时间是否先于结束时间"""
    if t == 'date':
        assert is_valid_date(s) and is_valid_date(e), '日期不合法'
        s, e = time.strptime(s, '%Y-%m-%d'), time.strptime(e, '%Y-%m-%d')
    elif t == 'time':
        assert is_valid_time(s) and is_valid_time(e), '时间不合法'
        s, e = time.strptime(s, '%Y-%m-%d %H:%M:%S'), time.strptime(e, '%Y-%m-%d %H:%M:%S')
    else:
        assert False, '只支持日期、时间类型'
    return s <= e


def date_delta(begin_date, end_date):
    """返回开始日期与结束日期的日期间隔, 如果值不合法或开始日期大于结束日期，返回-1"""
    try:
        begin_date, end_date = datetime.strptime(begin_date, '%Y-%m-%d'), datetime.strptime(end_date, '%Y-%m-%d')
        delta = (end_date - begin_date).days
        if delta < 0: return -1
        return delta
    except ValueError:
        return -1


def date_slice(begin_date, end_date, days=1):
    """返回开始日期与结束日期的日期切片列表, 包含结束日期, 默认间隔为1天"""
    try:
        date_list = []
        begin_date, end_date = datetime.strptime(begin_date, '%Y-%m-%d'), datetime.strptime(end_date, '%Y-%m-%d')
        while begin_date <= end_date:
            date_list.append(str(begin_date.date()))
            begin_date += timedelta(days=days)
        return date_list
    except ValueError:
        return []


def time_slice(hours=1):
    time_list = []
    for i in range(0, 24, hours):
        time_list.append('{0:02d}:00'.format(i))
    return time_list


if __name__ == '__main__':
    print(date_slice('2021-10-11', '2021-10-12', days=2))
