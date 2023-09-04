# -*- coding: utf-8 -*-
from urllib.parse import urlencode

import ujson
from peewee import DoesNotExist, SQL
from common.models.cam import CardRecord, model_to_dict, UserWhiteList
from mtkext.db import sql_printf, sql_execute, safe_string
from datetime import datetime, timedelta
from decimal import Decimal
from sanic.log import logger
from common.models.crm import db_eros_crm, UserTags
from copy import deepcopy
from mtkext.db import FlexModel
from biz.campaign import record_campaign

class CardPage():
    def __init__(self, app, campaign_info):
        self.app = app
        self.campaign_info = campaign_info
        self.cid = campaign_info["campaign_id"]
        self.init_card()
        card_record_cls = FlexModel.get(CardRecord, self.cid)
        self.table_name = card_record_cls._meta.table_name
        self.card_record_cls = card_record_cls
        logger.info(f"init table name: {self.table_name}")
        logger.info(f"init record cls: {self.card_record_cls}")


        all_cam = self.card_conf.get("children", [])
        self.people_cls = {}
        
        for cam in all_cam: # 初始化人群包数据表
            target_type = cam.get("target_type")
            campaign_child_no = cam.get("campaign_child_no")
            logger.info(f"cam {campaign_child_no} target_type: {target_type}")
            if target_type == 1: # 人群包判断
                people_ids = cam.get("people_ids", [])
                logger.info(f"{campaign_child_no} people ids: {people_ids}")
                for pid in people_ids:
                    _people_cls = FlexModel.get(UserWhiteList, pid)
                    self.people_cls[pid] = _people_cls
                    logger.info(f"init user white list cls: {_people_cls}")



    def init_card(self):
        campaign_info = self.campaign_info
        logger.info(f"init lottery: {self.campaign_info}")
        self.card_conf = campaign_info.get('detail', {})
        self.cache_key = "neocam_card_info_713"

    async def get_member_card(self, member_no=None):
        all_cam = deepcopy(self.card_conf.get("children", []))
        _now_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for cam in all_cam:
            start_time, end_time = cam.get("start_time"), cam.get("end_time")
            campaign_child_no = cam.get("campaign_child_no")
            if start_time <= _now_date < end_time :
                target_type = cam.get("target_type")
                if member_no:
                    if target_type == 1 : # 人群包判断
                        is_in_white_list = await self.member_in_white_list(member_no, cam.get("people_ids"))
                        if is_in_white_list:
                            received_card = await self.member_received(member_no)
                            cam = self.rebuild_cam(cam, received_card)
                            return True, dict(code=0, data=cam)
                        else:
                            logger.info(f"{member_no}白名单判断失败{campaign_child_no}")
                    elif target_type == 2 : # 标签判断
                        tag_condition = cam.get("tag_condition")
                        is_in_tag = await self.member_tag(member_no, tag_condition)
                        if is_in_tag:
                            received_card = await self.member_received(member_no)
                            cam = self.rebuild_cam(cam, received_card)
                            return True, dict(code=0, data=cam)
                        else:
                            logger.info(f"{member_no}标签判断失败{campaign_child_no}")
                    else:
                        received_card = await self.member_received(member_no)
                        cam = self.rebuild_cam(cam, received_card)
                        logger.info(f"no target condition, all user show: {campaign_child_no}")
                        return True, dict(code=0, data=cam)
                else:
                    logger.info(f"no member, all user show: {campaign_child_no}")
                    return True, dict(code=0, data=cam)

            else:
                logger.info(f"{campaign_child_no}不在活动时间范围内:{start_time}-{end_time}")
                pass

        return False, dict(code=0,data={})

    def rebuild_cam(self, cam, received_card):
        logger.info(f"rebuild cam: {cam}, {received_card}")
        _received_card = received_card.get("coupon_list",[])
        cam["received"] = {
            "received_card": received_card
        }
        coupon_list = cam.get("goods_info", {}).get("coupon_list", [])
        logger.info(f"{coupon_list}")
        logger.info(f"{_received_card}")
        logger.info(f"{cam}")
        cam["coupon_result"] = [{
            "status": 1 if _x in _received_card else 0,
            "card_id": _x
        } for _x in coupon_list]
        return cam

    async def member_received(self, member_no):
        now_date = datetime.now().strftime("%Y%m%d")
        received_cards = await self.app.redis.get(f"{self.cache_key}_{self.cid}_{member_no}_{now_date}")
        if received_cards:
            return ujson.loads(received_cards)
        _cls = self.card_record_cls
        campaign_info = self.campaign_info
        instance_id = campaign_info["instance_id"]
        _res = await self.app.mgr.execute(
            _cls.select().where(_cls.member_no == member_no, _cls.is_received == 1,
                                _cls.instance_id == instance_id))
        if len(_res):
            for _x in _res:
                card_conf = _x.card_conf
                _card_conf = ujson.dumps(card_conf)
                await self.app.redis.setex(f"{self.cache_key}_{self.cid}_{member_no}_{now_date}", 24 * 3600, _card_conf)
                return card_conf
        return {}

    async def append_received_card(self, member_no, card_ids, campaign_child_no, utm_source):
        if not member_no:
            logger.error("no member no")
            return False,dict(code=0,msg="no member no")
        campaign_info = self.campaign_info
        instance_id = campaign_info["instance_id"]
        _cls = self.card_record_cls
        _res = await self.app.mgr.execute(
            _cls.select().where(_cls.member_no == member_no, _cls.is_received == 1,
                                _cls.instance_id == instance_id))

        to_cam_record = {
            "campaign_id": self.cid,
            "member_no": member_no,
            "instance_id": instance_id,
            "campaign_type": self.campaign_info.get("campaign_type"),
            "event_type": 2,
            "utm_source": utm_source,
        }

        if len(_res) and card_ids:
            now_date = datetime.now().strftime("%Y%m%d")
            for _x in _res: #理论只有1个结果
                goods_conf = _x.card_conf
                coupon_list = goods_conf['coupon_list']
                coupon_list.extend(card_ids)
                coupon_list = list(set(coupon_list))
                goods_conf['coupon_list'] = coupon_list
                got = await self.app.mgr.execute(_cls.update({'card_conf': goods_conf}).where(_cls.auto_id == _x.auto_id) )
                await self.app.redis.delete(f"{self.cache_key}_{self.cid}_{member_no}_{now_date}")

                res = {"goods_info": goods_conf}
                _goods_conf = deepcopy(goods_conf)
                _goods_conf["coupon_list"] = card_ids
                to_cam_record["prize_conf"] = _goods_conf
                if got: await record_campaign(self.app.mgr, to_cam_record)
                res = self.rebuild_cam(res, goods_conf)
                return True, dict(code=0, data=res)
        else:
            # campaign_id = IntegerField(help_text="campaign id")
            #     instance_id = CharField(index=True, max_length=64, help_text="uid")
            #     member_no = CharField(unique=True, max_length=64, help_text="会员号")
            #     card_conf = JSONField(default={}, help_text="领券信息")
            #     is_received = SmallIntegerField(default=0, help_text="0:未领取 1：已领取")
            #     utm_source = CharField(max_length=64, null=True, help_text="活动推广来源")
            campaign_child = {}
            card_conf = self.card_conf
            for x in card_conf["children"]:
                if x.get("campaign_child_no") == campaign_child_no:
                    campaign_child = x
            if not campaign_child:
                logger.error(f"未找到campaign_child: {campaign_child_no}, {self.campaign_info}")
                return True,dict(code=0,msg=f"未找到{self.cid}-{campaign_child_no}")
            goods_info = campaign_child.get("goods_info", {})
            body = {
                "campaign_id": self.cid,
                "member_no": member_no,
                "instance_id": instance_id,
                "card_conf": goods_info,
                "is_received": 1,
                "utm_source": utm_source
            }
            got = await self.app.mgr.execute(_cls.insert(body).on_conflict_ignore())
            res = {"goods_info": goods_info}
            res = self.rebuild_cam(res, goods_info)
            to_cam_record["prize_conf"] = goods_info
            if got: await record_campaign(self.app.mgr, to_cam_record)
            return True, dict(code=0, data=res)

    # 判断用户是否在会员号白名单数据表
    async def member_in_white_list(self, member_no, people_ids):
        cid = self.cid
        for pid in people_ids:
            _, table_name = UserWhiteList.get_table_name(pid)
            sql = safe_string(f"select auto_id from {table_name} where member_no = '{member_no}' and campaign_id = '{cid}'")
            sql = str(sql)
            query = self.people_cls[pid].raw(sql)
            _ans = await self.app.mgr.execute(query)
            if _ans:
                return True

        return False

    # 判断用户是否在会员号白名单数据表
    async def member_tag(self, member_no, tag_condition):
        logger.info(f"member_tag: {member_no}")
        crm_id = tag_condition.get("crm_id")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        tag_cls = FlexModel.get(UserTags, yesterday, db=db_eros_crm)
        logger.info(f"crm_id: {crm_id}, member_no: {member_no}")
        query = tag_cls.select().where(tag_cls.member_no == member_no, tag_cls.crm_id == crm_id)
        _sql = query.sql()
        logger.info(f"query sql: {_sql}")
        _ans = await self.app.crm_mgr.execute(query)
        logger.info(f"user tag: {_ans}")
        for x in _ans:
            logger.info(f"user tag: {x}")
            member_tag = model_to_dict(x)
            res = self.tag_process(tag_condition, member_tag)
            return res
        return False

    def tag_process(self, tag_condition, tags):
        includes = tag_condition.get("includes",{})
        includes_result = True
        if includes:
            includes_result = self.expr_process(includes, tags)
        excludes = tag_condition.get("excludes", {})
        excludes_result = True
        if excludes:
            excludes_result = not self.expr_process(excludes, tags)
        return includes_result and excludes_result

    def expr_process(self, condition, tags):
        op, expr = condition.get("op"), condition.get("expr")
        if op == "and":
            _res = True
            for exp in expr:
                _tag_bind_field = self.app.all_crm_tag.get(exp.get("tag_id"), "")
                level_id = exp.get("level_id")
                _tag_value = tags.get(_tag_bind_field)
                logger.info(f"_tag_value: {_tag_value}, _tag_bind_field: {_tag_bind_field}, level_id: {level_id}")
                if str(level_id) in _tag_value.split(","):
                    pass
                else:
                    # _res = False
                    return False
            return _res
        else:
            _res = False
            for exp in expr:
                _tag_bind_field = self.app.all_crm_tag.get(exp.get("tag_id"), "")
                level_id = exp.get("level_id")
                _tag_value = tags.get(_tag_bind_field)
                if str(level_id) in _tag_value.split(","):
                    # _res = True
                    return True
                else:
                    pass
            return _res
