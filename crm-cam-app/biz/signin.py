# -*- coding: utf-8 -*-
from urllib.parse import urlencode

import ujson
from peewee import DoesNotExist, SQL
from common.models.cam import LotteryRecord, Signin, model_to_dict
from mtkext.db import sql_printf, sql_execute, safe_string
from datetime import datetime, timedelta
from decimal import Decimal
from sanic.log import logger
from mtkext.db import FlexModel
from biz.campaign import record_campaign

class SignInGift():
    def __init__(self, app, campaign_info):
        self.app = app
        self.campaign_info = campaign_info
        self.cid = campaign_info["campaign_id"]
        self.init_signin()
        signin_record_cls = FlexModel.get(Signin, self.cid)
        logger.info(f"signin_record_cls: {signin_record_cls}")
        logger.info(f"signin_record_cls: {dir(signin_record_cls)}")
        self.table_name = signin_record_cls._meta.table_name
        logger.info(f"signin table name: {self.table_name}")
        self.signin_record_cls = signin_record_cls
        logger.info(f"init table name: {self.table_name}")
        logger.info(f"init record cls: {self.signin_record_cls}")

    def init_signin(self):
        campaign_info = self.campaign_info
        logger.info(f"init lottery: {self.campaign_info}")
        self.signin_conf = campaign_info.get('detail', {})
        self.signin_way = self.signin_conf.get('signin_way', 1) #1连续，2周期
        self.prize_conf = self.signin_conf.get('prize_conf', [])
        self.cache_key = "neocam_signin_info_713"


    async def get_signin_info(self, member_no, month=None):
        now_date = datetime.now().strftime("%Y%m%d")
        key = f"{self.cache_key}_{self.cid}_{member_no}_{now_date}"
        signin_info_redis = await self.app.redis.get(key)
        if signin_info_redis:
            return ujson.loads(signin_info_redis)
        signin_info = await self.get_member_signin_record(member_no, month)
        logger.info(f"signin_info: {signin_info}")
        await self.app.redis.setex(key, 24 * 60 * 60, ujson.dumps(signin_info))
        return signin_info

    def get_signin_text(self, signin_infos, latest_sign_day, now_day):
        count = 0
        week_count = 0
        month_count = 0
        signin_text = f"已连续签到"
        if self.signin_way == 1:  # 连续签到n天
            first_date = datetime.now().strftime("%Y%m%d") if latest_sign_day and latest_sign_day == now_day else (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
            flag = 0 if latest_sign_day and latest_sign_day == now_day else 1
            for i, signin_info in enumerate(signin_infos):
                logger.info(f"signin_info: {signin_info}, first_date: {first_date}, flag: {flag}, count: {count}")
                if datetime.strptime(signin_info["create_time"], "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d") == first_date:
                    count += 1
                    first_date = (datetime.now() - timedelta(days=flag + 1)).strftime("%Y%m%d")
                    logger.info(f"first_date: {first_date}, {count}, {flag}")
                    flag += 1
                else:
                    break
            #signin_text = f"已连续签到{count}天"
        elif self.signin_way == 2:  # 当月签到或者一周签到几天
            for schedule_item in self.prize_conf:
                schedule = schedule_item.get('schedule')
                if schedule == "month":
                    cur_month = datetime.now().strftime("%Y%m")
                    for i, signin_info in enumerate(signin_infos):
                        if datetime.strptime(signin_info["create_time"], "%Y-%m-%d %H:%M:%S").strftime("%Y%m") == cur_month:
                            week_count += 1
                    signin_text = f"累积签到"
                elif schedule == "week":
                    cur_week = datetime.now().weekday()
                    this_week = []
                    for i in range(7):
                        this_week.append(datetime.strftime(datetime.now() + timedelta(days=i - cur_week), "%Y%m%d"))
                    for i, signin_info in enumerate(signin_infos):
                        if datetime.strptime(signin_info["create_time"], "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d") in this_week:
                            month_count += 1
                    signin_text = f"累积签到"
        else:
            logger.error(f"signin_way error: {self.signin_way}")
        logger.info(f"get_signin_text: {count}, {week_count}, {month_count}, {signin_text}")
        count = max(count, week_count, month_count)
        return count, signin_text


    async def create_signin_record(self, _cls, insert_data):
        now_date = datetime.now().strftime("%Y%m%d")
        member_no = insert_data.get("member_no", "")
        created = await self.app.mgr.create(_cls, **insert_data)
        insert_data["auto_id"] = created.auto_id
        await self.app.redis.delete(f"{self.cache_key}_{self.cid}_{member_no}_{now_date}")
        return insert_data

    # 在适配层发送奖品，这里返回需要发送的奖品的信息
    async def handle_prize(self, count, member_no, latest_sign_day, now_day):
        count = count if latest_sign_day and latest_sign_day == now_day else count + 1

        logger.info(f"count: {count}")
        prize_result = []
        for prize_item in self.prize_conf:
            if int(prize_item['signin_days']) == count:
                item = prize_item['item']
                logger.info(f"prize_item:{item}")
                prize_result.extend(item)
        return prize_result


    def get_latest_sign_day(self, signin_infos):
        now_date = datetime.now().strftime("%Y%m%d")
        latest_sign_day = datetime.strptime(signin_infos[0]["create_time"], "%Y-%m-%d %H:%M:%S").strftime(
            "%Y%m%d") if signin_infos else {}
        return latest_sign_day, now_date

    async def signin(self, member_no, utm_source=None):
        # 加缓存（24h），读取缓存，每次更新数据，清除缓存
        if not member_no:
            logger.warning(f"{self.cid} signin no member_no")
            return False, dict(code=0, msg="非会员")
        signin_infos = await self.get_signin_info(member_no)
        logger.info(signin_infos)
        latest_sign_day, now_date = self.get_latest_sign_day(signin_infos)
        logger.info(f"signin_infos:{signin_infos} latest_sign_day:{latest_sign_day}, now_date:{now_date}")
        count, signin_text = self.get_signin_text(signin_infos, latest_sign_day, now_date)
        calendar = self.convert_member_calendar(signin_infos)
        if latest_sign_day and latest_sign_day == now_date:
            logger.warning(f"{self.cid} {member_no} has signined {now_date}")
            await self.app.redis.delete(f"{self.cache_key}_{self.cid}_{member_no}_{now_date}")
            return True, dict(code=0, data=dict(is_success=1, sign_in_days=count,
                                            calendar=calendar))
        # 写入签到记录
        _cls = self.signin_record_cls
        instance_id = self.campaign_info.get("instance_id")
        insert_data = dict(campaign_id=self.cid, instance_id=instance_id,
                           member_no=member_no, receive_prize=0, utm_source=utm_source)
        insert_data = await self.create_signin_record(_cls, insert_data)

        signin_infos = await self.get_signin_info(member_no)
        logger.info(f"signin infos: {signin_infos}")
        # 更新latest sign day 和 now date
        latest_sign_day, now_date = self.get_latest_sign_day(signin_infos)
        count, signin_text = self.get_signin_text(signin_infos, latest_sign_day, now_date)
        calendar = self.convert_member_calendar(signin_infos)
        # 计算奖品
        prize_info = await self.handle_prize(count, member_no, latest_sign_day, now_date)
        auto_id = insert_data.get("auto_id")
        event_no = f"CAMSIGNIN:{auto_id}"

        event_type = 2 if prize_info and prize_info[0] else 1
        to_cam_record = {
            "campaign_id": self.cid,
            "member_no": member_no,
            "instance_id": instance_id,
            "campaign_type": self.campaign_info.get("campaign_type"),
            "event_type": event_type,
            "utm_source": utm_source,
        }
        logger.info(f"prize_info: {prize_info}, event_type: {event_type}")
        if event_type == 2:
            to_cam_record["prize_conf"] = prize_info
            await self.app.mgr.execute( _cls.update( {_cls.receive_prize:1, _cls.prize_conf: prize_info} ).where(_cls.auto_id == insert_data["auto_id"])  )
        await record_campaign(self.app.mgr, to_cam_record)

        return True, dict(code=0, data=dict(event_no=event_no,
                                            prize_info=prize_info, is_success=1, sign_in_days=count,
                                            calendar=calendar))


    async def get_member_signin_record(self, member_no, month=None):
        _cls = self.signin_record_cls
        _where = [_cls.member_no == member_no]
        if month:
            _where.append(SQL(f"DATE_FORMAT(dl.create_time,'%Y%m') = {month}"))
        sql = _cls.select().where(*_where)\
            .order_by(_cls.create_time.desc())
        objs = await self.app.mgr.execute(sql)
        result = []
        for x in objs:
            _x = model_to_dict(x)
            _x["create_time"] = _x["create_time"].strftime("%Y-%m-%d %H:%M:%S")
            result.append(_x)
        
        return result

    async def get_prize_record(self, member_no, page_id=1, page_size=10):
        _cls = self.signin_record_cls
        _records = await self.app.mgr.execute(
            _cls.select().where(_cls.campaign_id == int(self.cid), _cls.member_no == member_no, \
            _cls.receive_prize == 1)\
            .paginate(page_id, page_size).dicts())
        logger.info(f'{member_no}得到奖励记录: {len(_records)}')
        return _records

    def convert_member_calendar(self, signin_records=[]):
        calendar = []
        if signin_records:
            for x in signin_records:
                calendar.append(datetime.strptime(x["create_time"], "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d"))
                # calendar.append(x["create_time"].strftime("%Y%m%d"))
        return calendar
