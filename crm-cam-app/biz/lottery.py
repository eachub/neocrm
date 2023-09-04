# -*- coding: utf-8 -*-
from urllib.parse import urlencode

from peewee import DoesNotExist
from common.models.cam import LotteryRecord
from mtkext.db import sql_printf, sql_execute, safe_string
from datetime import datetime, timedelta
from decimal import Decimal
from sanic.log import logger

from common.utils.const import RC
from common.utils.probability import AliasMethods
import numpy as np
import numpy.random as npr
import uuid
from mtkext.db import FlexModel
from biz.campaign import record_campaign


class DrawLottery():
    def __init__(self, app, campaign_info):
        self.app = app
        self.campaign_info = campaign_info
        self.cid = campaign_info["campaign_id"]
        self.LEFT_COUNT_KEY_PRE = "neocam_lottery_left_count"
        self.init_lottery()
        lottery_record_cls = FlexModel.get(LotteryRecord, self.cid)
        self.table_name = lottery_record_cls._meta.table_name
        self.lottery_record_cls = lottery_record_cls
        logger.info(f"init table name: {self.table_name}")
        logger.info(f"init record cls: {self.lottery_record_cls}")

    def init_lottery(self):
        campaign_info = self.campaign_info
        logger.info(f"init lottery: {self.campaign_info}")
        self.lottery_conf = campaign_info.get('detail', {})
        self.lottery_way = self.lottery_conf.get('lottery_way')
        self.lottery_item = self.lottery_conf.get('lottery_item', [])
        self.count_all = sum([int(item['qty']) for item in self.lottery_item])
        self.lottery_p_list = [item['probability'] for item in self.lottery_item] if self.lottery_way == 2 else [round(int(item['qty']) / self.count_all, 4) for item in self.lottery_item]
        logger.info(f"{self.cid}: lottery_p_list: {self.lottery_p_list}")
        if self.lottery_way == 1:
            self.lottery_p_list[-1] = float(Decimal('1') - Decimal(str(sum([Decimal(str(self.lottery_p_list[i])) for i in range(len(self.lottery_p_list) - 1)]))))
        logger.info(f"{self.cid}: lottery_p_list: {self.lottery_p_list}")
        self.probs = np.array(self.lottery_p_list)
        self.alias = AliasMethods()
        self.alias_a, self.prob_a = self.alias.alias_setup(self.probs)


    async def handle_lottery_times(self, member_no):
        """
        抽奖次数控制，抽奖时用
        :param member_no: 会员号
        :param campaign_info: 活动信息
        :return:
        """
        campaign_info = self.campaign_info
        cid = campaign_info["campaign_id"]
        lottery_conf = campaign_info["detail"] or {}
        lottery_schedule = lottery_conf.get('lottery_schedule', {})
        interval, schedule_interval, total_times, schedule_times = lottery_schedule.get('interval'), lottery_schedule.get('schedule_interval', 1), int(
            lottery_schedule.get('total_times', 0)), lottery_schedule.get('schedule_times')
        _schedule_times = await self.get_lottery_record_times(member_no, schedule=interval, schedule_interval=schedule_interval)
        draw_times = await self.get_lottery_record_times(member_no)
        logger.info(f'抽奖次数 conf total_time:{total_times} draw_times:{draw_times} schedule_times:{schedule_times} _schedule_times:{_schedule_times}')
        if (total_times and int(total_times) <= draw_times) or (int(schedule_times) and int(schedule_times) <= int(_schedule_times)):
            logger.warning(f"{cid} {member_no} has draw {draw_times}: {total_times} conf: {interval} {_schedule_times}:{schedule_times}")
            return False, 0
        return True, int(schedule_times) - int(_schedule_times) if int(schedule_times) else -1

    def get_schedule_times(self):
        lottery_conf = self.campaign_info["detail"] or {}
        lottery_schedule = lottery_conf.get('lottery_schedule', {})
        schedule_times = lottery_schedule.get('schedule_times')
        return schedule_times if int(schedule_times) else -1 # -1 不限制抽奖次数

    async def get_remain_times(self, member_no):
        lottery_conf = self.campaign_info["detail"] or {}
        lottery_schedule = lottery_conf.get('lottery_schedule', {})
        schedule, schedule_interval, schedule_times = \
            lottery_schedule.get('interval'), lottery_schedule.get('schedule_interval', 1), \
            lottery_schedule.get('schedule_times')
        record_times = await self.get_lottery_record_times(member_no, schedule, schedule_interval)
        logger.info(f"record_times: {record_times}, schedule_times: {schedule_times}")
        return int(schedule_times) - int(record_times) if int(schedule_times) else -1 # -1 不限制抽奖次数

    async def get_lottery_record_times(self, member_no, schedule=None, schedule_interval=None):
        now_data = datetime.now()
        table_name = self.table_name
        sql = safe_string(f"select auto_id from {table_name} where member_no = '{member_no}'")
        if not schedule:
            sql = sql
        elif schedule == "minutes" and schedule_interval:
            sql = f"{sql} and (create_time between '{now_data - timedelta(minutes=int(schedule_interval))}' and '{now_data}')"
        elif schedule == "day":
            sql = f"{sql} and (create_time between '{now_data - timedelta(days=int(schedule_interval))}' and '{now_data}')"
        else:
            return []
        sql = str(sql)
        query = self.lottery_record_cls.raw(sql)
        _ans = await self.app.mgr.execute(query)
        return len(_ans)

    async def get_lottery_record(self, member_no, page_id=1,page_size=10):
        _cls = self.lottery_record_cls
        lottery_records = await self.app.mgr.execute(
            _cls.select().where(_cls.campaign_id == int(self.cid), _cls.member_no == member_no)\
            .order_by(_cls.update_time.desc())\
            .paginate(page_id, page_size).dicts())
        logger.info(f'{member_no}得到领奖记录: {len(lottery_records)}')
        return lottery_records

    async def start_lottery(self,  member_no, utm_source=""):
        """
        判断消费积分在适配层
        抽奖回调, 先判断抽奖次数，再抽奖，然后扣库存
        :param member_no:
        :param all_args:
        :param channel:
        :param _data:
        :return:
        """
        logger.info(f'开始抽奖')
        cid = self.cid
        campaign_info = self.campaign_info
        if not member_no:
            logger.warning(f"{cid} start_lottery no member_no: {member_no}")
            return False, dict(code=RC.MEMBER_ERROR, msg="非会员")
        logger.info(f'开始查询已抽次数')
        left, _ = await self.handle_lottery_times(member_no)
        logger.info(f'次数查询完成')

        if not left:
            logger.error(f"{member_no} has no left times for {cid} lottery")
            return False, dict(code=RC.LIMIT_ERROR, msg="抽奖次数已经用完")
            # return self.get_return_modal(1, "抽奖次数已用完", False, pop_type)  # 如何展示报错信息
        lottery_conf = campaign_info.get("detail",{})
        # lottery_item = lottery_conf.get("lottery_item")
        # order_info = dict(prize_count=len(lottery_item))
        logger.info('查询neoapp 实例id')
        instance_id = campaign_info["instance_id"]
        # 抽奖
        prize_index = self.alias.alias_draw_auto(self.alias_a, self.prob_a)
        prize_info = self.lottery_item[prize_index]
        prize_no = prize_info.get('prize_no')
        prize_key = f"{self.LEFT_COUNT_KEY_PRE}_{cid}_{prize_no}"
        default_item = {}
        for l_item in self.lottery_item:
            if l_item.get('is_default'):
                default_item = l_item
        if not default_item:
            logger.error(f"{cid} no default item")
        consume_count = await self.app.redis.incr(prize_key)
        if consume_count > int(prize_info.get('qty')):  # 所抽中商品没有库存的话采用默认奖品（可为未中奖）（自动计算概率的会有问题）
            logger.error(f"{self.cid} {member_no} draw {consume_count} but no count left")
            await self.app.redis.decr(prize_key)
            default_id = default_item.get('prize_no')
            if not default_id:
                logger.error("未配置默认奖品，抽奖失败:%s" % (self.campaign_info))
                return False, dict(code=RC.PRIZE_ERROR, msg="抽奖失败")
            await self.app.redis.incr(f"{self.LEFT_COUNT_KEY_PRE}_{self.cid}_{default_id}")  # 默认奖品是否需要扣库存
            prize_info = default_item
        prize_type, goods_info = prize_info.get('type'), prize_info.get('goods_info', {})
        if not prize_type or prize_type not in [1, 2, 3, 4]:
            logger.error(f"{self.cid} wrong prize type: %s" % prize_info)
            return False, dict(code=RC.PRIZE_ERROR, msg="抽奖失败")
        lottery_data = dict(
            campaign_id= cid,
            instance_id=instance_id,
            member_no=member_no,
            lottery_config=lottery_conf,
            lottery_info=prize_info,
            lottery_type=prize_type,
            prize_no=prize_info.get('prize_no'),
            utm_source=utm_source
        )
        _cls = self.lottery_record_cls
        created = await self.app.mgr.create(_cls, **lottery_data)
        lottery_data["auto_id"] = created.auto_id
        event_type = 1 if prize_type == 3 else 2
        to_cam_record = {
            "campaign_id": self.cid,
            "member_no": member_no,
            "instance_id": instance_id,
            "campaign_type": self.campaign_info.get("campaign_type"),
            "event_type": event_type,
            "utm_source": utm_source,
        }
        if prize_type != 3:
            to_cam_record['prize_conf'] = goods_info
        logger.info(f"created: {created}")
        #if created:
        await record_campaign(self.app.mgr, to_cam_record)
        return True, dict(code=0,msg="ok",data=dict(lottery_data=lottery_data))


    def get_member_interval_key(self, member_no):
        campaign_info = self.campaign_info
        cid = campaign_info["campaign_id"]
        lottery_conf = campaign_info["detail"] or {}
        lottery_schedule = lottery_conf.get('lottery_schedule', {})
        interval = lottery_schedule.get('interval')
        interval_period = ""
        if interval == 'day':
            interval_period = datetime.now().strftime("%Y%m%d")
        member_interval_key = f"{self.LEFT_COUNT_KEY_PRE}_{cid}_{member_no}_{interval}_{interval_period}"
        return member_interval_key



    async def lock_lottery_draw(self, member_no):
        """
        计算活动库存，计算用户限制，计算返回需要扣取的积分
        :param member_no:
        :return:
        """
        logger.info(f'开始预先抽奖计算')
        # 1. 增加redis中的会员的今天的key，如果增加结果等于1，查询数据库的记录，将数据库中的记录的今天的条数加到redis中的key
        # key组成
        schedule_times = self.get_schedule_times()
        cid = self.cid
        points = self.campaign_info["detail"]["lottery_consume"]["points"]
        if schedule_times == -1:
            logger.info(f"{cid}活动不限制抽奖次数")
            return True, {"points": points, "remain_times": schedule_times}

        member_key = self.get_member_interval_key(member_no)
        consume_count = await self.app.redis.incr(member_key)
        await self.app.redis.expire(member_key, 24 * 3600)
        logger.info(f"{member_key} incr result: {consume_count}")
        if consume_count == 1:
            campaign_info = self.campaign_info
            lottery_conf = campaign_info["detail"] or {}
            lottery_schedule = lottery_conf.get('lottery_schedule', {})
            interval, schedule_interval = lottery_schedule.get('interval'), lottery_schedule.get('schedule_interval', 1)
            _schedule_times = await self.get_lottery_record_times(
                member_no, schedule=interval, schedule_interval=schedule_interval)
            consume_count = await self.app.redis.incrby(member_key, _schedule_times)

        # 2. 计算增加后的值，如果大于抽奖次数限制，返回失败
        if schedule_times < consume_count:
            await self.app.redis.decr(member_key)
            return False, {"points": points, "remain_times": 0}
        # 3. 如果满足抽奖次数限制，返回剩余次数和需要扣除的积分值
        return True, {"points": points, "remain_times": schedule_times - consume_count}

    async def unlock_lottery_draw(self, member_no):
        """
        退还预锁定的抽奖次数
        :param member_no:
        :return:
        """
        logger.info(f'开始预先抽奖计算回退')
        schedule_times = self.get_schedule_times()
        cid = self.cid
        if schedule_times == -1:
            logger.info(f"{cid}活动不限制抽奖次数")
            return True, {"remain_times": schedule_times}
        member_key = self.get_member_interval_key(member_no)
        consume_count = await self.app.redis.decr(member_key)
        await self.app.redis.expire(member_key, 24 * 3600)
        logger.info(f"{member_no} decr result: {consume_count}")
        if consume_count == -1:
            campaign_info = self.campaign_info
            lottery_conf = campaign_info["detail"] or {}
            lottery_schedule = lottery_conf.get('lottery_schedule', {})
            interval, schedule_interval = lottery_schedule.get('interval'), lottery_schedule.get('schedule_interval', 1)
            _schedule_times = await self.get_lottery_record_times(
                member_no, schedule=interval, schedule_interval=schedule_interval)
            logger.info(f"_schedule_times: {_schedule_times}")
            consume_count = await self.app.redis.incrby(member_key, _schedule_times)
        if consume_count == -1:
            consume_count = await self.app.redis.incr(member_key)
        return True, {"remain_times": schedule_times - consume_count}

