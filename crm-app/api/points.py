#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from biz.points import *
from biz.utils import save_order, save_refund
from common.biz.const import RC
from biz import member as biz_member, utils
from datetime import datetime
from common.models.helper import *
from common.biz.wrapper import except_decorator

bp = Blueprint('bp_points_api', url_prefix="/points")


@bp.get("/<crm_id>/summary")
async def points_summary(request, crm_id):
    """积分概览"""
    try:
        params_dict = request.args
        member_no = params_dict.get("member_no")
        assert crm_id, "实例ID缺失"
        assert type(member_no) is str, "传入合法的member_no参数"
        # 会员校验
        member_info = await biz_member.fetch_member_info_by_no(request.app.mgr, crm_id, member_no)
        assert member_info, "未查找到会员信息"
        ### 获取数据
        response = await handle_points_summary(request.app, crm_id, params_dict)
        return json(response)
    except AssertionError as e:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(e), data=None))
    except (KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post("/<crm_id>/produce/by_rule")
async def points_produce_rule(request, crm_id):
    try:
        ### 参数校验
        params_dict = request.json
        event_no = params_dict.get("event_no")
        member_no = params_dict.get("member_no")
        action_scene = params_dict.get("action_scene")
        rule_id = params_dict.get("rule_id")
        event_type = params_dict.get("event_type")
        assert type(event_no) is str, "传入合法的event_no参数"
        assert type(member_no) is str, "传入合法的member_no参数"
        assert event_type in ("order", "event"), "传入合法的event_type参数"
        ### 校验会员是否
        member_info = await biz_member.fetch_member_info_by_no(request.app.mgr, crm_id, member_no)
        assert member_info, "未查找到会员信息"
        exist_event = await fetch_member_point_event(request.app.mgr, crm_id, event_no, member_no)
        assert not exist_event, "已重复的event_no"
        event_at = params_dict.get("event_at")
        if event_at:
            event_at = datetimeFromString(event_at)
        else:
            event_at = datetime.now()
        # 根据action_scence 读取积分规则
        app = request.app
        rule_items = await get_rules_by_action(app.mgr, crm_id, action_scene, rule_id=rule_id)
        assert rule_items, "action_scene和rule_id找不到规则"
        if rule_id:
            action_scene = rule_items[0].get("action_scene")
        assert type(action_scene) is str, "传入合法的action_scene参数或rule_id参数"
        ### 判断积分是否已经存在过 或者超过领取的限制
        points = params_dict.get("points")
        # 积分记录表 action_scene 
        if event_type == "order":
            order_info = params_dict.get("order_info")
            prod_points, expire_term, freeze_term, total_amount = await \
                calculate_add_points_by_rules(app, crm_id, member_no, event_at, rule_items, params_dict,
                                              action_scene=action_scene)
            # goods_id=goods_id, pay_amount=pay_amount, can_to_points=can_to_points
            assert order_info, "传入合法的order_info参数"
            # 计算解冻时间和过期时间
            unfreeze_time = utils.plus_some_day(event_at, freeze_term)
            expire_time = utils.plus_some_day(event_at, expire_term)
            event_data = dict(
                crm_id=crm_id,
                member_no=member_no,
                event_no=event_no,
                action_scene=action_scene,
                event_type="produce",
                event_at=event_at,
                amount=total_amount,
                points=points if points else prod_points,
                expire_time=expire_time,
                unfreeze_time=unfreeze_time,
                store_code=params_dict.get("store_code"),
                cost_center=params_dict.get("cost_center"),
                campaign_code=params_dict.get("campaign_code"),
                operator=params_dict.get("operator"),
                event_desc=params_dict.get("event_desc"),
                # order_items=order_info
            )

        else:
            # 计算积分 过期时间 冻结时间
            prod_points, expire_term, freeze_term, __ = await \
                calculate_add_points_by_rules(app, crm_id, member_no, event_at, rule_items, params_dict,
                                              action_scene=action_scene)
            unfreeze_time = utils.plus_some_day(event_at, days=freeze_term)
            expire_time = utils.plus_some_day(event_at, days=expire_term)
            event_data = dict(
                crm_id=crm_id,
                member_no=member_no,
                event_no=event_no,
                action_scene=action_scene,
                event_type="produce",
                event_at=event_at,
                points=points if points else prod_points,
                expire_time=expire_time,
                unfreeze_time=unfreeze_time,
                store_code=params_dict.get("store_code"),
                cost_center=params_dict.get("cost_center"),
                campaign_code=params_dict.get("campaign_code"),
                operator=params_dict.get("operator"),
                event_desc=params_dict.get("event_desc"),
            )
        response = await produce_points_event(request.app, crm_id, member_no, prod_points, event_data, event_at)
        if event_type == "order" or action_scene == "order_pay":
            # 订单信息的保存
            order_info = params_dict.get("order_info")
            await save_order(app, crm_id, member_no, order_info, event_no=event_no)
        return json(response)
    except AssertionError as e:
        logger.exception(e)
        return json(dict(code=RC.PARAMS_INVALID, msg=str(e), data=None))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post("/<crm_id>/produce/direct")
async def points_produce_direct(request, crm_id):
    try:
        ### 参数校验
        params_dict = request.json
        event_no = params_dict.get("event_no")
        member_no = params_dict.get("member_no")
        action_scene = params_dict.get("action_scene", "os_direct")
        event_type = params_dict.get("event_type")
        points = params_dict.get("points")
        assert type(event_no) is str, "传入合法的event_no参数"
        assert type(member_no) is str, "传入合法的member_no参数"
        assert type(action_scene) is str, "传入合法的action_scene参数"
        assert event_type in ("order", "event"), "传入合法的event_type参数"
        assert type(points) is int, "传入合法的points参数"
        ### 校验会员是否
        member_info = await biz_member.fetch_member_info_by_no(request.app.mgr, crm_id, member_no)
        assert member_info, "未查找到会员信息"
        exist_event = await fetch_member_point_event(request.app.mgr, crm_id, event_no, member_no)
        assert not exist_event, "已重复的event_no"
        event_at = params_dict.get("event_at")
        if event_at:
            event_at = datetimeFromString(event_at)
        else:
            event_at = datetime.now()
        expire_days = params_dict.get('expire_days')
        freeze_hours = params_dict.get('freeze_hours')
        # 计算积分 过期时间 冻结时间
        prod_points = points
        unfreeze_time = utils.plus_some_day(event_at, hours=freeze_hours)
        expire_time = utils.plus_some_day(event_at, days=expire_days)
        event_data = dict(
            crm_id=crm_id,
            member_no=member_no,
            event_no=event_no,
            action_scene=action_scene,
            event_type="produce",
            event_at=event_at,
            points=prod_points,
            expire_time=expire_time,
            unfreeze_time=unfreeze_time,
            store_code=params_dict.get("store_code"),
            cost_center=params_dict.get("cost_center"),
            campaign_code=params_dict.get("campaign_code"),
            operator=params_dict.get("operator"),
            event_desc=params_dict.get("event_desc"),
        )
        response = await produce_points_event(request.app, crm_id, member_no, prod_points, event_data, event_at)
        return json(response)
    except AssertionError as e:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(e), data=None))
    except (KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post("/<crm_id>/consume/by_rule")
async def points_consume_rule(request, crm_id):
    try:
        params_dict = request.json
        app = request.app
        ### 参数校验
        event_no = params_dict.get("event_no")
        member_no = params_dict.get("member_no")
        action_scene = params_dict.get("action_scene")
        event_type = params_dict.get("event_type")
        assert type(event_no) is str, "传入合法的event_no参数"
        assert type(member_no) is str, "传入合法的member_no参数"
        assert type(action_scene) is str, "传入合法的action_scene参数"
        ### 校验会员和事件no
        member_info = await biz_member.fetch_member_info_by_no(request.app.mgr, crm_id, member_no)
        assert member_info, "未查找到会员信息"
        exist_event = await fetch_member_point_event(request.app.mgr, crm_id, event_no, member_no)
        assert not exist_event, "已重复的event_no"
        event_at = params_dict.get("event_at")
        if event_at:
            event_at = datetimeFromString(event_at)
        else:
            event_at = datetime.now()
        ### 计算要消耗的积分
        rules = await get_rules_by_action(app.mgr, crm_id, action_scene)
        con_points = await calculate_less_points_by_rules(rules)
        if not con_points:
            return json(dict(code=RC.OK, msg="要扣减的积分为0"))
        ### 处理积分消耗的事件
        event_data = dict(
            crm_id=crm_id,
            member_no=member_no,
            event_no=event_no,
            action_scene=action_scene,
            event_type="consume",
            points=con_points,
            store_code=params_dict.get("store_code"),
            cost_center=params_dict.get("cost_center"),
            campaign_code=params_dict.get("campaign_code"),
            operator=params_dict.get("operator"),
            event_desc=params_dict.get("event_desc"),
            event_at=event_at,
        )
        response = await consume_points_event(app, crm_id, member_no, event_at, con_points, event_data)
        return json(response)
    except AssertionError as e:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(e), data=None))
    except (KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post("/<crm_id>/consume/direct")
async def points_consume_direct(request, crm_id):
    try:
        params_dict = request.json
        app = request.app
        ### 参数校验
        event_no = params_dict.get("event_no")
        member_no = params_dict.get("member_no")
        action_scene = params_dict.get("action_scene", "os_direct")
        con_points = params_dict.get("points")
        assert type(event_no) is str, "传入合法的event_no参数"
        assert type(member_no) is str, "传入合法的member_no参数"
        assert type(action_scene) is str, "传入合法的action_scene参数"
        assert con_points, "传入合法的points参数"
        con_points = Decimal(str(con_points))
        ### 校验会员和事件no
        member_info = await biz_member.fetch_member_info_by_no(request.app.mgr, crm_id, member_no)
        assert member_info, "未查找到会员信息"
        exist_event = await fetch_member_point_event(request.app.mgr, crm_id, event_no, member_no)
        assert not exist_event, "已重复的event_no"
        event_at = params_dict.get("event_at")
        if event_at:
            event_at = datetimeFromString(event_at)
        else:
            event_at = datetime.now()
        ### 处理积分消耗的事件
        event_data = dict(
            crm_id=crm_id,
            member_no=member_no,
            event_no=event_no,
            action_scene=action_scene,
            event_type="consume",
            points=con_points,
            store_code=params_dict.get("store_code"),
            cost_center=params_dict.get("cost_center"),
            campaign_code=params_dict.get("campaign_code"),
            operator=params_dict.get("operator"),
            event_desc=params_dict.get("event_desc"),
            event_at=event_at,
        )
        response = await consume_points_event(app, crm_id, member_no, event_at, con_points, event_data)
        return json(response)
    except AssertionError as e:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(e), data=None))
    except (KeyError, TypeError, ValueError) as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post("/<crm_id>/reverse/produce")
async def points_reverse_produce(request, crm_id):
    try:
        params = request.json
        app = request.app
        ### 参数校验
        event_no = params.get("event_no")
        origin_event_no = params.get("origin_event_no")
        member_no = params.get("member_no")
        allow_negative = params.get("allow_negative")
        assert type(event_no) is str, "传入合法的event_no参数"
        assert type(member_no) is str, "传入合法的member_no参数"
        assert type(origin_event_no) is str, "传入合法的origin_event_no参数"
        assert type(allow_negative) is bool, "传入合法的allow_negative参数"

        member_info = await biz_member.fetch_member_info_by_no(request.app.mgr, crm_id, member_no)
        assert member_info, "未查找到会员信息"
        exist_event = await fetch_member_point_event(request.app.mgr, crm_id, event_no, member_no)
        assert not exist_event, "已重复的event_no"
        event_at = params.get("event_at")
        if event_at:
            event_at = datetimeFromString(event_at)
        else:
            event_at = datetime.now()
        # 查找原来的事件
        origin_event = await get_points_his_event(app.mgr, crm_id, origin_event_no)
        if not origin_event:
            return json(dict(code=RC.PARAMS_INVALID, msg="找不到origin_evnet事件"))
        if origin_event.get("origin_event_no"):
            return json(dict(code=RC.HANDLER_ERROR, msg="不支持冲正冲正事件"))

        origin_points = origin_event.get("points")

        # 部分冲正积分 和原来事件的积分对比
        reverse_points = params.get("reverse_points")
        # 根据退单金额计算部分冲正
        if not reverse_points:
            refund_info = params.get("refund_info")
            if refund_info:
                try:
                    _refund_amount = refund_info.get("refund_amount")
                    _pay_amount = refund_info.get("order_pay_amount") or refund_info.get("pay_amount")
                    if _refund_amount != _pay_amount:
                        reverse_points = Decimal(str(_refund_amount))*origin_points/Decimal(str(_pay_amount))
                        logger.info(f"{event_no} refund_amount!=pay_amount, origin_points={origin_points} reverse_points={reverse_points}")
                except Exception as ex:
                    logger.info(f"{ex}")
        part_reverse = False
        change_points = origin_points
        if reverse_points:
            # 转换成decimal4
            reverse_points = points_rounding(reverse_points, 4)
            if reverse_points < origin_points:
                change_points = reverse_points
                part_reverse = True
        # 获取可用或冻结的积分
        act_points = await member_unexpire_points(app.mgr, crm_id, member_no, event_at=event_at)
        if not allow_negative:
            if act_points < change_points:
                #  冲正之后是可用为负的 处理失败
                return json(dict(code=RC.HANDLER_ERROR, msg="冲正之后为负,无法冲正"))
        # 查看原事件已经被冲正多少积分 todo 这块逻辑可让调用方限制
        # reversed_his = await app.mgr.execute(PointsHistory.select(
        #     fn.SUM(PointsHistory.points).alias("points")).where(PointsHistory.origin_event_no==origin_event_no, PointsHistory.member_no==member_no).dicts())
        # reversed_points = reversed_his[0].get("points") if reversed_his else 0
        # if reversed_points + change_points > origin_points:
        #     return json(dict(code=RC.HANDLER_ERROR, msg="冲正的积分值大于原来事件的积分值,无法冲正"))
        ### 处理积分消耗的事件
        event_data = dict(
            crm_id=crm_id,
            member_no=member_no,
            event_no=event_no,
            reverse_status=1,
            action_scene=origin_event.get("action_scene"),
            event_type="reverse_produce",
            points=change_points,
            operator=params.get("operator"),
            store_code=origin_event.get("store_code"),
            cost_center=origin_event.get("cost_center"),
            campaign_code=origin_event.get("campaign_code"),
            event_desc=params.get("event_desc"),
            origin_event_no=origin_event_no,
            event_at=event_at,
            redo_use_event=origin_event_no,  # 先冲原事件
        )
        response = await reverse_produce_event(app, crm_id, member_no, origin_event_no, event_data,
                                               part_reverse=part_reverse, change_points=change_points)
        # 退单信息的保存
        refund_info = params.get("refund_info")
        await save_refund(app, crm_id, member_no, refund_info)
        return json(response)
    except AssertionError as e:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(e), data=None))
    except (KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post("/<crm_id>/reverse/consume")
async def points_reverse_consume(request, crm_id):
    try:
        params = request.json
        app = request.app
        ### 参数校验
        event_no = params.get("event_no")
        origin_event_no = params.get("origin_event_no")
        member_no = params.get("member_no")

        assert type(event_no) is str, "传入合法的event_no参数"
        assert type(member_no) is str, "传入合法的member_no参数"
        assert type(origin_event_no) is str, "传入合法的origin_event_no参数"

        member_info = await biz_member.fetch_member_info_by_no(request.app.mgr, crm_id, member_no)
        assert member_info, "未查找到会员信息"
        exist_event = await fetch_member_point_event(request.app.mgr, crm_id, event_no, member_no)
        assert not exist_event, "已重复的event_no"
        origin_event = await get_points_his_event(app.mgr, crm_id, origin_event_no)
        if not origin_event:
            return json(dict(code=RC.PARAMS_INVALID, msg="找不到origin_evnet事件"))
        event_at = params.get("event_at")
        if event_at:
            event_at = datetimeFromString(event_at)
        else:
            event_at = datetime.now()
        # 计算要增加的积分
        reverse_points = params.get("reverse_points")
        origin_points = origin_event.get("points")
        if reverse_points and reverse_points > origin_points:
            return json(dict(code=RC.PARAMS_INVALID, msg="要冲销的积分大于原始事件的积分,无法冲销"))
        if not reverse_points:
            reverse_points = origin_points
        ### 处理积分增加的事件
        event_data = dict(
            crm_id=crm_id,
            member_no=member_no,
            event_no=event_no,
            reverse_status=1,
            action_scene=origin_event.get("action_scene"),
            event_type="reverse_consume",
            points=reverse_points,
            store_code=origin_event.get("store_code"),
            cost_center=origin_event.get("cost_center"),
            campaign_code=origin_event.get("campaign_code"),
            operator=params.get("operator"),
            event_desc=params.get("event_desc"),
            origin_event_no=origin_event_no,
            event_at=event_at,
        )
        response = await reverse_consume_event(app, crm_id, member_no, event_at, origin_event_no, event_data)
        return json(response)
    except AssertionError as e:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(e), data=None))
    except (KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post("/<crm_id>/transfer")
async def points_transfer(request, crm_id):
    """转赠接口"""
    try:
        params = request.json
        app = request.app
        ### 参数校验
        transfer_no = params.get("transfer_no")
        from_user = params.get("from_user")
        to_user = params.get("to_user")
        trans_type = params.get("trans_type")
        event_no_li = params.get("event_no_li") or []  # 增加限制最多转移5条
        points = params.get("points")
        assert type(transfer_no) is str, "传入合法的transfer_no参数"
        assert type(from_user) is str, "传入合法的from_user参数"
        # assert type(to_user) is str, "传入合法的to_user参数"
        assert trans_type in ("by_poins", "by_events"), "传入合法的 trans_type参数"
        assert type(event_no_li) is list, "传入合法的 event_no_li参数"
        if all([points, event_no_li]): assert False, "points和event_no_li只能传递一个"
        assert not points or not event_no_li, "points和event_no_li必须传递一个"
        # 校验会员号是否存在
        member_from = await biz_member.fetch_member_info_by_no(request.app.mgr, crm_id, from_user)
        assert member_from, "未查找到会员信息"
        member_to = await biz_member.fetch_member_info_by_no(request.app.mgr, crm_id, to_user)
        assert member_to, "未查找到会员信息"
        # 转赠event事件重复
        transfer_his = await points_transfer_event(app.mgr, crm_id, transfer_no)
        assert not transfer_his, f"重复的转赠事件"

        response = await handle_transfer_event(app, crm_id, transfer_no, params, event_no_li, trans_points=points)
        return json(response)
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


# 转赠领取之后 增加两个事件 from_user 转赠积分出去的事件 to_user 获取转赠积分的事件
@bp.post("/<crm_id>/accept")
async def fetch_points_history(request, crm_id):
    try:
        params = request.json
        app = request.app
        transfer_no = params.get("transfer_no")
        member_no = params.get("member_no")
        assert type(transfer_no) is str, "传入合法的transfer_no参数"
        assert type(member_no) is str, "传入合法的 member_no 参数"
        member_info = await biz_member.fetch_member_info_by_no(request.app.mgr, crm_id, member_no)
        assert member_info, "未查找到会员信息"
        # 是否是指定会员领取
        transfer_his = await points_transfer_event(app.mgr, crm_id, transfer_no)
        assert transfer_his, f"转赠事件{transfer_no}, 过期或已经领取过"
        to_user = transfer_his.get("to_user")
        if to_user and to_user != member_no:
            assert False, f"无法领取,{member_no}没有领取的权限"
        transfer_expire = transfer_his.get("transfer_expire")
        event_at = datetime.now()
        if event_at > transfer_expire:
            assert False, f"无法领取,超过积分领取的时间"
        # 是否领取过
        exist_transfer = await get_points_his_event(app.mgr, crm_id, transfer_no)
        assert not exist_transfer, f"{transfer_no}已经被已经领取过"

        # 处理领取的逻辑
        response = await handle_accept_event(app, crm_id, member_no, event_at, params, transfer_his)
        return json(response)
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post("/<crm_id>/history")
async def fetch_points_history(request, crm_id):
    """获取用户的积分明细"""
    # 积分明细 收入 支出 冻结 过期
    try:
        params = request.json
        app = request.app
        model = PointsHistory
        where = [model.crm_id == crm_id]
        ### 参数校验
        search_type = params.get("search_type")
        assert not search_type or search_type in ("produce", "consume", "transfer", "accept",
                                                  "expired", "freeze"), "传入合法的积分类型"
        # 当前时间过期或冻结
        dt_now = datetime.now()
        if search_type in ("produce", "consume", "transfer", "accept"):
            where.append(model.event_type == search_type)
        elif search_type == "expire":
            where.append(model.expire_time < dt_now)
        elif search_type == "freeze":
            where.append(model.unfreeze_time < dt_now)

        start_time = params.get("start_time")
        if start_time:
            start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            where.append(model.event_at >= start_time)
        end_time = params.get("end_time")
        if end_time:
            end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            where.append(model.event_at <= end_time)

        for k in ["member_no", "mobile", "action_scene", "campaign_code", "stroe_code", "cost_center"]:
            key = getattr(model, k, None)
            if key:
                val = params.get(k)
                if val: where.append(key == val)
        ### 查询
        sql = model.select().where(*where)
        logger.info(sql.sql())
        total = await app.mgr.count(sql)
        page_id, page_size = params.get("page_id", 1), params.get("page_size", 10)
        items = await app.mgr.execute(sql.order_by(model.create_time.desc()).paginate(int(page_id), int(page_size)))
        exclude = ['auto_id', "crm_id", "order_items", "update_time"]
        result = [field_model_to_dict(item, exclude=exclude) for item in items]

        return json(dict(code=RC.OK, msg="OK", data=dict(total=total, items=result)))
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post("/<crm_id>/transfer/direct")
@except_decorator
async def points_transfer_direct(request, crm_id):
    """直接转赠积分 区别先发出转赠 再接受转赠"""
    params = request.json
    app = request.app
    transfer_no = params.get("transfer_no")
    from_user = params.get("from_user")
    to_user = params.get("to_user")
    points = params.get("points")
    assert type(transfer_no) is str, "传入合法的transfer_no参数"
    assert type(from_user) is str, "传入合法的from_user参数"
    assert type(to_user) is str, "传入合法的to_user参数"
    assert points, "传入合法的points参数"
    # 校验会员号是否存在
    member_from = await biz_member.fetch_member_info_by_no(request.app.mgr, crm_id, from_user)
    assert member_from, "未查找到会员信息"
    member_to = await biz_member.fetch_member_info_by_no(request.app.mgr, crm_id, to_user)
    assert member_to, "未查找到会员信息"
    # 转赠event事件重复
    transfer_his = await points_transfer_event(app.mgr, crm_id, transfer_no)
    assert not transfer_his, f"重复的转赠事件"
    # 直接转赠的逻辑
    response = await handle_transfer_event_v2(app, crm_id, transfer_no, params, trans_points=points,
                                              member_from=member_from, member_to=member_to)
    return json(response)