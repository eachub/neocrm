
from datetime import datetime
from .base import *
from common.models.points import *
from common.models.member import *
from sanic.log import logger


async def add_record_from_dict(mgr, ThatModel, obj, excluded=[], on_conflict=2, target_keys=[]):
    record = {}
    for k, v in obj.items():
        if k in excluded: continue
        if v is None or v == "": continue
        key = getattr(ThatModel, k, None)
        if key: record[key] = v
    ###
    if on_conflict == 0:
        return await mgr.execute(ThatModel.insert(record))
    if on_conflict == 1:
        return await mgr.execute(ThatModel.replace(record))
    if on_conflict == 2:
        conflict_target = None if not target_keys else \
            [getattr(ThatModel, k) for k in target_keys]
        return await mgr.execute(ThatModel.insert(record).on_conflict(
            update=record, conflict_target=conflict_target))
    ###
    assert target_keys, "必须指定target_keys"
    conds = [(getattr(ThatModel, k) == obj[k]) for k in target_keys]
    ###
    if on_conflict == 3:
        got = await mgr.execute(ThatModel.update(record).where(*conds))
        return got or (await mgr.execute(ThatModel.insert(record).on_conflict(update=record)))
    if on_conflict == 4:
        try:
            return await mgr.execute(ThatModel.insert(record))
        except IntegrityError:
            return await mgr.execute(ThatModel.update(record).where(*conds))
    raise RuntimeError("不支持的参数on_conflict")


async def _query_by_key_id(mgr, excluded, ThatModel, params):
    try:
        where = [getattr(ThatModel, k) == v for k, v in params.items()]
        q = ThatModel.select().where(*where) if where else ThatModel.select()
        items = await mgr.execute(q)
        return [model_to_dict(item, exclude=excluded) for item in items]
    except Exception as ex:
        logger.exception(ex)
        

async def get_rules_by_action(mgr, crm_id, action_scene, rule_id=None):
    model = PointsProduceRules
    where = [model.crm_id == crm_id, model.action_scene == action_scene]
    if rule_id is not None:
        where.append(model.rule_id == rule_id)
    rule_items = await mgr.execute(model.select().where(*where).order_by(model.create_time.desc()).dicts())
    return rule_items


async def get_points_his_event(mgr, crm_id, event_no):
    """判断积分事件是否存在"""
    try:
        one = await mgr.get(PointsHistory, crm_id=crm_id, event_no=event_no)
        data = model_to_dict(one, exclude=["create_time", "update_time", "auto_id"])
        return data
    except DoesNotExist:
        logger.info(f"not found in PointsHistory event_no={event_no}")
        return {}
    
    
async def points_usable_event(mgr, crm_id, event_no, member_no=None):
    """查找可用积分事件"""
    try:
        if member_no:
            one = await mgr.get(PointsAvailable, crm_id=crm_id, event_no=event_no, member_no=member_no)
        else:
            one = await mgr.get(PointsAvailable, crm_id=crm_id, event_no=event_no)
        data = model_to_dict(one, exclude=["create_time", "update_time", "auto_id"])
        return data
    except DoesNotExist:
        logger.info(f"not found in PointsAvailable event_no={event_no}")
        return {}
    
    
async def member_active_points(mgr, crm_id, member_no, event_at=None):
    """会员可用积分"""
    if not event_at:
        event_at = datetime.now()
    _model = PointsAvailable
    where = [
        (_model.expire_time >= event_at) | (_model.expire_time == None),
        (_model.unfreeze_time <= event_at) |  (_model.unfreeze_time == None),
        _model.member_no==member_no,
        _model.crm_id==crm_id,
        (_model.transfer_expire <= event_at) | (_model.transfer_expire==None),
    ]
    result = await mgr.get(
        _model.select(fn.SUM(_model.points).alias("act_points")).where(*where).dicts())
    
    act_points = result['act_points'] or 0
    logger.info(f"{member_no} 可用积分:{act_points} {event_at}")
    return act_points


async def member_unexpire_points(mgr, crm_id, member_no, event_at=None):
    """获取会员未过期的积分 包括冻结和可用 转赠出去的不能被冲"""
    if not event_at:
        event_at = datetime.now()
    _model = PointsAvailable
    where = [
        (_model.expire_time >= event_at) | (_model.expire_time == None),
        _model.member_no == member_no,
        _model.crm_id == crm_id,
        (_model.transfer_expire <= event_at) | (_model.transfer_expire == None),
    ]
    result = await mgr.get(
        _model.select(fn.SUM(_model.points).alias("act_points")).where(*where).dicts())

    act_points = result['act_points'] or 0
    logger.info(f"{member_no} 未过期积分:{act_points} {event_at}")
    return act_points


async def points_transfer_event(mgr, crm_id, transfer_no):
    """查找积分转赠记录"""
    try:
        one = await mgr.get(PointsTransfer, crm_id=crm_id, transfer_no=transfer_no, done=0)
        data = model_to_dict(one, exclude=["create_time", "update_time", "auto_id"])
        return data
    except DoesNotExist:
        logger.info(f"not found in PointsTransfer transfer_no={transfer_no}")
        return {}
    
    
async def query_crm_info(mgr,**kwargs):
    """获取所有的crm_info信息"""
    excluded = [CRMModel.auto_id, CRMModel.create_time]
    return await _query_by_key_id(mgr, excluded, CRMModel, kwargs)


def field_model_to_dict(model, exclude=[], only=[], fields_from_query=None):
    """exclude 和 only 传递的field的字符串"""
    exclude1 = []
    only1 = []
    for field in model._meta.sorted_fields:
        if field.name in exclude:
            exclude1.append(field)
        if field.name in only:
            only1.append(field)
    return model_to_dict(model, exclude=exclude1, only=only1, fields_from_query=fields_from_query)


async def get_tag_dict(app, crm_id, key="tag_name"):
    items = await app.mgr.execute(TagInfo.select(
            TagInfo.tag_id, getattr(TagInfo, key),
        ).where(
            TagInfo.crm_id == crm_id,
            TagInfo.removed == 0,
            getattr(TagInfo, key).is_null(False),
        ))
    return {i.tag_id: getattr(i, key) for i in items}


async def fetch_benefit_rules(mgr, crm_id, benefit_type=None):
    model = BenefitRuleInfo
    where = [model.crm_id==crm_id]
    if benefit_type:
        where.append(model.benefit_type==benefit_type)
    return await mgr.execute(model.select().where(*where))