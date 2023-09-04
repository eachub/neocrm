#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def date_add_day(s, count=1):
    """字符串格式日期加天数并返回字符串格式日期"""
    return (datetime.strptime(s, '%Y-%m-%d') + timedelta(days=count)).strftime('%Y-%m-%d')


def date_add_month(s, count=1):
    """字符串格式日期加月份并返回字符串格式日期"""
    return (datetime.strptime(s, '%Y-%m-%d') + relativedelta(months=count)).strftime('%Y-%m-%d')


def get_month_start(y, m):
    """返回某月第一天(字符串格式)"""
    return (datetime(y, m, 1)).strftime('%Y-%m-%d')


def get_month_start_stamp(y, m):
    """返回某月第一天(时间戳格式)"""
    return int(time.mktime(datetime(y, m, 1).timetuple()))


if __name__ == '__main__':
    print(get_month_start_stamp(2022, 4))
