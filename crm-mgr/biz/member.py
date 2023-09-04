from mtkext.db import pop_matched_dict
from mtkext.dt import getCurrentDatetime

from common.biz.const import *
from common.biz.heads import *
from common.biz.utils import model_build_key_map
from common.models.helper import *
from common.models.member import *
from biz.utils import get_level_dict, get_channle_type_dict
from common.biz.codec import encrypt_item


def get_children_node(child_nodes, ret_name_li):
    for one in child_nodes:
        ret_name_li.append(one.get("name"))
        child_nodes__ = one.get("children")
        if child_nodes__:
            get_children_node(child_nodes__, ret_name_li)


async def _build_tag_list(app, crm_id=None, more=None, tag_id=None):
    args = [TagInfo.tag_id, TagInfo.tag_name, TagInfo.only_folder, TagInfo.parent_id, TagInfo.active, TagInfo.build_in]
    if more: args.extend([TagInfo.renew_mode, TagInfo.define_mode, TagInfo.crm_id,
                          TagInfo.bind_field, TagInfo.desc, TagInfo.activate_at, ])
    ###
    _where_ = [TagInfo.removed == 0]
    if crm_id:
        _where_.append(TagInfo.crm_id == crm_id)
    if tag_id:
        _where_.append(TagInfo.tag_id==tag_id)
    q = TagInfo.select(*args).where(*_where_) \
        .order_by(TagInfo.build_in.desc(), TagInfo.parent_id.asc(), TagInfo.seqid.asc())
    items = await app.mgr.execute(q)
    ###
    _where_ = [TagLevel.removed == 0]
    if crm_id:
        _where_.append(TagLevel.crm_id == crm_id)
    if tag_id:
        _where_.append(TagLevel.tag_id == tag_id)
    levels = await app.mgr.execute(TagLevel.select(
        TagLevel.tag_id, TagLevel.level_id, TagLevel.level_name,
    ).where(*_where_).order_by(TagLevel.tag_id.asc(), TagLevel.seqid.asc()))
    ###
    level_dict = defaultdict(list)
    for i in levels:
        level_dict[i.tag_id].append(dict(level_id=i.level_id, level_name=i.level_name))
    ###
    tags = []
    for t in items:
        tag = model_to_dict(t, fields_from_query=q)
        if not t.only_folder:
            tag["levels"] = level_dict.get(t.tag_id) or []
        tags.append(tag)
    return tags


async def build_tag_tree(app, crm_id):
    tags = await _build_tag_list(app, crm_id, more=False)
    tag_dict, tag_tree = {}, defaultdict(list)
    for t in tags:
        tag_dict[t["tag_id"]] = t
        tag_tree[t["parent_id"]].append(t)
    for parent_id, items in tag_tree.items():
        parent = tag_dict.get(parent_id)
        if not parent: continue
        parent["children"] = items
    return tag_tree.pop(0, [])


def _fill_dataset_detail(ds, dataset_dict):
    for data in (ds["data"] or []):
        t = dataset_dict.get(data["dataset_id"])
        if not t:
            logger.warning(f'无法匹配到：dataset_id={data["dataset_id"]}')
        else:
            data.update(name=t.name, platform=t.platform, title=t.title,
                        main_id_type=t.main_id_type, dataset_key=t.dataset_key)


def tag_fix_dataset(tag, dataset_dict):
    logger.info(tag)
    if tag["define_mode"] == 1:  # 分区
        for level in tag["desc"]:
            for j in level["rules"]:
                for expr in j["expr_list"]:
                    _fill_dataset_detail(expr["dataset"], dataset_dict)
    elif tag["define_mode"] in (2, 3):  # 单指标
        obj = tag["desc"][0]
        _fill_dataset_detail(obj["dataset"], dataset_dict)
    return tag


async def get_tag_detail(app, crm_id, tag_id):
    q1 = TagInfo.select(
        TagInfo.tag_id, TagInfo.tag_name, TagInfo.only_folder,
        TagInfo.parent_id, TagInfo.renew_mode, TagInfo.define_mode,
        TagInfo.active, TagInfo.activate_at,
        TagInfo.bind_field, TagInfo.desc, TagInfo.qty,
        TagInfo.create_time, TagInfo.update_time,
    ).where(
        TagInfo.tag_id == tag_id,
        TagInfo.crm_id == crm_id,
    )
    items = await app.mgr.execute(q1)
    if not items: return {}
    ###
    t = items[0]
    if t.only_folder:
        return dict(tag_id=t.tag_id, tag_name=t.tag_name, parent_id=t.parent_id, only_folder=True)
    define_mode = t.define_mode
    ###
    # dataset_dict = await build_dataset_dict(app, crm_id)
    # if not dataset_dict: return {}
    tag = model_to_dict(t, fields_from_query=q1)
    ###
    q2 = TagLevel.select(
        TagLevel.level_id, TagLevel.level_name, TagLevel.qty, TagLevel.rules
    ).where(
        TagLevel.tag_id == tag_id,
        TagLevel.crm_id == crm_id,
        TagLevel.removed == 0,
    ).order_by(TagLevel.seqid.asc())
    levels = await app.mgr.execute(q2)
    levels = [model_to_dict(i, fields_from_query=q2) for i in levels]
    # 使用 rule里面的text替换level_name
    for i in levels:
        # mode=2 的单指标的 text描述 更新为level_name 因为卡劵要展示名称和卡劵id，原level_name存储的是card_id
        if define_mode in (2, 4):
            rules = i.pop("rules", [])
            if rules:
                text = rules[0].get("text")
                if text:
                    i['level_name'] = text
    tag["levels"] = levels
    return tag


def level_check_rule(rule):
    assert rule["op"] in ("and", "or"), "rule上的操作符必须是and/or"
    assert type(rule["expr_list"]) is list, "rule上的expr_list必须是数组"
    for t in rule["expr_list"]:
        op, ds, expr = t["op"], t["dataset"], t["expr"]
        assert op in ("and", "or"), "expr_list上的操作符必须是and/or"
        dataset_check_data(ds)
        assert type(expr) is list and expr, "expr必须是数组"
        if ds["data_type"] == "attr":
            assert ds["combo_mode"] in ("any", "all"), "dataset属性数据combo_mode支持any/all"
            expr_check_for_attr(expr)
        elif ds["data_type"] == "action":
            assert ds["combo_mode"] in ("sum", "any", "not"), "dataset行为数据combo_mode支持sum,any/not"
            expr_check_for_action(expr)
        else:
            raise AssertionError("错误的dataset数据类型，data_type=attr/action")


def expr_check_for_attr(expr):
    for t in expr:
        assert t["text"] and t["name"] and t["value"], "attr表达式字段缺失"
        assert t["op"] in ("gt","lt","eq","ge","le","ne","in","notin","startswith","endswith","contains"), "attr非法运算符"


def date_range_check(dr):
    assert type(dr) is list, "dr必须是数组"
    if len(dr) == 1:
        assert dr[0] in (1,7,15,30,60,90,180,360,540), "dr时间值必须是有效整数"
    elif len(dr) == 2:
        assert 20180101 < dr[0] < dr[1] < 20991231, "dr时间范围取值不对"
    else:
        raise AssertionError("dr必须是长度为1或2的数组")


def expr_check_for_action(expr):
    for t in expr:
        date_range_check(t["dr"])
        assert t["name"], "action表达式name字段缺失"
        assert type(t.get("param")) in (None, list), "action表达式param字段不正确"
        assert t["op"] in ("and", "or"), "expr上的操作符必须是and/or"
        assert type(t["aggr"]) is list, "aggr必须是数组"
        for a in t["aggr"]:
            assert a["name"] and a["value"], "agg表达式字段缺失"
            assert a["op"] in ("gt","lt","eq","ge","le","ne"), "aggr非法运算符号"


def dataset_check_data(ds):
    assert type(ds) is dict, "dataset必须是对象"
    if ds.get("data") not in (None, [], ["*"], ["all"]):
        assert type(ds["data"]) is list, "dataset['data']必须是数组"
        for data in ds["data"]:
            assert type(data["dataset_id"]) is str, "错误的dataset_id"


def single_check_mapping(t):
    ds = t["dataset"]
    dataset_check_data(ds)
    assert ds["data_type"] == "attr", "错误的dataset数据类型，单指标映射仅支持attr"
    assert ds["combo_mode"] in ("any", "all"), "dataset属性数据combo_mode支持any/all"
    assert t["text"] and t["name"], "单指标映射缺失attr字段"


async def get_tag_brief(app, crm_id, tag_id):
    q = TagInfo.select(
            TagInfo.crm_id, TagInfo.tag_id, TagInfo.tag_name, TagInfo.only_folder,
            TagInfo.parent_id, TagInfo.renew_mode, TagInfo.define_mode, TagInfo.desc,
            TagInfo.bind_field
        ).where(
            TagInfo.tag_id == tag_id,
            TagInfo.crm_id == crm_id,
        )
    items = await app.mgr.execute(q)
    if not items: return {}
    t = items[0]
    if not t.only_folder: return model_to_dict(t, fields_from_query=q)
    return dict(tag_id=t.tag_id, tag_name=t.tag_name, parent_id=t.parent_id, only_folder=True)


def make_rule_by_span(desc, span):
    if desc["dataset"]["data_type"] == "attr":
        return dict(span, name=desc["name"], text=desc["text"])
    elif desc["dataset"]["data_type"] == "action":
        return dict(span, name=desc["aggr_name"], text=desc["name"], dr=desc["dr"])
    else:
        return span


async def tag_rebuild(app, crm_id, tag_id=None):
    # dataset_dict = await build_dataset_dict(app, crm_id)
    # if not dataset_dict: return []
    ###
    tags = await _build_tag_list(app, crm_id, more=True, tag_id=tag_id)
    logger.info(tags)
    results = []
    for t in tags:
        if t.pop("only_folder", 0): continue
        if not t.pop("active", 0): continue
        # if t.get("define_mode") == 11: continue # 去掉企业微信标签，会导致无法转换bind field
        new_tag = tag_fix_dataset(t, {})
        results.append(new_tag)
        this_tag_id = t.get('tag_id')
        logger.info(f'tag rebuild: {t.get("tag_id")}')
        # 更新到t_tag_info里面
        # await app.mgr.execute(TagInfo.update(desc=new_tag['desc']).where(TagInfo.tag_id==this_tag_id, TagInfo.crm_id==crm_id))
    # bstr = json_dumps(results)
    # ver = hashlib.sha1(bstr.encode()).hexdigest()
    # k0 = f"{crm_id}:tags:version"
    # k1 = f"{crm_id}:tags:content"
    # got = await app.redis.mset(k0, ver, k1, bstr)
    # logger.info(f"{crm_id}: {bstr} {got}")
    return results


async def tag_translate(app, instance_id, tag_level_list):
    tag_dict = await get_tag_dict(app, instance_id)
    level_dict = await get_level_dict(app, instance_id)
    tag_parent = await get_tag_dict(app, instance_id, key="parent_id")
    results = []
    for tag_id, level_id_list in tag_level_list:
        tag_id = int(tag_id)
        levels = [dict(level_id=i, level_name=level_dict.get(i)) for i in level_id_list]
        results.append(dict(tag_id=tag_id, tag_name=tag_dict.get(tag_id),
            category=tag_dict.get(tag_parent.get(tag_id)), levels=levels))
    return results


async def fetch_member_extra_info(mgr, crm_id, model, member_no_li, list_flag=False):
    """获取会员附属信息 返回 {'member_no':item}"""
    # model = MemberExtendInfo
    if not member_no_li:
        return {}
    where = [model.member_no.in_(member_no_li)]
    if crm_id != "common":
        where.append(model.crm_id == crm_id)
    items = await mgr.execute(model.select().where(*where))
    if list_flag:
        order_dict = defaultdict(list)
        for i in items:
            order_dict[i.member_no].append(i)
        return order_dict
    return {i.member_no: i for i in items}


async def get_members_by_member_nos(mgr, crm_id, member_nos, member_status=MemberStatus.NORMAL):
    _where = [MemberInfo.crm_id == crm_id, MemberInfo.member_no.in_(member_nos)]
    if member_status:
        _where.append(MemberInfo.member_status == member_status)
    _query = MemberInfo.select().where(*_where)
    return await mgr.execute(_query)


async def handle_member_add_black(app, crm_id, member_nos, block_time, params_dict):
    try:
        async with app.mgr.atomic() as t:
            # 添加到黑名单表
            start_time = getCurrentDatetime()
            end_time = start_time + timedelta(days=block_time) if block_time else None
            desc = params_dict.get("desc")
            many_data = []
            for member_no in member_nos:
                cancel_data = dict(crm_id=crm_id,
                                   member_no=member_no, block_time=block_time,
                                   desc=desc,
                                   start_time=start_time, end_time=end_time, status=1)
                many_data.append(cancel_data)

            await app.mgr.execute(BlackMemberInfo.insert_many(many_data).on_conflict(update={
                BlackMemberInfo.block_time: block_time,
                BlackMemberInfo.start_time: start_time,
                BlackMemberInfo.end_time: end_time,
                BlackMemberInfo.status: 1,
                BlackMemberInfo.desc: desc
            }))
            await app.mgr.execute(MemberInfo.update(member_status=MemberStatus.BLACK).where(
                MemberInfo.member_no.in_(member_nos), MemberInfo.member_status._in(MemberStatus.ACTIVE)
            ))
            # TODO 其他渠道信息更新？
        return dict(code=RC.OK, msg="会员加入黑名单成功")
    except Exception as ex:
        await t.rollback()
        logger.exception(ex)
        return dict(code=RC.DATA_EXCEPTION, msg=str(ex))


async def build_benefit_rules_cfg(app, crm_id, benefit_id):
    """构造权益下的配置信息"""
    benefit_rules = await fetch_benefit_rules(app.mgr, crm_id)
    excludes = [BenefitRuleInfo.crm_id, BenefitRuleInfo.create_time, BenefitRuleInfo.update_time,
                                                BenefitRuleInfo.deleted]
    benefit_rules_map = model_build_key_map(benefit_rules, "benefit_rule_id", excludes=excludes)
    # 所有的rule
    items = await app.mgr.execute(BenefitRuleInfo.select().where(BenefitRuleInfo.benefit_id == benefit_id, BenefitRuleInfo.deleted==False))
    result = []
    for rule in items:
        tmp_dict = model_to_dict(rule, exclude=excludes)
        son_rules = tmp_dict.get("son_rules")
        son_rule_list = []
        if son_rules:
            for dict_ in son_rules:
                base_rule_id = dict_.get("base_rule_id")
                son_rule = benefit_rules_map.get(base_rule_id)
                son_rule_list.append(son_rule)
        tmp_dict['son_rule_list'] = son_rule_list
        result.append(tmp_dict)
    return result
    benefit_dict = defaultdict(list)
    for item in items:
        base_benefit_id = item.base_benefit_id
        benefit_rule_id = item.benefit_rule_id
        rules_dict = benefit_rules_map.get(benefit_rule_id) or {}
        benefit_dict[base_benefit_id].append(rules_dict)
    return benefit_dict


async def gen_channle_code(app, crm_id, channel_types_li, channel_id):
    "R + 层级1(2) 层级2(2) 层级3(2) 4位channel_id"
    channel_type_mp = await get_channle_type_dict(app, crm_id)
    channel_code = "R"
    channel_types_li + [None] * (3-len(channel_types_li))
    for type_id in channel_types_li:
        if type_id:
            type_no = channel_type_mp.get(type_id, {}).get("type_no")
            if type_no:
                channel_code += str(type_no)
                continue
        channel_code += "00"
    channel_id = str(channel_id).rjust(4, "0")
    channel_code += channel_id[-4:]
    return channel_code


async def get_member_info(app, crm_id, member_no=None, mobile=None, active_flag=False):
    """获取单个用户信息"""
    mgr = app.mgr
    try:
        if (not member_no) and (not mobile):
            raise Exception("fetch_member_info member_no mobile必须填一个")
        model = MemberInfo
        where = [model.crm_id == crm_id]
        if mobile:
            enc_mobile = encrypt_item(app.cipher, mobile)
            where.append(model.enc_mobile == enc_mobile)
        if member_no:
            where.append(model.member_no == member_no)
        if active_flag:
            where.append(model.member_status.in_(MemberStatus.ACTIVE))
        sql = model.select().where(*where)
        logger.info(sql.sql())
        one_obj = await mgr.get(sql)
        return one_obj
    except Exception as ex:
        logger.exception(ex)
        return None


async def get_member_no_list(app, crm_id, mobile, active_flag=False):
    """根据手机号列表获取会员号列表"""
    mgr = app.mgr
    try:
        if not mobile:
            raise Exception("fetch_member_info member_no mobile必须填一个")
        model = MemberInfo
        where = [model.crm_id == crm_id]
        if active_flag:
            where.append(model.member_status.in_(MemberStatus.ACTIVE))
        if mobile:
            enc_mobile = [encrypt_item(app.cipher, i) for i in mobile]
            where.append(model.enc_mobile.in_(enc_mobile))
        sql = model.select(model.member_no).where(*where)
        logger.info(sql.sql())
        data = await mgr.execute(sql)
        return [i.member_no for i in data]
    except Exception as ex:
        logger.exception(ex)
        return []