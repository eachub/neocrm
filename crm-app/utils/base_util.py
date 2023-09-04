import random
import string
from datetime import datetime, timedelta
from sanic.log import logger
from decimal import Decimal
import time

from mtkext.regex import is_mobile

hexs = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L',
        'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']


class Utils:
    d_format_str = "%Y-%m-%d"
    dt_format_str = "%Y-%m-%d %H:%M:%S"

    @staticmethod
    def date_to_str(n_date):
        return datetime.strftime(n_date, Utils.d_format_str)

    @staticmethod
    def datetime_to_str(n_datetime):
        return datetime.strftime(n_datetime, Utils.dt_format_str)

    @staticmethod
    def get_dict_args(data, *args):
        return data.get(args[0], None) if len(args) == 1 else [data.get(arg, None) for arg in args]

    @staticmethod
    def get_default_params(data, **params):
        res = [data.get(key, value) for key, value in params.items()]
        if len(res) == 1:
            return res[0]
        return res

    @staticmethod
    def format_region(region):
        if region.endswith('省') or region.endswith('市'):
            return region[:-1]
        return region

    @staticmethod
    def generate_random_str(length=6):
        return ''.join(random.sample(string.ascii_letters + string.digits, length))

    @staticmethod
    def transfer_hex(number, hex=36):
        """十进制整数转换为其他进制"""
        try:
            number = int(number)
        except Exception as ex:
            return number
        if hex < 2 or hex > 36:
            return ""
        if number < hex:
            return str(hexs[number])
        dis, numbers = number, ''
        while dis > hex:
            remain = dis % hex
            dis = dis // hex
            numbers = f"{hexs[remain]}{numbers}"
        return f"{hexs[dis]}{numbers}"

    @staticmethod
    def hide_mobile(mobile):
        if mobile and is_mobile(mobile):
            return mobile[:7]
        else:
            return mobile

    @staticmethod
    def check_birthday(birthday):
        try:
            birthday = datetime.strptime(birthday, Utils.d_format_str)
            if birthday > datetime.now():
                return False
            return True
        except Exception as ex:
            return False

    @staticmethod
    def filter_null(data):
        new_data = dict()
        for key, value in data.items():
            if not value:
                continue
            new_data[key] = value
        return new_data

    # str 转datetime.date  eg: str_time='2019-07-12'
    @staticmethod
    def str_to_datetimeDate(str_time):
        from datetime import date
        return date(*map(int, str_time.split('-')))

    @staticmethod
    def current_date_ymd():
        """
        获取当前时间 Y-M-D
        :return:
        """
        try:
            return time.strftime('%Y-%m-%d', time.localtime())
        except Exception as ex:
            logger.exception(ex)
            return '0000-00-00'

    @staticmethod
    def current_date_format(_format):
        """
        获取当前时间 Y-M-D
        :return:
        """
        try:
            return time.strftime(_format, time.localtime())
        except Exception as ex:
            logger.exception(ex)
            return '0000-00-00'

    @staticmethod
    def decimal_mul(left, right, scale=0):
        """
        将二个高精确度数字相乘
        :param left:
        :param right:
        :param scale:
        :return:
        """
        _exp = '0' if scale <= 0 else '0.' + ('0' * scale)
        return (Decimal(str(left)) * Decimal(str(right))).quantize(Decimal(_exp))

    @staticmethod
    def decimal_add(left, right, scale=2):
        """
        将二个高精确度数字相加
        :param left:
        :param right:
        :param scale:
        :return:
        """
        _exp = '0' if scale <= 0 else '0.' + ('0' * scale)
        return (Decimal(str(left)) + Decimal(str(right))).quantize(Decimal(_exp))

    @staticmethod
    def decimal_sub(left, right, scale=2):
        """
        将二个高精确度数字相减
        :param left:
        :param right:
        :param scale:
        :return:
        """
        _exp = '0' if scale <= 0 else '0.' + ('0' * scale)
        return (Decimal(str(left)) - Decimal(str(right))).quantize(Decimal(_exp))

    @staticmethod
    def decimal_div(left, right, scale=2):
        """
        将二个高精确度数字相除
        :param left:
        :param right:
        :param scale:
        :return:
        """
        _exp = '0' if scale <= 0 else '0.' + ('0' * scale)
        _right = Decimal(str(right))
        if _right == 0:
            return False
        return (Decimal(str(left)) / _right).quantize(Decimal(_exp))

    @staticmethod
    def decimal_comp(left, right):
        """
        将二个高精确度数字相比较
        :param left:
        :param right:
        :return:
        """
        _left = Decimal(str(left))
        _right = Decimal(str(right))
        if _left < _right:
            return -1
        elif _left == _right:
            return 0
        else:
            return 1

    @staticmethod
    def decimal_format(s, scale=2):
        """
        格式化浮点数保留scale位小数
        :param s:
        :param scale:
        :return:
        """
        _exp = '0' if scale <= 0 else '0.' + ('0' * scale)
        return Decimal(str(s)).quantize(Decimal(_exp))

    @staticmethod
    def decimal_to_int(_d):
        """
        decimal 转int 只保留整数部位
        :param _d:
        :return int:
        """
        list_d = str(_d).split('.')
        return int(list_d[0])

    @staticmethod
    def plus_some_day(end_time, _day):
        '''
        当前天数 + _day
        :param end_time: 开始时间
        :param _day: + 天数
        :return:
        '''
        new_day = datetime.strptime(end_time[0:10], "%Y-%m-%d") + timedelta(days=_day)
        return new_day.strftime("%Y-%m-%d 23:59:59")

    @staticmethod
    def easy_time():
        """
        获取当前时间
        :return:
        """
        return int(time.time())

    @staticmethod
    def current_time():
        """
        获取当前时间戳
        :return:
        """
        try:
            return int(time.time())
        except Exception as ex:
            logger.exception(ex)
            return 0

    @staticmethod
    def format_timestamp(date_format='%Y-%m-%d %H:%M:%S', timestamp=None):
        """
        时间戳格式化成指定格式的时间
        :param date_format:
        :param timestamp:
        :return:
        """
        if timestamp == '0000-00-00': return ''
        if timestamp is None:
            timestamp = Utils().easy_time()
        timestamp = int(timestamp)
        if timestamp <= 0:
            return ''
        return time.strftime(date_format, time.localtime(timestamp))

    @staticmethod
    def create_sring(sn_prefix="EACH"):
        """
        创建随机单号
        :param sn_prefix:
        :return:
        """
        import uuid
        _uid4 = str(uuid.uuid4()).replace('-', '')
        _str = ''
        for _u in _uid4:
            _str += str(ord(_u))
        return sn_prefix + Utils().format_timestamp('%y%m%d%H%M%S') + (str(int(time.clock() * 1000000))[:-4] + _str)[:16]

