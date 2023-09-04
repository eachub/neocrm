#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
author: lothar
date: 2022/6/28
"""
from collections import defaultdict

from common.models.base import CRMModel
from peewee import DoesNotExist
from sanic.kjson import json_loads, json_dumps
from sanic.log import logger
from common.models.member import ChannelInfo, MemberLevelInfo, BenefitRuleInfo
from common.biz.utils import model_build_key_map

instance_prefix = "CRM_INSTANCE_"


async def get_instance_info(db, redis, crm_id):
    try:
        got = await redis.get(f"{instance_prefix}{crm_id}")
        if got:
            return json_loads(got)
        else:
            data = await db.get(CRMModel.select().where(CRMModel.crm_id == crm_id).dicts())
            await redis.setex(f"{instance_prefix}{crm_id}", 60 * 5, json_dumps(data))
        return data
    except DoesNotExist:
        logger.exception(f"not find {crm_id}")
        return None


def build_points_scene_mp(points_config):
    scene_li = points_config.get("produce_scene", []) + points_config.get("consume_scene", []) +\
               [{"name": "积分值变更", "code": "os_direct"}]
    result_mp = dict()
    for one in scene_li:
        code = one.get("code")
        name = one.get("name")
        result_mp[code] = name
    return result_mp


async def cache_get_crm_scene(db_client, redis, crm_id):
    """获取 instance 信息"""

    key = f"crm_scene_detail:{crm_id}"
    got = await redis.get(key)
    data = (got and json_loads(got)) or {}
    if not data:
        m = CRMModel
        try:
            crminfo = await db_client.get(
                m.select(m.crm_id, m.points_config).where(m.crm_id == crm_id).dicts())
            points_config = crminfo.get("points_config")
            data = build_points_scene_mp(points_config)
        except DoesNotExist as ex:
            return {}
        await redis.setex(key, 7200, json_dumps(data))
    return data


async def cache_get_crm_channel_map(db_client, redis, crm_id):
    """获取渠道信息"""
    key = f"crm_channel_info:{crm_id}"
    got = await redis.get(key)
    data = (got and json_loads(got)) or {}
    if not data:
        m = ChannelInfo
        try:
            items = await db_client.execute(m.select().where(m.crm_id == crm_id))
            data = model_build_key_map(items, "channel_code", excludes=[m.crm_id, m.update_time, m.create_time, m.desc])
        except DoesNotExist as ex:
            return {}
        await redis.setex(key, 7200, json_dumps(data))
    return data


async def cache_get_wmp_name(app, redis, crm_id):
    """{'id':'name'}"""
    # 请求cms获取小程序信息
    host = app.conf.CMS_CLIENT['host']
    instance_id = app.conf.CMS_CLIENT['instance_id']

    key = f"crm_wmapp_name:{crm_id}"
    got = await redis.get(key)
    data = (got and json_loads(got)) or {}
    if not data:
        try:
            ret = await app.http.get(f"{host}/api/cms/application/{instance_id}/list")
            logger.info(f"get_wmpname {ret}")
            if ret.get("code") == 0:
                detail = ret.get("data", {}).get('detail')
                # 构建中文映射关系
                appid_name_map = dict()
                for one in detail:
                    app_name = one.get("app_name")
                    app_id = one.get("app_id")
                    appid_name_map[app_id] = app_name
                data = appid_name_map
            else:
                data = {}
        except Exception as ex:
            return {}
        await redis.setex(key, 7200, json_dumps(data))
    return data


async def get_crm_score_rule_map(db, redis, crm_id):
    key = f"score_rule_{crm_id}"
    try:
        got = await redis.get(key)
        if got:
            return json_loads(got)
        else:
            data = await db.get(CRMModel.select().where(CRMModel.crm_id == crm_id).dicts())
            score_rule_map = defaultdict(dict)
            give_rules = data.get("level_config", {}).get("give_rules")
            for item in give_rules:
                action = item.get("action")
                score_rule_map[action] = item
            deduct_rules = data.get("level_config", {}).get("deduct_rules")
            for item in deduct_rules:
                action = item.get("action")
                score_rule_map[action] = item
            await redis.setex(key, 60 * 5, json_dumps(score_rule_map))
        return score_rule_map
    except DoesNotExist:
        logger.exception(f"not find {crm_id}")
        return None


async def cache_get_level_benefit(mgr, redis, crm_id):
    key = f"level_base_benefit_{crm_id}"
    try:
        got = await redis.get(key)
        if got:
            return json_loads(got)
        else:
            level_infos = await mgr.execute(MemberLevelInfo.select().where(MemberLevelInfo.deleted == False,
                                                                               MemberLevelInfo.crm_id == crm_id).dicts())
            result = dict()
            for level_info in level_infos:
                base_rules = list()
                level_benefit = level_info.get("level_benefit")
                level_no = level_info.get("level_no")
                if level_benefit:
                    rules_items = await mgr.execute(BenefitRuleInfo.select().where(BenefitRuleInfo.crm_id == crm_id))
                    rules_map = model_build_key_map(rules_items, "benefit_rule_id", excludes=[])

                    benefit_rule_li = []
                    for benefit in level_benefit:
                        benefit_rule_id = benefit.get("benefit_rule_id")
                        benefit_rule_li.append(benefit_rule_id)
                    # 查询权益下所有的规则
                    benefit_rules = await mgr.execute(
                        BenefitRuleInfo.select().where(BenefitRuleInfo.benefit_rule_id.in_(benefit_rule_li)).dicts())
                    base_rule_ids = []
                    for rule in benefit_rules:
                        son_rules = rule.get("son_rules")
                        if son_rules:
                            for son_rule in son_rules:
                                base_rule_id = son_rule.get("base_rule_id")
                                base_rule_ids.append(base_rule_id)
                        else:
                            base_rule_ids.append(rule.get("benefit_rule_id"))
                    ###
                    # 根据 base_rule_id 增加权益
                    for rule_id in list(set(base_rule_ids)):
                        this_rule = rules_map.get(rule_id)
                        base_rules.append(this_rule)
                result[level_no] = base_rules
            await redis.setex(key, 60 * 5, json_dumps(result))
        return result
    except Exception as ex:
        logger.exception(ex)
        return {}


async def cache_get_level_ratio_points(mgr, redis, crm_id):
    key = f"level_base_benefit_{crm_id}"
    try:
        got = await redis.get(key)
        if got:
            return json_loads(got)
        else:
            level_infos = await mgr.execute(MemberLevelInfo.select().where(MemberLevelInfo.deleted == False,
                                                                           MemberLevelInfo.crm_id == crm_id).dicts())
            result = dict()
            for level_info in level_infos:
                level_benefit = level_info.get("level_benefit")
                level_no = level_info.get("level_no")

                tmp_dict = defaultdict(list)
                if level_benefit:
                    rules_items = await mgr.execute(BenefitRuleInfo.select().where(BenefitRuleInfo.crm_id == crm_id))
                    rules_map = model_build_key_map(rules_items, "benefit_rule_id", excludes=[])

                    benefit_rule_li = []
                    for benefit in level_benefit:
                        benefit_rule_id = benefit.get("benefit_rule_id")
                        benefit_rule_li.append(benefit_rule_id)
                    # 查询权益下所有的规则
                    benefit_rules = await mgr.execute(
                        BenefitRuleInfo.select().where(BenefitRuleInfo.benefit_rule_id.in_(benefit_rule_li)).dicts())
                    base_rule_ids = []
                    for rule in benefit_rules:
                        son_rules = rule.get("son_rules")
                        if son_rules:
                            for son_rule in son_rules:
                                base_rule_id = son_rule.get("base_rule_id")
                                base_rule_ids.append(base_rule_id)
                        else:
                            base_rule_ids.append(rule.get("benefit_rule_id"))
                    ###
                    # 处理成 {level_no: {"ratio1":[rule_id1, rule_id2]}}
                    for rule_id in list(set(base_rule_ids)):
                        this_rule = rules_map.get(rule_id)
                        if this_rule.get("benefit_type") == "be_ratio_points":
                            content = this_rule.get("content")
                            ratio_points = content.get('ratio_points')
                            if ratio_points:
                                ratio_points = str(ratio_points).strip('0')
                                produce_scene = content.get("produce_scene") or []
                                for i in produce_scene:
                                    # 将积分增加场景的 rule_id 存放
                                    tmp_dict[ratio_points].append(i.get("rule_id"))

                result[level_no] = tmp_dict
            logger.info(f"level_base_benefit result={result}")
            await redis.setex(key, 60 * 5, json_dumps(result))
        return result
    except Exception as ex:
        logger.exception(ex)
        return {}


async def cache_get_crm_level(mgr, redis, crm_id):
    """获取crm_id的level信息"""
    key = f"crm_level_info:{crm_id}"
    got = await redis.get(key)
    data = (got and json_loads(got)) or {}
    if not data:
        try:
            _model = MemberLevelInfo
            items = await mgr.execute(_model.select().where(_model.crm_id == crm_id, _model.deleted == False))
            level_no_map = model_build_key_map(items, "level_no")
            data = level_no_map
        except Exception as ex:
            return {}
        await redis.setex(key, 7200, json_dumps(data))
    return data