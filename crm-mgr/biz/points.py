#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from common.biz.const import *
from common.biz.crm import cache_get_crm_scene
from common.biz.heads import *
from common.biz.utils import model_build_key_map
from common.models.helper import *
from common.models.points import *
from async_lru import alru_cache
from biz.member import get_member_info, get_member_no_list

event_type_map = {
    "produce": "累加", "consume": "消耗", "reverse_produce": "反累加", "reverse_consume": "反消耗",
    "expire": "过期", "transfer": "转赠", "accept": "领取"
}


async def config_rules_goodswhite(app, crm_id, rule_id, goods_white, rule_type="produce"):
    for item in goods_white:
        sku_id = item['sku_id']
        goods_id = item['goods_id']
        in_obj = dict(
            crm_id=crm_id,
            rule_id=rule_id,
            rule_type=rule_type,
            sku_id=sku_id,
            goods_id=goods_id
        )
        await app.mgr.execute(RuleGoodsWhite.insert(in_obj).on_conflict(update=in_obj))



async def handle_consume_rule_save(app, crm_id, rules_li, params_dict):
    """积分消耗规则的save"""
    try:
        model = PointsConsumeRules
        async with app.mgr.atomic() as t:
            # 把之前的全部deleted然后
            action_scene=params_dict.get("action_scene")
            await app.mgr.execute(model.update(is_deleted=True).where(
                model.crm_id==crm_id,model.action_scene==action_scene
                ))
            for one_rule  in rules_li:
                base_points = one_rule.get("base_points")
                convert_money = one_rule.get("convert_money")
                consume_level = one_rule.get("consume_level")
                assert all([base_points, convert_money]), "传入合法的base_points,convert_money参数"
                assert type(consume_level) is int, "传入合法的 consume_level 参数"
                goods_white = one_rule.get("goods_white")
                rule_obj = dict(
                    crm_id = crm_id,
                    rule_name=params_dict.get("rule_name"),
                    action_scene=action_scene,
                    points_type=params_dict.get("points_type"),
                    base_points=base_points,
                    convert_money=convert_money,
                    consume_level=consume_level,
                    is_deleted=False
                )
                rule_id = await add_record_from_dict(app.mgr, model, rule_obj, on_conflict=3, target_keys=['crm_id', 'action_scene', 'consume_level'])
                if not rule_id:
                    raise Exception("没有写入或更新规则")
                if goods_white:
                    await config_rules_goodswhite(app, crm_id, rule_id, goods_white, rule_type="consume")
        return dict(code=RC.OK, msg="保存成功")
    except AssertionError as ex:
        await t.rollback()
        return dict(code=RC.PARAMS_INVALID, msg=f"{ex}")
    except Exception as ex:
        logger.exception(ex)
        await t.rollback()
        return dict(code=RC.HANDLER_ERROR, msg="积分消耗规则保存失败")


async def handle_produce_scene_rules_save(app, crm_id, inobj, params_dict):
    try:
        mul_rules = params_dict.get("mul_rules")
        inobj['is_deleted'] = False
        action_scene = params_dict.get("action_scene")
        goods_white = params_dict.get("goods_white")
        async with app.mgr.atomic() as t:
            if mul_rules:
                rule_id = await add_record_from_dict(app.mgr, PointsProduceRules, inobj, on_conflict=0)
            else:
                existed = await app.mgr.execute(PointsProduceRules.select().where(
                    PointsProduceRules.crm_id==crm_id, PointsProduceRules.action_scene==action_scene
                ))
                if existed:
                    logger.info("existed produce rule")
                    got1 = await app.mgr.execute(PointsProduceRules.update(inobj).where(
                        PointsProduceRules.crm_id==crm_id, PointsProduceRules.action_scene==action_scene))
                    logger.info(got1)
                    rule_id = existed[0].rule_id
                else:
                    rule_id = await add_record_from_dict(app.mgr, PointsProduceRules, inobj, on_conflict=0)
            if goods_white:
                await config_rules_goodswhite(app, crm_id, rule_id, goods_white)
        return dict(code=RC.OK, msg="保存积分累加规则成功")
    except Exception as ex:
        await t.rollback()
        logger.exception(ex)
        return dict(code=RC.HANDLER_ERROR, msg="积分累加规则保存失败")


@alru_cache(maxsize=1000)
async def cache_get_campaign_info(client, cid):
    try:
        flag, cam_info = await client.campaign.fetch(
            dict(campaign_id=cid), instance_id=client._instance_id)
    except Exception as ex:
        logger.exception(ex)
        return dict()
    logger.info(cam_info)
    if flag:
        return cam_info
    else:
        return {}


async def get_points_history(app, crm_id, params, is_download=False):
    model = PointsHistory
    where = [model.crm_id == crm_id]
    store_code = params.get("store_code") or "ALL"
    cost_center = params.get("cost_center") or "ALL"
    if store_code != "ALL":
        where.append(model.store_code == store_code)
    if cost_center != "ALL":
        where.append(model.cost_center == cost_center)
    ### 参数校验
    event_type = params.get("event_type")
    assert not event_type or event_type in ("reverse", "produce", "consume", "transfer", "accept",
                                            "expired", "reverse_produce", "reverse_consume"), "event_type参数缺失或错误"
    #
    if event_type:
        if event_type == "reverse":
            where.append(model.event_type.in_(['reverse_produce', 'reverse_consume']))
        else:
            where.append(model.event_type == event_type)
    start_time = params.get("start_time")
    if start_time:
        start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        where.append(model.event_at >= start_time)
    end_time = params.get("end_time")
    if end_time:
        end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        where.append(model.event_at <= end_time)
    mobile = params.get("mobile")
    if mobile:
        if isinstance(mobile, list):
            member_no_list = await get_member_no_list(app, crm_id, mobile=mobile, active_flag=True)
            if not member_no_list:
                return json(dict(code=RC.OK, msg="OK", data=dict(total=0, items=[])))
            else:
                where.append(model.member_no.in_(member_no_list))
        else:
            member_nos = await get_member_no_list(app, crm_id, [mobile, ], active_flag=True)
            if not member_nos:
                return json(dict(code=RC.OK, msg="OK", data=dict(total=0, items=[])))
            else:
                where.append(model.member_no.in_(member_nos))
    member_no = params.get("member_no")
    if member_no:
        if isinstance(member_no, list):
            where.append(model.member_no.in_(member_no))
        else:
            where.append(model.member_no == member_no)
    campaign_code = params.get("campaign_code")
    if campaign_code: params.update(dict(campaign_code=f"cam_crm_{campaign_code}"))
    for k in ["action_scene", "campaign_code", "stroe_code", "cost_center"]:
        key = getattr(model, k, None)
        if key:
            val = params.get(k)
            if val: where.append(key == val)
    order_by = params.get("order_by", 'event_at')
    order_asc = params.get("order_asc", 0)
    assert order_asc in (0, 1), "order_desc参数缺失或错误"
    sql = model.select().where(*where)
    logger.info(sql)
    if is_download:
        total = None
    else:
        ### 查询
        total = await app.mgr.count(sql)
    page_id, page_size = params.get("page_id", 1), params.get("page_size", 10)
    if order_by:
        order_field = getattr(model, order_by)
        if order_asc == 0:
            items = await app.mgr.execute(sql.order_by(order_field.desc()).paginate(int(page_id), int(page_size)))
        else:
            items = await app.mgr.execute(sql.order_by(order_field.asc()).paginate(int(page_id), int(page_size)))

    exclude = [model.auto_id, model.crm_id, model.order_items]
    result = [model_to_dict(item, exclude=exclude) for item in items]
    # 添加客户名 场景转化为中文
    member_nos = [i.get("member_no") for i in result]
    member_nos = list(set(member_nos))
    member_items = await app.mgr.execute(
        MemberInfo.select().where(MemberInfo.crm_id == crm_id, MemberInfo.member_no.in_(member_nos)))
    member_mp = model_build_key_map(member_items, key="member_no", excludes=[])

    point_scene_mp = await cache_get_crm_scene(app.mgr, app.redis, crm_id)
    for item in result:
        member_no = item.get("member_no")
        action_scene = item.get("action_scene")
        nickname = member_mp.get(member_no, {}).get("nickname")
        item['nickname'] = nickname
        item['action_scene'] = point_scene_mp.get(action_scene) or action_scene
        # 活动名称中文显示
        camp_code = item.get("campaign_code")
        if camp_code:
            cid = camp_code.split("_")[-1]
            camp_info = await cache_get_campaign_info(app.cam_app_client, cid)
            campaign_name = camp_info.get("campaign_name")
            if campaign_name:
                item['campaign_code'] = campaign_name
        # 翻译 事件类型
        event_type = item.get("event_type")
        event_type_ = event_type_map.get(event_type)
        if event_type_: item['event_type'] = event_type_
    if is_download:
        return result
    else:
        return total, result