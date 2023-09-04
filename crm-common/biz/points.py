from common.biz.const import RC
from common.models.helper import add_record_from_dict, member_active_points, points_usable_event
from common.models.points import *
from common.models.helper import *
from common.biz.utils import gen_event_no
from peewee import fn
from decimal import Decimal


def points_rounding(points, decimal=4):
    if not points:
        points = 0
    new_points = Decimal(points).quantize(Decimal(f"0.{'0'*decimal}"))
    return new_points


async def handle_points_summary(app, crm_id, params_dict):
    member_no = params_dict.get("member_no")
    _query = PointsSummary.select().where(
        PointsSummary.crm_id == crm_id, PointsSummary.member_no == member_no
    )
    items = await app.mgr.execute(_query)
    if len(items):
        data = model_to_dict(items[0], exclude=["detail_id", "create_time", "update_time"])
    else:
        data = None
    return dict(code=RC.OK, msg="OK", data=data)


async def handle_points_produce_rule(app, crm_id, params_dict):
    """按照规则计算积分, 增加积分"""
    pass


async def fetch_member_point_event(mgr, crm_id, event_no, member_no):
    try:
        one = await mgr.get(PointsHistory, crm_id=crm_id, member_no=member_no, event_no=event_no)
    except DoesNotExist:
        logger.info(f"not found event")
        one = None
    return one


def process_points_change(points, now_dt, unfreeze_time, expire_time):
    """计算积分概览将要变化的情况, 冻结积分,过期积分 未来过期 可用积分"""
    freeze_points, expired_points, future_expired, active_points = 0, 0, 0, 0
    logger.info(f"{type(now_dt)} {type(unfreeze_time)} {type(expire_time)}")
    logger.info(f"now_dt:{now_dt} unfreeze_time:{unfreeze_time} expire_time:{expire_time}")
    # 先判断是否冻结
    if unfreeze_time:
        if unfreeze_time > now_dt:  # 冻结
            freeze_points = points
    else:  # 未冻结
        if expire_time:
            if expire_time <= now_dt:  # 过期
                expired_points = points
            elif expire_time <= (now_dt + timedelta(days=7)):  # 7天快过期
                future_expired = points
                active_points = points
            else:  # 过期时间>7天
                active_points = points
        else:  # 无过期时间
            active_points = points
    return freeze_points, expired_points, future_expired, active_points


async def adding_points_core(app, crm_id, member_no, change_points, event_data):
    # 积分事件记录
    await add_record_from_dict(app.mgr, PointsHistory, event_data, on_conflict=0)
    # 可用积分表
    await add_record_from_dict(app.mgr, PointsAvailable, event_data, on_conflict=0)
    # 积分总额表
    event_at = event_data.get("event_at")
    expire_time = event_data.get("expire_time")
    if expire_time and type(expire_time) is str:
        expire_time = datetime.strptime(expire_time, "%Y-%m-%d %H:%M:%S")
    unfreeze_time = event_data.get("unfreeze_time")
    if unfreeze_time and type(unfreeze_time) is str:
        unfreeze_time = datetime.strptime(unfreeze_time, "%Y-%m-%d %H:%M:%S")
    freeze_points, expired_points, future_expired, active_points = \
        process_points_change(change_points, event_at, unfreeze_time, expire_time)
    # 初始化积分
    in_obj = dict(
        crm_id=crm_id,
        member_no=member_no,
        total_points=change_points,
        freeze_points=freeze_points,
        expired_points=expired_points,
        future_expired=future_expired,
        active_points=active_points,
    )
    logger.info(
        f"{member_no} summary add total_points+{change_points} freeze_points+{freeze_points} expired_points+{expired_points} \
                future_expired+{future_expired} active_points+{active_points}")
    await app.mgr.execute(PointsSummary.insert(in_obj).on_conflict(
        update={
            "total_points": PointsSummary.total_points + change_points,
            "freeze_points": PointsSummary.freeze_points + freeze_points,
            "expired_points": PointsSummary.expired_points + expired_points,
            "future_expired": PointsSummary.future_expired + future_expired,
            "active_points": PointsSummary.active_points + active_points,
        }))
    return True, "累积积分成功"


async def produce_points_event(app, crm_id, member_no, points, event_data, event_at):
    """处理积分增加的事件"""
    # 事务处理
    try:
        async with app.mgr.atomic() as t:
            flag, result = await adding_points_core(app, crm_id, member_no, points, event_data)
            if flag:
                return dict(code=RC.OK, msg="累积积分成功")
            else:
                await t.rollback()
                return dict(code=RC.HANDLER_ERROR, msg="增加积分处理失败")
    except Exception as ex:
        logger.exception(ex)
        await t.rollback()
        return False, ""


async def calculate_less_points_by_rules(rules):
    # TODO 目前没有指定规则扣减积分的场景测试
    points_li = []
    for rule in rules:
        # 如果是 order
        points_type = rule.get("points_type")
        if points_type == "event":
            points = rule.get("ratio_points")
            points_li.append(points)
        # 如果是
    return max(points)


async def cal_consume_events_ids(app, crm_id, member_no, event_at, target_points, event_type="consume"):
    """计算消耗或者转赠的积分事件ids
    return 积分可用表数据+used+remain"""
    _model = PointsAvailable
    if event_type == "transfer":
        pass
    where = [
        (_model.expire_time >= event_at) | (_model.expire_time == None),
        (_model.unfreeze_time <= event_at) | (_model.unfreeze_time == None),
        _model.member_no == member_no,
        _model.crm_id == crm_id,
        (_model.transfer_expire <= event_at) | (_model.transfer_expire == None),
    ]

    counts = await app.mgr.count(_model.select().where(*where))
    logger.info(f"可用的积分事件数是counts={counts}")
    page_size = 100
    quo, rem = divmod(counts, page_size)
    page_num = quo + 1 if rem else quo
    # 分页计算
    consume_ids_li = []  # dict(auto_id, event_no, points, remain)
    all_point = 0
    used_ids = set()  # 避免重复计算 去重
    if event_type == "transfer":
        sql_str = _model.select().where(*where). \
            order_by(_model.expire_time.desc())
    else:
        sql_str = _model.select().where(*where). \
            order_by(_model.expire_time.asc())
    for page_id in (1, page_num + 1):
        # 计算要消耗的快过期的积分事件ids
        ids_li = await app.mgr.execute(sql_str.paginate(page_id, page_size).dicts())
        for _id in ids_li:
            auto_id = _id['auto_id']
            if auto_id in used_ids:
                continue
            one_points = _id['points']
            all_point += one_points
            used_ids.add(auto_id)
            if all_point >= target_points:
                remain = all_point - target_points
                used = one_points - remain
                _id.update(dict(remain=remain, used=used))
                consume_ids_li.append(_id)
                break
            else:
                _id.update(dict(remain=0, used=one_points))
                consume_ids_li.append(_id)
    logger.info(f"{member_no} consume points={target_points} need process ids={consume_ids_li}")
    return consume_ids_li


async def consume_active_points(app, crm_id, member_no, con_points, event_at, consume_ids_li=None):
    """消耗积分
    params: con_points 要消耗的积分"""
    _model = PointsAvailable
    act_points = await member_active_points(app.mgr, crm_id, member_no, event_at=event_at)
    if act_points < con_points:  # 活跃积分<要消耗积分
        return False, "积分不足处理失败", ""
    # 删除修改可用积分(update 添加where条件)
    for point_info in consume_ids_li:
        # 删除或修改
        auto_id = point_info['auto_id']
        used = point_info['used']
        remain = point_info['remain']
        if remain:  # 修改
            logger.info(f"update PointsAvailable points={remain} where auto_id={auto_id}")
            got = await app.mgr.execute(_model.update(points=remain).where(
                _model.points >= used, _model.auto_id == auto_id
            ))
        else:  # 删除
            logger.info(f"delete PointsAvailable where auto_id={auto_id}")
            got = await app.mgr.execute(_model.delete().where(
                _model.points >= used, _model.auto_id == auto_id))
        if not got:
            logger.info(f"删除或更新可用积分报错")
            return False, "处理可用积分出错", ""
    logger.info("all process ok")
    return True, "可用积分更新OK", deepcopy(consume_ids_li)


async def lessing_points_core(app, crm_id, member_no, change_points, consume_ids_li, event_data, record_flag=False,
                              trans_flag=False):
    """减少积分的核心操作"""
    if not consume_ids_li:
        return False, "没有要减少积分的事件"
    _model = PointsAvailable
    ### 删除修改可用积分(update 添加where条件)
    for point_info in consume_ids_li:
        # 删除或修改
        auto_id = point_info['auto_id']
        used = point_info['used']
        remain = point_info['remain']
        if remain:  # 修改
            logger.info(f"update PointsAvailable points={remain} where auto_id={auto_id}")
            got = await app.mgr.execute(_model.update(points=remain).where(
                _model.points >= used, _model.auto_id == auto_id
            ))
        else:  # 删除
            logger.info(f"delete PointsAvailable where auto_id={auto_id}")
            got = await app.mgr.execute(_model.delete().where(
                _model.points >= used, _model.auto_id == auto_id))
        if not got:
            logger.info(f"删除或更新可用积分报错")
            return False, "处理可用积分出错"

    logger.info("all process ok")
    ### 增加积分消耗记录
    await add_record_from_dict(app.mgr, PointsHistory, event_data, on_conflict=0)
    if record_flag:
        for detail in consume_ids_li:
            in_consume_record = dict(
                crm_id=crm_id, member_no=member_no, points=change_points,
                store_code=event_data.get("store_code"),
                cost_center=event_data.get("cost_center"),
                consuemd_event=detail.get("event_no"),
                points_used=detail.get("used"),
                points_remain=detail.get("remain"),
            )
            await app.mgr.execute(PointsConsumeRecord.insert(in_consume_record))
    ### 更改积分概览 todo 这个需要修改?
    in_obj = dict(
        crm_id=crm_id,
        member_no=member_no,
        active_points=- change_points,
        used_points=change_points
    )

    await app.mgr.execute(PointsSummary.insert(in_obj).on_conflict(
        update={
            "active_points": PointsSummary.active_points - change_points,
            "used_points": PointsSummary.used_points + change_points
        }))
    return True, "处理OK"


async def consume_points_event(app, crm_id, member_no, event_at, con_points, event_data):
    """处理积分消耗的事件"""
    # 事务处理
    consume_ids_li = await cal_consume_events_ids(app, crm_id, member_no, event_at, target_points=con_points)
    act_points = await member_active_points(app.mgr, crm_id, member_no, event_at=event_at)
    if act_points < con_points:  # 活跃积分<要消耗积分
        return dict(code=RC.HANDLER_ERROR, msg="积分不足扣减失败")
    try:
        async with app.mgr.atomic() as t:
            flag, result = await lessing_points_core(app, crm_id, member_no, con_points, consume_ids_li, event_data,
                                                     record_flag=True)
            if flag:
                return dict(code=RC.OK, msg="消耗积分处理成功")
            else:
                await t.rollback()
                return dict(code=RC.HANDLER_ERROR, msg="消耗积分处理失败")
    except Exception as ex:
        logger.exception(ex)
        await t.rollback()
        return dict(code=RC.DATA_EXCEPTION, msg="消耗积分处理失败")


async def reverse_produce_event(app, crm_id, member_no, origin_event_no, event_data, part_reverse=False,
                                change_points=0):
    try:
        async with app.mgr.atomic() as t:
            # 反累加
            one = await points_usable_event(app.mgr, crm_id, origin_event_no)
            # 更改可用积分
            if not one:
                logger.info("可用积分表不存在,可能已被消耗 已被消耗也能冲正")
                # todo 更改积分概览？？？
            else:
                if part_reverse:
                    logger.info(f"part_reverse origin_event_no:{origin_event_no}")
                    # 部分冲正  这个可用积分事件可能被使用过, 减少为0
                    # 先修改
                    got1 = await app.mgr.execute(PointsAvailable.update({
                        "points": PointsAvailable.points - change_points
                    }).where(
                        PointsAvailable.event_no == origin_event_no,
                        PointsAvailable.points > change_points
                    ))
                    if not got1:
                        # 删除
                        got1 = await app.mgr.execute(PointsAvailable.delete().where(
                            PointsAvailable.event_no == origin_event_no,
                            PointsAvailable.points <= change_points
                        ))
                else:
                    # 可用积分表删除 剩余多少冲正多少
                    got1 = await app.mgr.execute(PointsAvailable.delete().where(
                        PointsAvailable.event_no == origin_event_no
                    ))
                if not got1:
                    await t.rollback()
                    return dict(code=RC.HANDLER_ERROR, msg="冲正处理失败")
                ### 积分概览计算
                expire_time = one['expire_time']
                unfreeze_time = one['unfreeze_time']
                event_at = event_data.get("event_at")
                freeze_points, expired_points, future_expired, active_points = \
                    process_points_change(change_points, event_at, unfreeze_time, expire_time)
                logger.info(
                    f"summay changes {member_no} freeze_points-{freeze_points} future_expired-{future_expired} active_points-{active_points}")
                await app.mgr.execute(PointsSummary.update(
                    freeze_points=PointsSummary.freeze_points - freeze_points,
                    future_expired=PointsSummary.future_expired - future_expired,
                    # expired_points = PointsSummary.expired_points-expired_points ,
                    active_points=PointsSummary.active_points - active_points,

                ).where(PointsSummary.member_no == member_no, PointsSummary.crm_id == crm_id))

            # 更新为冲正状态
            await app.mgr.execute(PointsHistory.update(reverse_status=1).where(
                PointsHistory.crm_id == crm_id, PointsHistory.event_no == origin_event_no
            ))
            ### 事件记录
            await add_record_from_dict(app.mgr, PointsHistory, event_data)
            return dict(code=RC.OK, msg="冲正处理成功")
    except Exception as ex:
        logger.exception(ex)
        return dict(code=RC.HANDLER_ERROR, msg="冲正处理失败")


async def reverse_consume_event(app, crm_id, member_no, event_at, origin_event_no, event_data):
    try:
        async with app.mgr.atomic() as t:
            # 反消耗 累加积分
            change_points = event_data['points']
            flag, result = await adding_points_core(app, crm_id, member_no, change_points, event_data)
            ### 旧事件更新为冲正状态
            got = await app.mgr.execute(PointsHistory.update(reverse_status=1).where(
                PointsHistory.crm_id == crm_id, PointsHistory.event_no == origin_event_no,
                PointsHistory.reverse_status == 0
            ))
            if not got:
                return dict(code=RC.HANDLER_ERROR, msg="积分冲正处理失败")
            return dict(code=RC.OK, msg="冲正处理成功")
    except Exception as ex:
        logger.exception(ex)
        return dict(code=RC.HANDLER_ERROR, msg="冲正处理失败")


async def handle_transfer_event(app, crm_id, transfer_no, params, event_no_li=None, trans_points=None):
    """积分转赠的事件处理"""
    from_user = params.get("from_user")
    event_at = datetime.now()
    event_ids_li = []  # 要转赠的积分事件detail
    try:
        async with app.mgr.atomic() as t:
            if trans_points:
                # 转赠固定的积分值 查找有效期最长的排序 多条的话,转赠积分的过期时间:最早过期时间
                # 查找要转赠的积分事件
                event_ids_li = await cal_consume_events_ids(app, crm_id, from_user, event_at, trans_points,
                                                            event_type="transfer")
            else:
                not_existed = []
                # 判断要转赠的事件是否可用 记录积分详情
                for event_no in event_no_li:
                    usable_event = await points_usable_event(app.mgr, crm_id, event_no, from_user)
                    if not usable_event:
                        not_existed.append(event_no)
                    else:
                        usable_event.update(dict(used=usable_event.get('points'), remain=0))
                        event_ids_li.append(usable_event)
                assert not_existed, f"不可转赠的积分事件:{not_existed}"

            # 可用积分表 标记为转赠 添加转赠的窗口事件
            transfer_expire = event_at + timedelta(days=1)
            trans_points = 0
            logger.info(event_ids_li)
            # [{'auto_id': 5, 'event_no': 'EACH20220615202826397549953503', 'points': 10, 'remain': 0, 'used': 10}]
            pa_id_li = []
            for item in event_ids_li:
                # 添加转赠窗口期
                auto_id = item.get("auto_id")
                pa_id_li.append(auto_id)
                trans_points += item.get("used")
            got = await app.mgr.execute(PointsAvailable.update(transfer_expire=transfer_expire).where(
                PointsAvailable.auto_id.in_(pa_id_li)
            ))
            if not got or got != len(pa_id_li):
                await t.rollback()
                return dict(code=RC.HANDLER_ERROR, msg="事务更新可用积分失败")
            # 放在转赠记录表里面, 领取之后再写到事件表里面
            event_data = dict(
                transfer_no=transfer_no,
                crm_id=crm_id,
                from_user=params.get("from_user"),
                to_user=params.get("to_user"),
                points=trans_points,
                transfer_expire=transfer_expire,
                points_detail=event_ids_li,
                trans_type=params.get("trans_type"),
                event_at=event_at
            )
            await app.mgr.execute(PointsTransfer.insert(event_data).on_conflict(update=event_data))
            return dict(code=RC.OK, msg="转赠成功,待领取")
    except Exception as ex:
        logger.exception(ex)
        return dict(code=RC.HANDLER_ERROR, msg="转赠处理失败")


async def accept_one_event(app, crm_id, member_no, event_at, from_user, transfer_no, trans_detail_raw, index):
    """转移一个事件的积分"""
    # trans_detail 之前计算好的要转移ids详细信息
    tran_points = used = trans_detail_raw['used']

    expire_time = trans_detail_raw['expire_time']
    unfreeze_time = trans_detail_raw['unfreeze_time']

    transfer_no = f"{transfer_no}-{index}"
    from_event_data = dict(
        crm_id=crm_id,
        member_no=from_user,
        event_no=transfer_no,
        event_at=event_at,
        action_scene='present',
        event_type="present",
        points=tran_points,
        from_transfer_no=transfer_no,
        expire_time=expire_time,
        unfreeze_time=unfreeze_time,
    )
    # 减少from用户积分
    flag1, result1 = await lessing_points_core(app, crm_id, from_user, tran_points, consume_ids_li=[trans_detail_raw],
                                               event_data=from_event_data)
    to_event_data = dict(
        crm_id=crm_id,
        member_no=member_no,
        event_no=f"A{transfer_no}",
        event_at=event_at,
        event_type="accept",
        points=tran_points,
        from_transfer_no=transfer_no,
        expire_time=expire_time,
        unfreeze_time=unfreeze_time,
    )
    # 增加to用户积分
    flag2, result2 = await adding_points_core(app, crm_id, member_no, tran_points, to_event_data)
    if all([flag1, flag2]):
        return True, "处理一条成功"
    else:
        return False, "处理一条失败"


async def handle_accept_event(app, crm_id, member_no, event_at, params, transfer_his):
    """领取积分"""
    # 查询要领取的积分明细
    # 看是否过期
    event_ids_li = transfer_his.get('points_detail')
    transfer_expire = transfer_his.get('transfer_expire')
    trans_type = transfer_his.get('trans_type')  # trans_type是事件的积分过期时间计算
    from_user = transfer_his['from_user']
    tran_points = transfer_his['points']
    transfer_no = params['transfer_no']
    # 修改可用积分表 from_user
    # 增加积分事件记录 两条 transfer(-) accept(+)
    # 更新用户的积分概览
    try:
        min_expire_time = event_ids_li[-1]['expire_time']
        min_unfreeze_time = event_ids_li[-1]['unfreeze_time']
        async with app.mgr.atomic() as t:
            # 可用积分表中的transfer_time 修改
            for trans_detail in event_ids_li:
                ava_auto_id = trans_detail['auto_id']
                await app.mgr.execute(
                    PointsAvailable.update(transfer_expire=None).where(PointsAvailable.transfer_expire != None,
                                                                       PointsAvailable.auto_id == ava_auto_id))
            if trans_type == "by_events":
                for index, trans_detail in enumerate(event_ids_li):
                    one_flag, msg = await accept_one_event(app, crm_id, member_no, event_at, from_user, transfer_no,
                                                           trans_detail, index)
                    if not one_flag:
                        await t.rollback()
                        return dict(code=RC.HANDLER_ERROR, msg="领取转赠处理失败")
            else:  # 通过积分规整为1条
                from_event_data = dict(
                    crm_id=crm_id,
                    member_no=from_user,
                    event_no=transfer_no,
                    event_at=event_at,
                    action_scene='present',
                    event_type="present",
                    points=tran_points,
                    from_transfer_no=transfer_no,
                    expire_time=min_expire_time,  # 取最小过期时间
                    unfreeze_time=min_unfreeze_time,  # 取最小过期时间
                )
                # 减少from用户积分
                logger.info(f"减少from:{from_user}用户积分")
                flag1, result1 = await lessing_points_core(app, crm_id, from_user, tran_points,
                                                           consume_ids_li=event_ids_li, event_data=from_event_data)
                to_event_data = dict(
                    crm_id=crm_id,
                    member_no=member_no,
                    event_no=f"A{transfer_no}",
                    event_at=event_at,
                    event_type="accept",
                    points=tran_points,
                    from_transfer_no=transfer_no,  # 领取的哪个积分
                    expire_time=min_expire_time,  # 取最小过期时间
                    unfreeze_time=min_unfreeze_time,  # 取最小过期时间
                )
                # 增加to用户积分
                logger.info(f"增加to:{member_no}用户积分")
                flag2, result2 = await adding_points_core(app, crm_id, member_no, tran_points, to_event_data)
                # 更改转赠记录表
                await app.mgr.execute(PointsTransfer.update(done=1, to_user=member_no).where(
                    PointsTransfer.auto_id == transfer_his['auto_id']))
                if not all([flag1, flag2]):
                    await t.rollback()
                    return dict(code=RC.OK, msg="领取转赠处理失败")
            return dict(code=RC.OK, msg="转赠领取处理OK")

    except Exception as ex:
        logger.exception(ex)
        return dict(code=RC.HANDLER_ERROR, msg="领取转赠处理失败")


async def check_points_limit(app, crm_id, member_no, prod_points, event_at, this_rule, action_scene):
    """根据积分规则判断是否超过限制"""
    logger.info(f"this_rule is ={this_rule}")
    max_times = this_rule.get("max_times")
    max_points = this_rule.get("max_points")
    range_days = this_rule.get("range_days")
    if (not max_times) and (not max_points):
        return True
    # 没有时间范围的
    model = PointsHistory
    where = [model.crm_id == crm_id, model.member_no == member_no,
             model.action_scene == action_scene, model.reverse_status == 0]
    if range_days == 0:
        pass
    else:
        # event_at 当天时间 00:00:00 所在的时间 计算range_days 往前-days
        end_date = event_at.date() + timedelta(days=1)
        start_date = end_date - timedelta(days=range_days)
        logger.info(f'event_at:{event_at} start_date:{start_date} end_date:{end_date}')
        where.append(model.create_time >= start_date)
        where.append(model.create_time < end_date)
    result = await app.mgr.execute(model.select(fn.SUM(model.points).alias("m_points"),
                                                fn.COUNT(model.event_no).alias("m_times"))
                                   .where(*where).dicts())
    result = list(result)
    logger.info(result)
    if max_points:
        old_max_points = result[0].get("m_points") or 0
        if (old_max_points + prod_points) <= max_points:
            return True
        else:
            return False
    if max_times:
        old_max_times = result[0].get('m_times') or 0
        if (old_max_times + 1) <= max_times:
            return True
        else:
            return False


async def calculate_add_points_by_rules(app, crm_id, member_no, event_at, rule_items, params_dict, action_scene):
    """rule_items 按照时间倒序排列 [dict]
    return 积分 过期时间 冻结时间 金额"""
    prod_points, expire_term, freeze_term, total_amount = 0, None, None, 0
    if action_scene == "order_pay":
        # 支持多条积分规则的计算
        # 按照条件最高的那一次 若条件一样使用时间最新的那条规则
        # 按照base_ 排序

        sort_rules = sorted(rule_items, key=lambda i: i['change_points'], reverse=True)
        logger.info(f"sort_rules: {sort_rules}")
        order_items = params_dict.get("order_items") or []
        for order_item in order_items:
            can_to_points = order_item.get("can_to_points")
            if can_to_points:
                amount = order_items.get("pay_amount")
                total_amount += amount
        for i in sort_rules:
            ratio_points = i.get('ratio_points')
            per_money = i.get('per_money')
            change_points = i.get('change_points')
            freeze_term = i.get('freeze_term')
            expire_term = i.get('expire_term')
            this_rule = i
            if ratio_points:  # 使用积分倍率
                prod_points = total_amount * ratio_points
                break
            else:
                # 判断是否是最符合条件的
                if total_amount > per_money:
                    # 使用这个规则
                    prod_points = (total_amount % per_money) * change_points
                    break

    # 其他积分场景
    # todo 增加场景权益下的积分倍率
    else:
        # 最新的rule
        this_rule = rule_items[0]
        prod_points = this_rule.get('change_points')
        freeze_term = this_rule.get('freeze_term')
        expire_term = this_rule.get('expire_term')
    # 积分取整
    prod_points = points_rounding(prod_points)
    # 判断是否超过限制
    is_ok = await check_points_limit(app, crm_id, member_no, prod_points, event_at, this_rule, action_scene)
    if not is_ok:
        logger.info(f"超过限制 rule={this_rule}")
        assert False, "该场景值增加积分超过限制"
    return prod_points, expire_term, freeze_term, total_amount
