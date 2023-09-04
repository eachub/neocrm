import time
from collections import defaultdict
from datetime import timedelta, datetime

from mtkext.xlsx import XLSXBook
from playhouse.shortcuts import model_to_dict


def make_time_range(from_date, to_date, use_timestamp=0):
    if use_timestamp:
        from_time = int(time.mktime(from_date.timetuple()))
        to_time = int(time.mktime(to_date.timetuple())) + 86400
    else:
        from_time = f"{from_date:%Y-%m-%d} 00:00:00"
        tdate = to_date + timedelta(days=1)
        to_time = f"{tdate:%Y-%m-%d} 00:00:00"
    return from_time, to_time


def gen_event_no(sn_prefix="EACH"):
    """创建随机事件no"""
    import uuid
    _uid4 = str(uuid.uuid4()).replace('-', '')
    _str = ''
    for _u in _uid4:
        _str += str(ord(_u))
    print(_str)
    return sn_prefix + datetime.now().strftime('%Y%m%d%H%M%S') + (str(int(time.process_time() * 1000000))[:-4] + _str)[:12]


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


def write_to_excel(filepath, sheet_list):
    book = XLSXBook()
    for sheet_name, header, rows in sheet_list:
        t = book.add_sheet(sheet_name)
        if header: t.append_row(*header)
        for row in rows: t.append_row(*row)
    book.finalize(to_file=filepath)


def model_build_key_map(ordered_items, key, excludes):
    distr = defaultdict()
    for i in ordered_items:
        one = model_to_dict(i, exclude=excludes)
        distr[getattr(i, key)] = one
    return distr


def get_by_list_or_comma(args, key):
    items = args.getlist(key, [])
    return items if len(items) != 1 else [i.strip() for i in items[0].split(",")]


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


def masked_nickname(nickname):
    if nickname.startswith("特小益") and len(nickname) >= 7:
        nickname = "特小益***" + nickname[-4:]
        return nickname
    return None