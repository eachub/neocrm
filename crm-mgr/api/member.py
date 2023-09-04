from biz.crm import build_tree
from biz.member import *
from common.biz.crm import cache_get_crm_channel_map
from common.biz.utils import model_build_distr
from common.models.member import *
from common.models.points import *
from common.biz.wrapper import safe_crm_instance, except_decorator
from mtkext.dt import datetimeToString
from biz.utils import get_channle_type_dict, fetch_model_increment_list, get_channel_dict
from common.biz.codec import decrypt_item
from biz.member import get_members_by_member_nos

bp = Blueprint('bp_member_mgr', url_prefix="/member")

StatusMaping = {
    MemberStatus.NORMAL: "普通会员",
    MemberStatus.CANCEL: "注销会员",
    MemberStatus.FAMILY: "家庭组会员",
}


@bp.post('/<crm_id>/list')
@safe_crm_instance
async def api_member_list(request, crm_id):
    #
    app = request.app
    params_dict = request.json
    model = MemberInfo
    mobile = params_dict.get("mobile")
    member_no = params_dict.get("member_no")
    create_start = params_dict.get("create_start")
    create_end = params_dict.get("create_end")
    order_by = params_dict.get("order_by") or "create_time"
    order_asc = params_dict.get("order_asc") or 0
    page_id = params_dict.get("page_id", 1)
    page_size = params_dict.get("page_size", 10)
    status = params_dict.get("status")
    update_start = params_dict.get("update_start")
    update_end = params_dict.get("update_end")
    nickname = params_dict.get("nickname")
    assert not status or status in ['NORMAL', 'CANCEL', 'FAMILY'], "会员status参数错误或缺失"
    where = [MemberInfo.crm_id == crm_id]
    if mobile:
        enc_mobile = encrypt_item(app.cipher, mobile)
        where.append(MemberInfo.enc_mobile == enc_mobile)
    if member_no:
        where.append(MemberInfo.member_no == member_no)
    if create_start:
        from_dt = datetimeFromString(create_start)
        where.append(MemberInfo.create_time > from_dt)
    if create_end:
        to_dt = datetimeFromString(create_end)
        where.append(MemberInfo.create_time < to_dt)
    if update_start:
        from_update = datetimeFromString(update_start)
        where.append(MemberInfo.update_time >= from_update)
    if update_end:
        to_update = datetimeFromString(update_end)
        where.append(MemberInfo.update_time <= to_update)
    if status:
        member_status = getattr(MemberStatus, status)
        where.append(MemberInfo.member_status == member_status)
    if nickname:
        where.append(MemberInfo.nickname == nickname)
    sql = model.select().where(*where)
    total = await app.mgr.count(sql)

    if order_by:
        order_field = getattr(model, order_by)
        if order_asc == 0:
            sql = sql.order_by(order_field.desc()).paginate(int(page_id), int(page_size))
        else:
            sql = sql.order_by(order_field.asc()).paginate(int(page_id), int(page_size))
    logger.info(sql.sql())
    items = await app.mgr.execute(sql.dicts())
    member_no_li = [member.get('member_no') for member in items]
    # 积分信息
    points_infos = await fetch_member_extra_info(app.mgr, crm_id, PointsSummary, member_no_li)
    # 家庭组信息
    family_infos = await fetch_member_extra_info(app.mgr, crm_id, MemberFamily, member_no_li, list_flag=True)
    # 扩展信息
    extend_infos = await fetch_member_extra_info(app.mgr, crm_id, MemberExtendInfo, member_no_li)
    # 来源信息
    source_infos = await fetch_member_extra_info(app.mgr, crm_id, MemberSourceInfo, member_no_li)
    result = []
    for item in items:

        member_status = item.get('member_status')
        # 格式化 member_status为字符串
        str_status = StatusMaping.get(member_status)
        if str_status:
            item['member_status'] = str_status
        _member_no = item.get('member_no')
        ###
        family = family_infos.get(_member_no)
        if family: item['family'] = [model_to_dict(i) for i in family]
        points = points_infos.get(_member_no)
        if points: item['points'] = model_to_dict(points)
        extend_info = extend_infos.get(_member_no)
        if extend_info:
            item['occupation'] = extend_info.occupation
        source_info = source_infos.get(_member_no)
        if source_info:
            # 翻译 channel_code
            source_info = model_to_dict(source_info)
            channel_code = source_info.get("channel_code")
            if channel_code:
                channel_map = await cache_get_crm_channel_map(app.mgr, app.redis, crm_id)
                source_info['channel_name'] = channel_map.get(channel_code, {}).get("channel_name")
            item['source_info'] = source_info
        result.append(item)

    return json(dict(code=RC.OK, msg="OK", data=dict(items=result, total=total)))


@bp.post("/<crm_id>/channel/add")
@safe_crm_instance
async def api_member_channel_add(request, crm_id):
    app = request.app
    params_dict = request.json
    model = ChannelInfo
    # 参数校验
    channel_type = params_dict.get("channel_type")
    channel_name = params_dict.get("channel_name")
    assert type(channel_type) is list, "channel_type格式错误或缺失"
    assert type(channel_name) is str, "channel_name格式错误或缺失"
    # 判断是否存在
    item = await app.mgr.execute(model.select().where(model.channel_name == channel_name, model.crm_id == crm_id))
    assert not item, "渠道名称已存在"
    params_dict.update(dict(crm_id=crm_id))
    channel_id = await add_record_from_dict(app.mgr, model, params_dict, on_conflict=0)
    # 渠道code生成 写入
    channel_code = await gen_channle_code(app, crm_id, channel_type, channel_id)
    await app.mgr.execute(model.update(channel_code=channel_code).where(model.channel_id == channel_id))
    return json(dict(code=RC.OK, msg="保存成功"))


@bp.post("/<crm_id>/channel/list")
@safe_crm_instance
async def api_member_channel_list(request, crm_id):
    app = request.app
    params_dict = request.json
    model = ChannelInfo
    # 参数
    keyword = params_dict.get("keyword")
    page_id = params_dict.get("page_id", 1)
    page_size = params_dict.get("page_size", 10)
    order_by = params_dict.get("order_by", "update_time")
    order_asc = params_dict.get("order_asc", 0)
    where = [model.crm_id == crm_id, model.is_deleted==False]
    if keyword:
        where.append(model.channel_name.contains(keyword))
    sql = model.select().where(*where)
    total = await app.mgr.count(sql)
    if order_by:
        order_field = getattr(model, order_by)
        if order_asc == 0:
            sql = sql.order_by(order_field.desc())
        else:
            sql = sql.order_by(order_field.asc())
    if page_id and page_size:
        sql = sql.paginate(int(page_id), int(page_size))

    items = await app.mgr.execute(sql.dicts())
    # 处理渠道类型
    channel_dict = await get_channel_dict(app, crm_id)
    logger.info(channel_dict)
    for item in items:
        channel_type = item.get("channel_type")  # 存放的是id列表
        # 处理
        ret_name_li = [channel_dict.get(i) or '' for i in channel_type]
        item['channel_type_name'] = '|'.join(ret_name_li)
    return json(dict(code=RC.OK, msg="OK", data=dict(items=items, total=total)))


@bp.post("/<crm_id>/channel/update")
@safe_crm_instance
async def api_member_channel_update(request, crm_id):
    app = request.app
    params_dict = request.json
    model = ChannelInfo
    channel_id = params_dict.get("channel_id")
    assert channel_id, "channel_id参数缺失"
    where = [model.crm_id == crm_id, model.channel_id == channel_id]
    existd = await app.mgr.execute(model.select().where(*where))
    assert existd, "无法更新channel_id不存在"
    inobj = peewee_normalize_dict(model, params_dict)
    await app.mgr.execute(model.update(inobj).where(*where))
    return json(dict(code=RC.OK, msg="更新成功"))


@bp.post("/<crm_id>/channel/delete")
@safe_crm_instance
async def api_member_channel_delete(request, crm_id):
    app = request.app
    params_dict = request.json
    model = ChannelInfo
    channel_id = params_dict.get("channel_id")
    assert channel_id, "channel_id参数缺失"
    where = [model.crm_id == crm_id, model.channel_id == channel_id]
    await app.mgr.execute(model.update(is_deleted=True).where(*where))
    return json(dict(code=RC.OK, msg="删除成功"))


@bp.post("/<crm_id>/black_add")
@except_decorator
async def api_member_black_add(request, crm_id):
    app = request.app
    params_dict = request.json
    block_time = params_dict.get("block_time", 0)
    assert type(block_time) is int, "block_time格式错误"
    black_list = params_dict.get("black_list")
    assert type(black_list) is list, "black_list参数缺失或格式错误"
    desc = params_dict.get('desc')
    members = await get_members_by_member_nos(app.mgr, crm_id, member_nos=black_list)
    if not members:
        raise ValueError("会员不存在或者已经在黑名单")
    if len(set(black_list)) != len(members):
        raise ValueError("有会员不存在或者已经在黑名单")
    resp = await handle_member_add_black(app, crm_id, black_list, block_time, params_dict)
    return json(resp)


@bp.post("/<crm_id>/black/list")
@safe_crm_instance
async def api_member_black_query(request, crm_id):
    """查看黑名单"""
    app = request.app
    params_dict = request.json
    model = BlackMemberInfo
    # 参数
    page_id = params_dict.get("page_id", 1)
    page_size = params_dict.get("page_size", 10)
    order_by = params_dict.get("order_by", "update_time")
    order_asc = params_dict.get("order_asc", 0)
    where = [model.crm_id == crm_id, model.status == 1]
    sql = model.select().where(*where)
    total = await app.mgr.count(sql)
    if order_by:
        order_field = getattr(model, order_by)
        if order_asc == 0:
            sql = sql.order_by(order_field.desc())
        else:
            sql = sql.order_by(order_field.asc())
    if page_id and page_size:
        sql = sql.paginate(int(page_id), int(page_size))

    items = await app.mgr.execute(sql.dicts())
    return json(dict(code=RC.OK, msg="OK", data=dict(items=items, total=total)))


@bp.post("/<crm_id>/black/remove")
@safe_crm_instance
async def api_member_black_remove(request, crm_id):
    """移除黑名单"""
    app = request.app
    params_dict = request.json
    model = BlackMemberInfo
    member_no = params_dict.get("member_no")
    assert member_no, "member_no参数缺失"
    # 查看是否正常
    where = [model.crm_id == crm_id, model.member_no == member_no]
    existd = await app.mgr.execute(model.select().where(*where))
    assert existd, "会员号没有被拉黑"
    if existd[0].status == 0:
        return json(dict(code=RC.OK, msg="会员已经移除黑名单,不用重复移除"))
    await app.mgr.execute(model.update(status=0).where(*where))
    return json(dict(code=RC.OK, msg="移除黑名单成功"))


@bp.get("/<crm_id>/tag/tree")
@safe_crm_instance
async def handle_tag_tree(request, crm_id):
    tree = await build_tag_tree(request.app, crm_id)
    if tree: return json(dict(code=RC.OK, msg="ok", data=tree))
    return json(dict(code=RC.DATA_NOT_FOUND, msg="实例匹配不到标签树"))


@bp.get("/<crm_id>/tag/detail")
@safe_crm_instance
async def handle_tag_detail(request, crm_id):
    try:
        tag_id = int(request.args.get("tag_id") or 0)
        assert tag_id, "缺少tag_id参数"
    except AssertionError as ex:
        return json(dict(code=RC.PARSER_FAILED, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.PARAMS_INVALID, msg=f"参数错误：{ex}"))
    ###
    try:
        tag = await get_tag_detail(request.app, crm_id, tag_id)
        if tag:
            return json(dict(code=RC.OK, msg="ok", data=tag))
        return json(dict(code=RC.DATA_NOT_FOUND, msg="匹配不到标签"))
    except AssertionError as ex:
        return json(dict(code=RC.HANDLER_ERROR, msg=str(ex)))
    except Exception as ex:
        logger.exception(ex)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务内部故障"))


@bp.post("/<crm_id>/tag/level_update")
@safe_crm_instance
async def api_tag_level_update(request, crm_id):
    """
    更新 有时间范围或区间值的标签
    更改 level.level_name rules desc 里面存在是level的配置
    单指标区间
    desc:[
        {dr
        span:{"level_name": "停留低时长","value": [null,"10"],"level_id": 601159}
        name
        text
        }
    ]

    level.rules 存放的值[
        {
            "level_name": "停留低时长",
            "value": [
                null,
                "10"
            ],
            "name": "sum",
            "text": "页面停留时长",
            "dr": [
                7
            ]
        }
    ]
    """
    app = request.app
    params_dict = request.json
    tag_id = params_dict.get("tag_id")
    assert type(tag_id) is int, "tag_id格式错误或缺失"
    desc = params_dict.get("desc")
    assert type(desc) is list, "传入合法的desc参数"
    one_desc = desc[0]
    span_li = one_desc.get('spans')
    dr = one_desc.get('dr')  # dr 放在span同一等级
    for level in span_li:
        level_id = level.get('level_id')
        level_name = level.get('level_name')
        level['dr'] = dr
        rules = level
        level_obj = dict(level_id=level_id, level_name=level_name, rules=[rules])
        await add_record_from_dict(app.mgr, TagLevel, level_obj, on_conflict=2)
    # 更新desc 信息
    await app.mgr.execute(
        TagInfo.update(desc=params_dict['desc']).where(TagInfo.tag_id == tag_id, TagInfo.crm_id == crm_id))
    # 重新构建 t_tags_info里面的desc信息
    # await tag_rebuild(app, crm_id, tag_id=tag_id)
    data = await get_tag_brief(app, crm_id, tag_id)
    return json(dict(code=RC.OK, msg="OK", data=data))


@bp.get("/<crm_id>/member_attrs")
@safe_crm_instance
async def api_get_member_attrs(request, crm_id):
    """从order_items中统计指标"""
    app = request.app
    params_dict = request.args
    member_no = params_dict.get('member_no')
    member = await app.mgr.execute(WechatUserInfo.select().where(WechatUserInfo.member_no == member_no))
    assert member, "member_no查找不到会员"
    now = datetime.now()
    start_dt = now - timedelta(days=30)
    now_dt = datetimeToString(now)
    start_dt = datetimeToString(start_dt)
    # 计算指标
    model = OrderInfo
    all_mounts = await app.mgv.execute(model.select(fn.SUM(model.pay_amount).alias("amount")).where(
        model.member_no == member_no, model.crm_id == crm_id
    ).dicts())
    all_mounts = all_mounts[0].get("amount") if all_mounts else 0
    mounts_30 = await app.mgv.execute(model.select(fn.SUM(model.pay_amount).alias("amount")).where(
        model.member_no == member_no, model.crm_id == crm_id, model.create_time > start_dt, model.create_time <= now
    ).dicts())
    mounts_30 = mounts_30[0].get('amount') if mounts_30 else 0
    # 消费次数
    order_times_30 = await app.mgv.counts(model.select().where(
        model.member_no == member_no, model.crm_id == model.crm_id
    ))
    # 访问小程序天数 todo 要放在这里吗？
    # 获取openid
    openid = member_no.openid
    app_times_sql = f"""SELECT count(*) as count from (
        SELECT date_format(create_time ,'%Y-%m-%d') as 'date'  
        from db_event.t_wmp_app_event
        where openid='{openid}' and create_time > '{start_dt}' and create_time <='{now_dt}'
        group by date_format(create_time ,'%Y-%m-%d')
    ) t1"""
    app_times = await app.mgv.execute(PointsHistory.raw(app_times_sql).dicts())
    app_times = app_times[0].get("count") if app_times else 0
    # 访问小程序


@bp.get('/<crm_id>/show360')
@safe_crm_instance
async def api_show360(request, crm_id):
    app = request.app
    params_dict = request.args
    member_no = params_dict.get('member_no')
    ###
    # 获取会员的标签数据
    pass
    #
    # await fill_user_tags(app.kvdb["bind_tag"], member_no, tag_dict)
    # await fill_user_tags(app.kvdb["rule_tag"], member_no, tag_dict)
    # tags = await tag_translate(app, crm_id, tag_dict.items())
    # 指标的计算 总消耗金额  近30天：消费次数 消费金额 访问小程序天数 小程序加购次数

    # 获取会员的统计数据 总消费金额 attr
    # 30天访问小程序天数，db_event.t_wmp_app_event
    # 30天小程序加购次数，db_event.t_wmp_custom_event
    return json(dict(code=RC.OK, msg="OK", data=dict(tags={}, attr=None)))


@bp.get("/<crm_id>/channel_types")
async def api_instance_info(request, crm_id):
    try:
        app = request.app
        model = CRMChannelTypes
        items = await app.mgr.execute(
            model.select(model.type_id, model.parent_id, model.name).where(model.crm_id == crm_id).dicts())
        # 转换成树形结构
        result = await build_tree(items, id_key='type_id', parent_id="parent_id")
        return json(dict(code=RC.OK, msg="OK", data=result))
    except DoesNotExist:
        return json(dict(code=RC.DATA_NOT_FOUND, msg="crm实例不存在"))
    except AssertionError as e:
        return json(dict(code=RC.PARAMS_INVALID, msg=str(e), data=None))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post('/<crm_id>/info/increment')
@except_decorator
async def api_member_list(request, crm_id):
    """轮训会员信息接口"""
    app = request.app
    params_dict = request.json
    model = MemberInfo
    where = []
    if crm_id != "common":
        crm_id = crm_id
    member_no = params_dict.get("member_no")
    if member_no: where.append(model.member_no == member_no)
    resp = await fetch_model_increment_list(app, crm_id, model, params_dict, exclude=[model.info_id], base_where=where)
    # 更新 扩展信息积分信息 来源信息等信息
    member_list = resp['data']['items']
    member_no_li = [member.get('member_no') for member in member_list]
    # 扩展信息
    extend_infos = await fetch_member_extra_info(app.mgr, crm_id, MemberExtendInfo, member_no_li)
    # 来源信息
    source_infos = await fetch_member_extra_info(app.mgr, crm_id, MemberSourceInfo, member_no_li)
    # 积分信息
    points_infos = await fetch_member_extra_info(app.mgr, crm_id, PointsSummary, member_no_li)
    # 家庭组信息
    family_infos = await fetch_member_extra_info(app.mgr, crm_id, MemberFamily, member_no_li, list_flag=True)
    # 平台信息
    SUPPORT_PLATFORM = app.conf.SUPPORT_PLATFORM
    platform_mping = dict()
    for platform in SUPPORT_PLATFORM:
        model = get_model_by_platform(platform)
        if model:
            plt_info = await fetch_member_extra_info(app.mgr, crm_id, model, member_no_li)
            platform_mping[platform] = plt_info
    for member in member_list:
        member_no = member.get('member_no')
        extend = extend_infos.get(member_no)
        if extend: member['extend'] = model_to_dict(extend)
        source = source_infos.get(member_no)
        if source: member['source'] = model_to_dict(source)
        points = points_infos.get(member_no)
        if points: member['points'] = model_to_dict(points)
        family = family_infos.get(member_no)
        if family: member['family'] = [model_to_dict(i) for i in family]
        for platform in SUPPORT_PLATFORM:
            tmp = platform_mping.get(platform, {}).get(member_no)
            if tmp:
                member[f'{platform}_member_info'] = model_to_dict(tmp)
    return json(resp)


@bp.post('/<crm_id>/source/increment')
@except_decorator
async def api_member_source_list(request, crm_id):
    """轮询会员信息接口"""
    app = request.app
    params_dict = request.json
    model = MemberSourceInfo
    where = []
    if crm_id != "common":
        where = [model.crm_id == crm_id]
    resp = await fetch_model_increment_list(app, crm_id, model, params_dict, exclude=[model.auto_id], base_where=where)
    return json(resp)


@bp.post('/<crm_id>/family_increment')
@except_decorator
async def api_family_member_list(request, crm_id):
    """获取数据接口"""
    app = request.app
    params_dict = request.json
    model = MemberFamily
    where = []
    if crm_id != "common":
        where = [model.crm_id == crm_id]
    resp = await fetch_model_increment_list(app, crm_id, model, params_dict, exclude=None, base_where=where)
    return json(resp)


@bp.post("/<crm_id>/tags_increment")
@except_decorator
async def api_member_tags_list(request, crm_id):
    app = request.app
    params_dict = request.json
    model = getUsertags()
    where = []
    if crm_id != "common":
        where = [model.crm_id == crm_id]
    resp = await fetch_model_increment_list(app, crm_id, model, params_dict, exclude=[model.auto_id], base_where=where)
    data = resp.get("data")
    # 标签等级转换成属性
    for row in data:
        for k, v in row.items():
            if k.start_with("tag_"):
                level_id = v
                lev_info = app.base_config['level_info_mp'].get(level_id)
                level_name = lev_info.get("level_name")
                row[k] = level_name
    return json(resp)


@bp.get('/<crm_id>/member_config')
@except_decorator
async def api_member_config(request, crm_id):
    """获取crm实例的基础配置"""
    app = request.app
    model = CRMModel
    item = await app.mgr.get(model.select().where(model.crm_id == crm_id))
    result = model_to_dict(item, only=[model.points_config, model.benefit_config, model.level_config])
    return json(dict(code=RC.OK, msg="OK", data=result))


@bp.post('/<crm_id>/config_update')
@except_decorator
async def api_member_config_update(request, crm_id):
    """实例配置更新"""
    app = request.app
    params_dict = request.json
    model = CRMModel
    peewee_normalize_dict(model, params_dict)
    await app.mgr.execute(model.update(params_dict).where(model.crm_id == crm_id))
    return json(dict(code=RC.OK, msg="OK"))


@bp.get("/<crm_id>/level_detail")
@except_decorator
async def api_member_level_detail(request, crm_id):
    app = request.app
    model = MemberLevelInfo

    # 全局的规则
    item = await app.mgr.get(CRMModel.select().where(CRMModel.crm_id == crm_id))
    crm_obj = model_to_dict(item, only=[CRMModel.level_config])
    # 等级信息
    where = [model.crm_id == crm_id, model.deleted == False]
    items = await app.mgr.execute(model.select().where(*where).order_by(model.level_no))
    result = [model_to_dict(one, exclude=[model.update_time]) for one in items]
    return json(dict(code=RC.OK, msg="OK", data=dict(level_config=crm_obj.get("level_config"), level_list=result)))


@bp.post('/<crm_id>/level_cfg_save')
@except_decorator
async def api_member_level_cfg(request, crm_id):
    app = request.app
    params_dict = request.json
    model = MemberLevelInfo
    #
    level_config = params_dict.get("level_config")
    assert level_config and type(level_config) is dict, "level_config参数错误或缺失"
    try:
        async with app.mgr.atomic() as t:
            ###
            # 检验参数
            give_rules = level_config.get("give_rules")
            downgrade = level_config.get("downgrade")
            deduct_rules = level_config.get("deduct_rules")
            assert type(give_rules) is list, "give_rules参数缺失或错误"
            assert type(downgrade) is dict, "downgrade 参数缺失或错误"
            assert type(deduct_rules) is list, "deduct_rules 参数缺失或错误"
            await app.mgr.execute(CRMModel.update(level_config=level_config))
            ###
            # 更新等级的信息
            level_list = params_dict.get("level_list")
            assert type(level_list) is list, "level_list 参数缺失或错误"
            # 删除之前的 新写入新的
            if level_list:
                await app.mgr.execute(model.update(deleted=True).where(model.crm_id == crm_id))
            for level in level_list:
                level['deleted'] = False
            if level_list:
                for level in level_list:
                    level_id = level.get("level_id")
                    level['crm_id'] = crm_id
                    # 更新
                    if level_id:
                        await add_record_from_dict(app.mgr, model, level, on_conflict=3, target_keys=['level_id'])
                    # 写入
                    else:
                        await add_record_from_dict(app.mgr, model, level, on_conflict=2)
        return json(dict(code=RC.OK, msg="保存成功", data=None))
    except Exception as ex:
        logger.exception(ex)
        await t.rollback()
        return json(dict(code=RC.DATA_EXCEPTION, msg="处理失败"))


@bp.post('/<crm_id>/level_save')
@except_decorator
async def api_member_level_add(request, crm_id):
    """新增或更新一条level"""
    app = request.app
    params_dict = request.json
    model = MemberLevelInfo
    level_no = params_dict.get("level_no")
    assert type(level_no) is int, "level_no 参数缺失或格式错误"
    level_id = params_dict.pop("level_id", None)
    try:
        async with app.mgr.atomic() as t:
            if level_id:
                # 更新
                await app.mgr.execute(model.update(params_dict).where(model.level_id == level_id))
            else:  # 新增
                if level_no != 0:
                    min_score = params_dict.get("min_score")
                    assert type(min_score) is int, "min_score 参数缺失或格式错误"
                name = params_dict.get("name")
                assert type(name) is str, "name参数格式错误"
                down_able = params_dict.get("down_able")
                assert type(down_able) is bool, "down_able参数缺失或格式错误"
                if down_able is True:
                    min_ship_times = params_dict.get("min_ship_times")
                    assert type(min_ship_times) is int, "可降级类型传入min_ship_times参数"
                params_dict['crm_id'] = crm_id
                level_id = await add_record_from_dict(app.mgr, model, params_dict, on_conflict=2)
                # 降级策略
        return json(dict(code=RC.OK, msg="OK", data=level_id))
    except Exception as ex:
        logger.exception(ex)
        await t.rollback()
        return json(dict(code=RC.DATA_EXCEPTION, msg="处理失败"))


@bp.post("/<crm_id>/level_delete")
@except_decorator
async def api_member_level_delete(request, crm_id):
    app = request.app
    params_dict = request.json
    model = MemberLevelInfo
    level_id = params_dict.get("level_id")
    got = await app.mgr.execute(model.update(delete=True).where(model.level_id == level_id))
    if got:
        msg = "删除成功"
    else:
        msg = "不存在或已经被删除"
    return json(dict(code=RC.OK, msg=msg, data=None))


@bp.post("/<crm_id>/level_bonus_save")
@except_decorator
async def api_member_level_bonus_save(request, crm_id):
    """等级奖励积分配置"""
    app = request.app
    params_dict = request.json
    model = MemberLevelInfo
    level_id = params_dict.get("level_id")
    points = params_dict.get("points")
    score = params_dict.get("score")
    coupon = params_dict.get("coupons")
    level_bonus = dict(points=points, score=score, coupon=coupon)
    await app.mgr.execute(model.update(level_bonus=level_bonus).where(model.level_id == level_id))
    return json(dict(code=RC.OK, msg="OK", data=None))


@bp.post("/<crm_id>/level_benefit_save")
@except_decorator
async def api_member_level_benefit(request, crm_id):
    """等级权益配置"""
    app = request.app
    params_dict = request.json
    model = BenefitRulesMap
    level_id = params_dict.get("level_id")
    benefit_id_li = params_dict.get("benefit_id_li")
    in_objs = []
    for benefit_id in benefit_id_li:
        in_obj = dict(level_id=level_id, benefit_id=benefit_id, crm_id=crm_id)
        in_objs.append(in_obj)
    if in_objs:
        await app.mgr.execute(model.insert_many(in_objs).on_conflict_ignore())
    return json(dict(code=RC.OK, msg="OK", data=None))


# 权益相关的接口
@bp.post("/<crm_id>/benefit_update")
@except_decorator
async def api_member_benefit_update(request, crm_id):
    """会员权益配置更新"""
    # 请求参数 benefit_id  title icon describe enable
    app = request.app
    params_dict = request.json
    model = MemberBenefit
    benefit_id = params_dict.get("benefit_id")
    params_dict.update(dict(crm_id=crm_id))
    await app.mgr.get(model, benefit_id=benefit_id, crm_id=crm_id)
    await add_record_from_dict(app.mgr, model, params_dict, on_conflict=3, target_keys=['crm_id', 'benefit_id'])
    return json(dict(code=RC.OK, msg="OK"))


@bp.post('/<crm_id>/defined_benefit_rule_save')
@except_decorator
async def api_defined_benefit_add(request, crm_id):
    """自定义会员权益规则保存"""
    # 参数 custom_config benefit_id title benefit_type title enable
    app = request.app
    params_dict = request.json
    model = MemberBenefit
    benefit_id = params_dict.get("benefit_id")
    params_dict.update(dict(crm_id=crm_id))
    # 更新
    if benefit_id:
        await app.mgr.get(model, crm_id=crm_id, benefit_id=benefit_id)
        await add_record_from_dict(app.mgr, model, params_dict, on_conflict=3, target_keys=['crm_id', 'benefit_id'])
    # 新增
    else:
        title = params_dict.get('title')
        assert type(title) is str, "title参数缺失或格式错误"
        benefit_type = params_dict.get("benefit_type")
        assert type(benefit_type) is str, "benefit_type 参数缺失或格式错误"

        await add_record_from_dict(app.mgr, model, params_dict, on_conflict=1)
    return json(dict(code=RC.OK, msg="OK", data=benefit_id))


@bp.post('/<crm_id>/benefit_rule_add')
@except_decorator
async def api_member_benefit_rule_add(request, crm_id):
    """权益规则添加更新"""
    app = request.app
    params_dict = request.json
    model = BenefitRuleInfo
    benefit_id = params_dict.get("benefit_id")
    assert type(benefit_id) is int, "benefit_id 参数缺失或格式错误"
    benefit_type = params_dict.get("benefit_type")
    assert type(benefit_type) is str, "benefit_type 参数缺失或格式错误"
    # 自定义的权益 只保存规则id
    if benefit_type == "be_customize":
        custom_config = params_dict.get("custom_config")
        assert type(custom_config) is dict, "custom_config 参数缺失或格式错误"
        await app.mgr.execute(
            MemberBenefit.update(custom_config=custom_config).where(MemberBenefit.benefit_id == benefit_id))
    else:
        content = params_dict.get("content")
        assert type(content) is dict, "content 参数缺失或格式错误"
        in_obj = peewee_normalize_dict(model, params_dict)
        await app.mgr.execute(model.insert(in_obj))
        return json(dict(code=RC.OK, msg="OK"))


@bp.post('/<crm_id>/benefit_list')
@except_decorator
async def api_member_benefit_list(request, crm_id):
    """权益列表"""
    app = request.app
    params_dict = request.json or {}
    model = MemberBenefit
    where = [model.crm_id == crm_id, model.deleted == False]
    keyword = params_dict.get("keyword")
    if keyword:
        where.append((model.title.contains(keyword) | model.describe.contains(keyword)))
    items = await app.mgr.execute(model.select().where(*where))
    result = []
    for one in items:
        tmp_dict = model_to_dict(one, exclude=[model.create_time, model.update_time])
        benefit_id = tmp_dict.get("benefit_id")
        # rules_num
        tmp_dict['rules_num'] = await app.mgr.count(BenefitRuleInfo.select().where(
            BenefitRuleInfo.benefit_id==benefit_id, BenefitRuleInfo.deleted==False))
        result.append(tmp_dict)
    return json(dict(code=RC.OK, msg="OK", data=dict(items=result)))


@bp.post('/<crm_id>/benefit_detail')
@except_decorator
async def api_member_benefit_detail(request, crm_id):
    app = request.app
    params_dict = request.json
    model = MemberBenefit
    benefit_id = params_dict.get("benefit_id")
    ###
    # 权益基础信息
    base_info = await app.mgr.get(model.select().where(model.crm_id == crm_id, model.benefit_id == benefit_id))
    base_info = model_to_dict(base_info,
                              exclude=[model.update_time, model.create_time, model.deleted, model.custom_config])
    ###
    # 获取权益规则

    benefit_dict = await build_benefit_rules_cfg(app, crm_id, benefit_id)
    return json(dict(code=RC.OK, msg="OK", data=dict(benefit_info=base_info, rules_dict=benefit_dict)))


@bp.post('/<crm_id>/benefit_cfg_save')
@except_decorator
async def api_benefit_cfg_save(request, crm_id):
    app = request.app
    params_dict = request.json
    model = MemberBenefit
    benefit_info = params_dict.get("benefit_info")
    # assert type(benefit_id) is int, "benefit_id 参数缺失或格式错误"
    benefit_type = benefit_info.get("benefit_type")
    assert type(benefit_type) is str, "benefit_info.benefit_type 参数缺失或格式错误"
    benefit_id = benefit_info.get("benefit_id")
    try:
        async with app.mgr.atomic() as t:
            benefit_info['crm_id'] = crm_id
            # 基础信息的更新
            if benefit_id:  # 更新
                await app.mgr.get(model, crm_id=crm_id, benefit_id=benefit_id)
                await add_record_from_dict(app.mgr, model, benefit_info, on_conflict=3,
                                           target_keys=['crm_id', 'benefit_id'])
            else:
                benefit_id = await add_record_from_dict(app.mgr, model, benefit_info, on_conflict=0)
            rules_dict = params_dict.get("rules_dict")
            # 基础权益添加规则
            # 旧规则的逻辑删除
            await app.mgr.execute(
                BenefitRuleInfo.update(deleted=True).where(BenefitRuleInfo.benefit_id == benefit_id))
            for rule in rules_dict:
                rule['deleted'] = False
                rule['crm_id'] = crm_id
                rule['benefit_id'] = benefit_id
                rule['benefit_type'] = benefit_type
                benefit_rule_id = rule.get('benefit_rule_id')
                if benefit_rule_id:
                    # 更新
                    logger.info(f"update 规则 benefit_rule_id={benefit_rule_id}")
                    await add_record_from_dict(app.mgr, BenefitRuleInfo, rule, on_conflict=3,
                                               target_keys=['benefit_rule_id'])
                else:
                    # 写入
                    logger.info("新增一条规则")
                    benefit_rule_id = await add_record_from_dict(app.mgr, BenefitRuleInfo, rule, on_conflict=0)
                rule["rule_id"] = benefit_rule_id
                #  写入到关系表中
                son_rules = rule.get("son_rules") or []
                # 系统权益也要写到 map表中
                if not son_rules:
                    base_rule_id = benefit_rule_id
                    base_benefit_id = benefit_id
                    tmp_dict = dict(benefit_id=benefit_id, benefit_rule_id=benefit_rule_id,
                                    base_benefit_id=base_benefit_id,
                                    base_rule_id=base_rule_id, rule_name=rule.get('name'), crm_id=crm_id)
                    await app.mgr.execute(BenefitRulesMap.insert(tmp_dict).on_conflict(update=tmp_dict))
                for item in son_rules:
                    base_rule_id = item.get("base_rule_id")
                    base_benefit_id = item.get("base_benefit_id")
                    tmp_dict = dict(benefit_id=benefit_id, benefit_rule_id=benefit_rule_id, base_benefit_id=base_benefit_id,
                                    base_rule_id=base_rule_id, rule_name=rule.get('name'), crm_id=crm_id)
                    await app.mgr.execute(BenefitRulesMap.insert(tmp_dict).on_conflict(update=tmp_dict))
            # 重新构造
            rules_dict = await build_benefit_rules_cfg(app, crm_id, benefit_id)
        return json(dict(code=RC.OK, msg="保存成功", data=rules_dict))
    except Exception as ex:
        logger.exception(ex)
        await t.rollback()
        return json(dict(code=RC.DATA_EXCEPTION, msg="处理失败"))


@bp.get("/<crm_id>/benefit_tree")
@except_decorator
async def api_member_benefit_tree(request, crm_id):
    app = request.app
    model = MemberBenefit
    # 系统权益
    items = await app.mgr.execute(model.select().where(model.crm_id == crm_id, model.deleted == False))
    result = []
    os_dict = dict(type="system", title="系统权益", rules=[], id=0)
    cust_dict = dict(type="customize", title="自定义权益", rules=[], id=1)
    __index = 1
    for item in items:
        top_dict = dict()

        benefit_id = item.benefit_id
        benefit_type = item.benefit_type
        tmp_dict = model_to_dict(item, only=[model.benefit_type, model.benefit_id, model.title])
        sql = BenefitRulesMap.select(
            BenefitRulesMap.base_benefit_id, BenefitRulesMap.benefit_rule_id, BenefitRuleInfo.name.alias("title"),
            BenefitRulesMap.auto_id.alias('id'), BenefitRulesMap.benefit_id.alias("pid")
        ).join(
            BenefitRuleInfo, JOIN.LEFT_OUTER, on=BenefitRuleInfo.benefit_rule_id == BenefitRulesMap.benefit_rule_id
        ).where(
            BenefitRulesMap.crm_id == crm_id, BenefitRulesMap.benefit_id == benefit_id, BenefitRuleInfo.deleted==False
        )
        rules = await app.mgr.execute(sql.dicts())
        # rules_ = [model_to_dict(i, fields_from_query=sql) for i in rules]
        tmp_dict["rules"] = rules
        tmp_dict['id'] = benefit_id
        if benefit_type == "be_customize":
            tmp_dict['pid'] = 1
            cust_dict['rules'].append(tmp_dict)
        else:
            tmp_dict['pid'] = 0
            os_dict['rules'].append(tmp_dict)

    # 添加唯一index_id
    # os_dict["id"] = __index
    # __index += 1
    # for rule in os_dict.get("rules") or []:
    #     rule["id"] = __index
    #     __index += 1
    #     for son in rule.get("rules", []):
    #         son['pid'] = rule["id"]
    #         son["id"] = __index
    #         __index += 1
    # cust_dict["id"] = __index
    # __index += 1
    # for rule in cust_dict.get("rules") or []:
    #     rule["id"] = __index
    #     __index += 1
    #     for son in rule.get("rules", []):
    #         son['pid'] = rule['id']
    #         son["id"] = __index
    #         __index += 1

    return json(dict(code=RC.OK, msg="OK", data=[os_dict, cust_dict]))


@bp.post("/<crm_id>/benefit_delete")
@except_decorator
async def api_benefit_delete(request, crm_id):
    app = request.app
    params_dict = request.json
    model = MemberBenefit
    benefit_ids = params_dict.get("benefit_ids")
    assert type(benefit_ids) is list, "benefit_ids格式错误或缺失"
    await app.mgr.execute(model.update(deleted=True).where(
        model.crm_id == crm_id, model.benefit_id.in_(benefit_ids),
        model.benefit_type == "be_customize"
    ))
    return json(dict(code=RC.OK, msg="删除操作成功"))


@bp.get("/<crm_id>/province_info")
@except_decorator
async def api_province_list(request, crm_id):
    app = request.app
    result = []
    for province in app.region_data:
        tmp_dict = dict(code=province.get("code"),
                        name=province.get("name"))
        result.append(tmp_dict)

    return json(dict(code=RC.OK, msg="OK", data=result))


@bp.post("/<crm_id>/fetch_member_nos")
@except_decorator
async def fetch_member_nos(request, crm_id):
    """批量获取会员号"""
    app = request.app
    model = WechatUserInfo
    params = request.json or {}
    unionid_li = params.get("unionid_li")
    assert not unionid_li or type(unionid_li) is list, "unionid_li参数格式错误"
    openid_li = params.get("openid_li")
    assert not openid_li or type(openid_li) is list, "openid_li参数格式错误"
    query = [model.unionid, model.member_no, model.openid]
    if unionid_li:
        items = await app.mgr.execute(model.select(*query).where(model.crm_id==crm_id, model.unionid.in_(unionid_li)).dicts())
    elif openid_li:
        items = await app.mgr.execute(model.select(*query).where(model.crm_id==crm_id, model.openid.in_(openid_li)).dicts())
    else:
        items = []
    member_nos = [x.get("member_no") for x in items]
    members = await get_members_by_member_nos(request.app.mgr, crm_id, member_nos=member_nos)
    members_dict = {}
    for x in members:
        members_dict[x.member_no] = x.nickname
    for x in items:
        x["nickname"] = members_dict.get(x.get("member_no", ""), "")

    return json(dict(code=RC.OK, msg="OK", data=items))


@bp.post("/<crm_id>/black_list")
@except_decorator
async def api_member_black_list(request, crm_id):
    """黑名单列表"""
    app = request.app
    params = request.json
    model = BlackMemberInfo
    page_id = int(params.get("page_id") or 1)
    page_size = int(params.get("page_size") or 20)
    mobile = params.get("mobile")
    member_no = params.get("member_no")
    start_time = params.get("start_time")
    end_time = params.get("end_time")

    order_asc = params.get("order_asc", 0)
    where = [model.crm_id == crm_id, model.status != 0]
    if start_time:
        from_update = datetimeFromString(start_time)
        where.append(model.start_time >= from_update)
    if end_time:
        end_time = datetimeFromString(end_time)
        where.append(model.start_time <= end_time)
    if member_no:
        where.append(model.member_no == member_no)
    elif mobile:
        member_info = await get_member_info(app, crm_id, mobile=mobile)
        if not member_info:
            return json(dict(code=RC.OK, msg="OK", data=[]))
        member_no = member_info.member_no
        where.append(model.member_no == member_no)
    query = model.select().where(*where)
    total = await app.mgr.count(query) or 0
    if order_asc:
        query2 = query.order_by(model.auto_id.asc()).paginate(page_id, page_size)
    else:
        query2 = query.order_by(model.auto_id.desc()).paginate(page_id, page_size)
    items = await app.mgr.execute(query2)
    member_nos = [i.member_no for i in items]
    member_infos = await app.mgr.execute(
        MemberInfo.select().where(MemberInfo.crm_id == crm_id, MemberInfo.member_no.in_(member_nos)))
    member_points = await app.mgr.execute(
        PointsSummary.select().where(PointsSummary.crm_id == crm_id, PointsSummary.member_no.in_(member_nos))
    )
    member_map = model_build_key_map(member_infos, key="member_no")
    points_map = model_build_key_map(member_points, key="member_no")
    result = list()
    for one in items:
        item = model_to_dict(one)
        _member_no = item.get("member_no")
        member_info = member_map.get(_member_no)
        if member_info:
            item['avatar'] = member_info.get('avatar')
            item['nickname'] = member_info.get('nickname')
            item['mobile'] = member_info.get('mobile')
            item['register_time'] = member_info.get('create_time')
        points_info = points_map.get(_member_no)
        if points_info:
            item['freeze_points'] = points_info.get("freeze_points")
            item['active_points'] = points_info.get("active_points")
        result.append(item)
    return json(dict(code=RC.OK, msg="OK", data=dict(items=result, total=total)))


@bp.post('/<crm_id>/v2/black_add')
@except_decorator
async def api_member_black_add(request, crm_id):
    app = request.app
    params = request.json
    model = BlackMemberInfo
    member_no = params.get("member_no")
    mobile = params.get("mobile")
    if (not member_no) and (not mobile):
        assert False, "member_no mobile必须填一个"
    member_info = await get_member_info(app, crm_id, member_no=member_no, mobile=mobile, active_flag=True)
    if not member_info:
        return json(dict(code=RC.HANDLER_ERROR, msg="会员号信息不存在"))
    existed = await app.mgr.count(model.select().where(model.member_no == member_info.member_no, model.status > 0))
    if existed:
        return json(dict(code=RC.DATA_EXIST, msg="已经存在黑名单中不用重复添加"))
    desc = params.get("desc")
    assert type(desc) is str, "desc 参数缺失"
    in_obj = dict(crm_id=crm_id, member_no=member_info.member_no, status=1, desc=desc)
    await app.mgr.execute(model.insert(in_obj).on_conflict(update=in_obj))
    return json(dict(code=RC.OK, msg="添加成功"))


@bp.post("/<crm_id>/freeze")
@except_decorator
async def api_freeze(request, crm_id):
    """用户注销-冻结积分、账户"""
    app = request.app
    params = request.json
    model = BlackMemberInfo
    member_no = params.get("member_no")
    status = str(params.get("status"))
    assert status in ('1', '2', '3', '4'), '不支持的操作'
    status = int(status)
    action = '解冻' if status == '1' else '限制活动' if status == '4' else "冻结"
    is_member = await get_member_info(app, crm_id, member_no)
    if not is_member:
        return json(dict(code=RC.DATA_NOT_FOUND, msg="OK", data=None))
    got = 0
    try:
        origin = await app.mgr.execute(model.select(model.status).where(model.crm_id == crm_id,
                                                                        model.member_no == member_no).dicts())
        assert origin, "该用户不在黑名单中"
        origin_status = origin[0].get('status')
        assert origin_status != status, "无效操作"
        # assert (origin_status > 1 and status == 1) or (origin_status == 1 and status > 1) or \
        #        (origin_status == 2 and status == 3), "不支持的操作"
        got = await app.mgr.execute(
            model.update(status=status).where(model.crm_id == crm_id,  model.member_no == member_no,
                                              model.status > 0))
    except AssertionError as ax:
        logger.error(ax)
        return json(dict(code=RC.FORBIDDEN, msg=f"{ax}"))
    except Exception as ex:
        logger.exception(ex)
    return json(dict(code=RC.OK, msg=f"{action}成功")) if got else json(dict(code=RC.HANDLER_ERROR, msg="无变化"))


@bp.post('/<crm_id>/black_remove')
@except_decorator
async def member_black_remove(request, crm_id):
    """会员黑名单移除"""
    # todo 接口待修改
    app = request.app
    params = request.json
    model = BlackMemberInfo
    member_no = params.get("member_no")
    is_member = await get_member_info(app, crm_id, member_no)
    if not is_member:
        return json(dict(code=RC.DATA_NOT_FOUND, msg="OK", data=None))
    try:
        async with app.mgr.atomic() as t:
            # 更改黑名单表的状态
            await app.mgr.execute(model.update(status=0).where(model.member_no == member_no))
            # 主表的状态
            await app.mgr.execute(
                MemberInfo.update(member_status=MemberStatus.NORMAL).where(MemberInfo.member_no == member_no))
            # 更改各个渠道的状态
            for plat in SUPPORT_PLATFORM:
                p_model = get_model_by_platform(plat)
                if p_model:
                    await app.mgr.execute(
                        p_model.update(status=MemberStatus.NORMAL).where(p_model.member_no == member_no))
    except Exception as ex:
        logger.exception(ex)
        await t.rollback()
        return json(dict(code=RC.HANDLER_ERROR, msg="移除黑名单失败"))
    return json(dict(code=RC.OK, msg="移除黑名单成功"))


@bp.post('/<crm_id>/black_cfg_save')
@except_decorator
async def api_black_cfg_save(request, crm_id):
    model = CRMModel
    app = request.app
    params = request.json or {}
    black_cfg = params.get("black_cfg")
    assert type(black_cfg) is dict, "black_cfg参数类型错误"
    await app.mgr.execute(model.update(black_cfg=black_cfg).where(model.crm_id==crm_id))
    return json(dict(code=RC.OK, msg="OK"))


@bp.get('/<crm_id>/black_cfg')
@except_decorator
async def api_black_cfg_get(request, crm_id):
    model = CRMModel
    app = request.app
    crminfo = await app.mgr.get(model.select(model.black_cfg).where(model.crm_id==crm_id).dicts())
    return json(dict(code=RC.OK, msg="OK", data=dict(black_cfg=crminfo.get("black_cfg"))))


@bp.post('/<crm_id>/cancel_remove')
@except_decorator
async def member_cancel_remove(request, crm_id):
    """从会员注销列表中移除"""
    app = request.app
    params = request.json
    model = CancelMemberInfo
    member_no = params.get("member_no")
    is_member = await get_member_info(app, crm_id, member_no)
    if not is_member:
        return json(dict(code=RC.DATA_NOT_FOUND, msg="OK", data=None))
    try:
        async with app.mgr.atomic() as t:
            # 更改注销表的状态
            await app.mgr.execute(model.update(status=0).where(model.member_no == member_no))
            # 主表的状态
            await app.mgr.execute(
                MemberInfo.update(member_status=MemberStatus.NORMAL).where(MemberInfo.member_no == member_no))
            # 更改各个渠道的状态
            for plat in SUPPORT_PLATFORM:
                p_model = get_model_by_platform(plat)
                if p_model:
                    await app.mgr.execute(
                        p_model.update(status=MemberStatus.NORMAL).where(p_model.member_no == member_no))
    except Exception as ex:
        logger.exception(ex)
        await t.rollback()
        return json(dict(code=RC.HANDLER_ERROR, msg="移除注销失败"))
    return json(dict(code=RC.OK, msg="移除注销成功"))


@bp.post('/<crm_id>/cancel_list')
@except_decorator
async def member_cancel_remove(request, crm_id):
    """注销列表"""
    app = request.app
    params = request.json
    model = CancelMemberInfo
    page_id = params.get("page_id") or 1
    page_size = params.get("page_size") or 20
    mobile = params.get("mobile")
    member_no = params.get("member_no")
    start_time = params.get("start_time")
    end_time = params.get("end_time")

    order_asc = params.get("order_asc", 1)
    where = [model.crm_id == crm_id, model.status == 1]
    if start_time:
        from_update = datetimeFromString(start_time)
        where.append(model.cancel_time >= from_update)
    if end_time:
        end_time = datetimeFromString(end_time)
        where.append(model.cancel_time <= end_time)
    if member_no:
        where.append(model.member_no == member_no)
    elif mobile:
        member_info = await get_member_info(app, crm_id, mobile=mobile)
        if not member_info:
            return json(dict(code=RC.OK, msg="OK", data=[]))
        member_no = member_info.member_no
        where.append(model.member_no == member_no)
    query = model.select().where(*where)
    total = await app.mgr.count(query) or 0
    if order_asc:
        query2 = query.order_by(model.cancel_time.asc()).paginate(int(page_id), int(page_size))
    else:
        query2 = query.order_by(model.cancel_time.desc()).paginate(int(page_id), int(page_size))
    items = await app.mgr.execute(query2)
    member_nos = [i.member_no for i in items]
    member_infos = await app.mgr.execute(
        MemberInfo.select().where(MemberInfo.crm_id == crm_id, MemberInfo.member_no.in_(member_nos)))
    member_map = model_build_key_map(member_infos, key="member_no")
    result = list()
    for one in items:
        item = model_to_dict(one)
        _member_no = item.get("member_no")
        member_info = member_map.get(_member_no)
        if member_info:
            item['avatar'] = member_info.get('avatar')
            item['nickname'] = member_info.get('nickname')
            item['mobile'] = member_info.get('mobile')
        result.append(item)
    return json(dict(code=RC.OK, msg="OK", data=dict(items=result, total=total)))
