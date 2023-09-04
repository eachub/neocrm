#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from enum import Enum


class CardType(Enum):
    """
    卡券类型
    """
    CASH_COUPON = 0  # 代金券
    DISCOUNT_COUPON = 1  # 折扣券
    EXCHANGE_COUPON = 2  # 兑换券
    FREE_SHIP_COUPON = 3  # 包邮券
    GIFT_COUPON = 4  # 赠品券

    @classmethod
    def get_card_type_values(cls):
        return [x.value for x in cls]


class CardSource(Enum):
    """
    卡券来源码表
    """
    CRM = 1  # crm 自制券
    WX_PAY = 2  # 微信商家券


class InterestsType(Enum):
    """
    卡券权益码表
    """
    QUOTA = 1  # 额度卡
    FREQUENCY = 2  # 频次卡

    @classmethod
    def get_values(cls):
        return [x.value for x in cls]


class InterestsPeriodType(Enum):
    """
    卡券权益周期类型码表
    """
    DAY = 1
    WEEK = 2
    MONTH = 3
    YEAR = 4

    @classmethod
    def get_values(cls):
        return [x.value for x in cls]


class CardDateType(Enum):
    """
    卡券日期模式码表
    """
    DURATION = 1  # 固定时段
    INTERVAL = 2  # 间隔动态时间
    PERMANENT = 3  # 永久

    @classmethod
    def get_card_date_type_values(cls):
        return [x.value for x in cls]


class CouponCodeGenStatus(Enum):
    """
    券码生成记录 码表
    """
    PENDING = 0  # 等待生成
    GENERATING = 1  # 生成中
    FINISH = 2  # 已完成


class CodeSourceTypeStatus(Enum):
    """
    券码生成方式
    """
    SYSTEM_GEN = 1  # 系统生成
    OUTER_IMPORT = 2  # 外部导入


class CouponCodeStatus(Enum):
    """
    券码状态
    """
    INACTIVE = 0  # 未激活
    ACTIVE = 1  # 已激活预存
    RECEIVED = 2  # 已领取
    INVALID = 3  # 已作废


class UserCardCodeStatus(Enum):
    """
    1.可用，2.转赠中，3.已核销，4.已过期，5.转赠已领取，6.已作废, 7.领取冲正【作废】
    """
    AVAILABLE = 1
    PRESENTING = 2
    REDEEM = 3
    EXPIRED = 4
    PRESENT_RECEIVED = 5
    INVALID = 6
    RECEIVE_REVERSE = 7


class UserPresentStatus(Enum):
    """
    1.转赠中，2.已领取，3.已退回, 4.过期退回
    """
    PRESENTING = 1
    RECEIVED = 2
    GOBACK = 3
    AUTO_GOBACK = 4
