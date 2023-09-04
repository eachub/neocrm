#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
from biz.utils import fetch_model_increment_list, export_list
from common.biz.const import RC
from biz.points import *
from common.biz.crm import cache_get_crm_scene
from common.biz.utils import model_build_key_map
from common.biz.wrapper import except_decorator
from common.models.helper import query_crm_info

bp = Blueprint('bp_points_mgr', url_prefix="/points")


# 积分累积场景创建
@bp.post("/<crm_id>/rules/produce_scene")
async def api_produce_scene_rules_add(request, crm_id):
    try:
        params = request.json
        app = request.app
        ### 参数校验
        rule_name = params.get("rule_name")
        action_scene = params.get("action_scene")
        points_type = params.get("points_type")
        expire_term = params.get("expire_term")
        assert type(rule_name) is str, "传入合法的 rule_name 参数"
        assert type(action_scene) is str, "传入合法的 action_scene 参数"
        assert points_type in ("order", "event"), "传入合法的 points_type 参数"
        assert type(expire_term) is int, "传入合法的 expire_term 参数"
        ratio_points = params.get("ratio_points")
        per_money = params.get("per_money")
        change_points = params.get("change_points")
        max_points = params.get("max_points")
        max_times = params.get("max_times")
        range_days = params.get("range_days")
        assert not range_days or type(range_days) is int, "传入合法的range_days参数"
        freeze_term = params.get("freeze_term")
        goods_white = params.get("goods_white")
        # 判断是否存在

        ### 写入到数据库中数据
        inobj = dict(
            crm_id=crm_id,
            rule_name=rule_name,
            action_scene=action_scene,
            points_type=points_type,
            ratio_points=ratio_points,
            per_money=per_money,
            change_points=change_points,
            max_points=max_points,
            range_days=range_days,
            max_times=max_times,
            freeze_term=freeze_term,
            expire_term=expire_term
        )
        resp = await handle_produce_scene_rules_save(app, crm_id, inobj, params)
        return json(resp)

    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post("/<crm_id>/rules/produce_scene/update")
async def api_produce_scene_rules_update(request, crm_id):
    try:
        params = request.json
        app = request.app
        model = PointsProduceRules
        ### 参数校验
        rule_id = params.get("rule_id")
        assert type(rule_id) is int, "传入合法的rule_id参数"
        # for key in params.keys():
        #     if key not in ["goods_white", 'rule_name', 'action_scene', 'change_points', 'per_money', 'convert_points','freeze_term', 'expire_term']:
        #         params.pop(key, None)
        goods_white = params.pop("goods_white", None)
        params['crm_id'] = crm_id
        if goods_white:
            await config_rules_goodswhite(app, crm_id, rule_id, goods_white, rule_type="consume")
        await add_record_from_dict(app.mgr, model, params, target_keys=['crm_id', 'rule_id'], on_conflict=3)
        return json(dict(code=RC.OK, msg="积分规则更新成功"))
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


# 积分消耗场景创建
@bp.post("/<crm_id>/rules/consume_scene")
async def api_produce_scene_rules_add(request, crm_id):
    try:
        params = request.json
        app = request.app
        ### 参数校验
        rule_name = params.get("rule_name")
        action_scene = params.get("action_scene")
        rules_li = params.get("rules_li")
        assert type(rules_li) is list, "传入合法的rules_li参数"
        assert type(rule_name) is str, "传入合法的 rule_name 参数"
        assert type(action_scene) is str, "传入合法的 action_scene 参数"

        resp = await handle_consume_rule_save(app, crm_id, rules_li, params)
        return json(resp)
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post("/<crm_id>/rules/consume_scene/update")
async def api_produce_scene_rules_update(request, crm_id):
    try:
        params = request.json
        app = request.app
        model = PointsConsumeRules
        ### 参数校验
        rule_id = params.pop("rule_id")
        assert type(rule_id) is int, "传入合法的rule_id参数"
        for key in params.keys():
            if key not in ["goods_white", 'rule_name', 'base_points', 'convert_money', 'consume_level', 'disabled']:
                params.pop(key, None)

        goods_white = params.pop("goods_white", None)
        if goods_white:
            await config_rules_goodswhite(app, crm_id, rule_id, goods_white, rule_type="consume")
        where = [model.is_deleted == False, model.rule_id == rule_id]
        await app.mgr.execute(model.update(params).where(*where))
        return json(dict(code=RC.OK, msg="积分规则更新成功"))
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


# 积分规则删除
@bp.post("/<crm_id>/rules/lot_delete")
async def api_rules_delete(request, crm_id):
    try:
        params = request.json
        app = request.app
        rule_type = params.get("rule_type")
        assert rule_type in ("produce", "consume"), "传入合法的 rule_type 参数"
        rule_id_li = params.get("rule_id_li")
        assert type(rule_id_li) is list, "rule_id_li参数缺失或格式错误"
        _model = PointsProduceRules if rule_type == "produce" else PointsConsumeRules
        await app.mgr.execute(_model.update(is_deleted=True).where(_model.rule_id.in_(rule_id_li)))
        return json(dict(code=RC.OK, msg="删除OK"))
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


# 积分规则查询
@bp.post("/<crm_id>/rules/query")
async def api_rules_fetch(request, crm_id):
    try:
        params = request.json
        app = request.app
        rule_type = params.get("rule_type")
        assert rule_type in ("produce", "consume"), "传入合法的 rule_type 参数"
        _model = PointsProduceRules if rule_type == "produce" else PointsConsumeRules
        where = [_model.crm_id == crm_id, _model.is_deleted == False]
        rule_id = params.get("rule_id")
        # 精准搜索
        if rule_id:
            where.append(_model.rule_id == rule_id)
        else:
            # 模糊搜索
            rule_name = params.get("rule_name")
            if rule_name: where.append(_model.rule_name.like(rule_name))
            action_scene = params.get("action_scene")
            if action_scene:
                where.append(_model.action_scene == action_scene)
        page_id = params.get("page_id", 1)
        page_size = params.get("page_size", 10)
        query_sql = _model.select().where(*where)
        total = await app.mgr.count(query_sql)
        if rule_type == "consume":
            items = await app.mgr.execute(query_sql)
        else:
            items = await app.mgr.execute(query_sql.paginate(page_id, page_size))
        exclude = [_model.crm_id, _model.points_type, _model.is_deleted]
        result = [model_to_dict(item, exclude=exclude) for item in items]
        data = dict(items=result, total=total)
        return json(dict(code=RC.OK, msg="OK", data=data))
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post("/<crm_id>/scene_list")
async def api_points_scene_list(request, crm_id):
    pass


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
        event_type = params.get("event_type")
        assert not event_type or event_type in ("reverse", "produce", "consume", "transfer", "accept",
                                                "expired", "reverse_produce", "reverse_consume"), "event_type参数缺失或错误"
        #
        if event_type == "transfer": event_type = "present"
        if event_type:
            if event_type =="reverse":
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
            member_nos = await get_member_no_list(app, crm_id, [mobile, ], active_flag=True)
            # member = await get_member_info(app, crm_id, mobile=mobile, active_flag=True)
            if not member_nos:
                return json(dict(code=RC.OK, msg="OK", data=dict(total=0, items=[])))
            else:
                where.append(model.member_no.in_(member_nos))
        member_no = params.get("member_no")
        if member_no:
            where.append(model.member_no == member_no)
        campaign_code = params.get("campaign_code")
        if campaign_code: params.update(dict(campaign_code=f"cam_crm_{campaign_code}"))
        for k in ["member_no", "action_scene", "campaign_code", "stroe_code", "cost_center"]:
            key = getattr(model, k, None)
            if key:
                val = params.get(k)
                if val: where.append(key == val)
        order_by = params.get("order_by", 'event_at')
        order_asc = params.get("order_asc", 0)
        assert order_asc in (0, 1), "order_desc参数缺失或错误"

        ### 查询
        sql = model.select().where(*where)
        logger.info(sql.sql())
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
        member_items = await app.mgr.execute(MemberInfo.select().where(MemberInfo.crm_id==crm_id, MemberInfo.member_no.in_(member_nos)))
        member_mp = model_build_key_map(member_items, key="member_no", excludes=[])

        point_scene_mp = await cache_get_crm_scene(app.mgr, app.redis, crm_id)
        for item in result:
            member_no = item.get("member_no")
            action_scene = item.get("action_scene")
            event_type = item.get("event_type")
            if event_type == "present":
                item["event_type"] = "transfer"
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
            event_at = item.get("event_at")
            item['update_time'] = event_at

        return json(dict(code=RC.OK, msg="OK", data=dict(total=total, items=result)))
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post("/<crm_id>/history/export")
async def points_history_export(request, crm_id):
    app = request.app
    params_dict = request.json
    file_name = f"积分明细表"
    header = ['会员号', '会员名称', '事件编码', '冲正-原事件编码', '转赠来源ID', '场景编码', '事件类型', '冲正状态', '涉及金额',
              '涉及积分', '过期时间', '解冻时间', '来源店铺', '成本中心', '活动', '操作员', '事件描述', '事件发生时间']
    reverse_status = {0: "正常状态", 1: "已冲正"}
    fields = [
        ("member_no", lambda x: str(x) if x else ''),
        ("nickname", lambda x: str(x) if x else ''),
        ("event_no", lambda x: str(x) if x else ''),
        ("origin_event_no", lambda x: str(x) if x else ''),
        ("from_transfer_no", lambda x: str(x) if x else ''),
        ("action_scene", lambda x: str(x) if x else ''),
        ("event_type", lambda x: str(x) if x else ''),
        ("reverse_status", lambda x: reverse_status.get(x)),
        ("amount", None),
        ("points", None),
        ("expire_time", lambda x: str(x) if x else ''),
        ("unfreeze_time", lambda x: str(x) if x else ''),
        ("store_code", lambda x: str(x) if x else ''),
        ("cost_center", lambda x: str(x) if x else ''),
        ("campaign_code", lambda x: str(x) if x else ''),
        ("operator", lambda x: str(x) if x else ''),
        ("event_desc", lambda x: str(x) if x else ''),
        ("event_at", lambda x: str(x) if x else ''),
    ]
    return await export_list(app, crm_id, params_dict, header, file_name, fields, get_points_history)


@bp.get("/<crm_id>/scene_info")
async def api_points_config_info(request, crm_id):
    try:
        app = request.app
        result = await query_crm_info(app.mgr, crm_id=crm_id)
        points_config = result[0].get('points_config')
        return json(dict(code=RC.OK, msg="OK", data=points_config))
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post("/<crm_id>/history/increment")
@except_decorator
async def api_points_record_list(request, crm_id):
    """轮询积分记录接口"""
    app = request.app
    params_dict = request.json
    model = PointsHistory
    where = []
    if crm_id != "common":
        crm_id = int(crm_id)
    ###
    # 非通用的where 条件处理
    member_no = params_dict.get('member_no')
    if member_no: where.append(model.member_no == member_no)
    resp = await fetch_model_increment_list(app, crm_id, model, params_dict, exclude=[model.auto_id], base_where=where)
    return json(resp)


@bp.post("/<crm_id>/summary/increment")
@except_decorator
async def api_points_summary_inc(request, crm_id):
    """轮询积分记录接口"""
    app = request.app
    params_dict = request.json
    model = PointsSummary
    where = []
    if crm_id != "common":
        crm_id = int(crm_id)
    ###
    # 非通用的where 条件处理
    member_no = params_dict.get('member_no')
    if member_no: where.append(model.member_no == member_no)
    resp = await fetch_model_increment_list(app, crm_id, model, params_dict, base_where=where)
    return json(resp)
