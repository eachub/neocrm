import ujson
from common.biz.utils import model_build_key_map
from common.models.member import *
from common.models.coupon import *


async def get_member_info(mgr, crm_id, member_no=None, mobile=None, active_flag=True):
    """获取单个用户信息"""
    try:
        if (not member_no) and (not mobile):
            raise Exception("fetch_member_info member_no mobile必须填一个")
        model = MemberInfo
        where = [model.crm_id == crm_id]
        if mobile:
            where.append(model.mobile == mobile)
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


async def calculate_score():
    pass


async def rule_id_benefit_give_member(app, crm_id, member_no, rule):
    logger.info(f"{member_no} 要添加的权益规则 {rule}")
    content = rule.get("content")
    if content:
        # 积分倍率
        ratio_points = content.get("ratio_points")
        if ratio_points:
            pass
        # 优惠券
        coupon_list = content.get("coupon_list")
        if coupon_list:
            # 发送时间
            send_type = content.get("send_type")
            # 立即发放
            if send_type == "now":
                card_info = []
                for coupon in coupon_list:
                    tmp_dict = dict(qty=1, card_id=coupon.get("card_id"), cost_center=None)
                    card_info.append(tmp_dict)
                _key = app.conf.MQ_CRM_ADAPT_TASK
                action_item = dict(
                    action='give_user_coupon',
                    crm_id=crm_id,
                    body=dict(card_info=card_info, member_no=member_no, event_at=datetime.now(),
                              )
                )
                logger.info(f"push give_user_coupon {_key} -- {action_item}")
                await app.redis.lpush(_key, ujson.dumps(action_item, ensure_ascii=False))
            # todo 非立即发放的逻辑
            # 定时发送 写到mysql cronjob表里面  轮训 cronjob 表
            # 写到适配层的队列里面 调用发券接口
            pass
        # 包邮
    pass


async def member_add_benefit(app, crm_id, member_no, target_levinfo):
    """根据等级添加权益"""
    level_benefit = target_levinfo.get("level_benefit")
    if level_benefit:
        rules_items = await app.mgr.execute(BenefitRuleInfo.select().where(BenefitRuleInfo.crm_id==crm_id))
        rules_map = model_build_key_map(rules_items, "benefit_rule_id", excludes=[])

        benefit_rule_li = []
        for benefit in level_benefit:
            benefit_rule_id = benefit.get("benefit_rule_id")
            benefit_rule_li.append(benefit_rule_id)
        # 查询权益下所有的规则
        benefit_rules = await app.mgr.execute(BenefitRuleInfo.select().where(BenefitRuleInfo.benefit_rule_id.in_(benefit_rule_li)).dicts())
        base_rule_ids = []
        for rule in benefit_rules:
            son_rules = rule.get("son_rules")
            if son_rules:
                for son_rule in son_rules:
                    base_rule_id = son_rule.get("base_rule_id")
                    base_rule_ids.append(base_rule_id)
            else:
                base_rule_ids.append(rule.get("benefit_rule_id"))
        logger.info(f"{member_no} 的基础权益规则列表 {base_rule_ids}")
        ###
        # 根据 base_rule_id 增加权益
        for rule_id in list(set(base_rule_ids)):
            this_rule = rules_map.get(rule_id)
            await rule_id_benefit_give_member(app, crm_id, member_no, this_rule)


async def member_add_bonus(app, crm_id, member_no, target_levinfo):
    level_bonus = target_levinfo.get('level_bonus') or {}
    if level_bonus:
        # 积分
        points = level_bonus.get("points")
        if points:
            pass
        # 成长值
        score = level_bonus.get("score")
        if score:
            pass
        # 自制劵
        coupon = level_bonus.get("coupon")
        # todo 目前存的是coupon_id 应该存 card_id
        if coupon:
            coupons = await app.mgr.execute(CouponInfo.select().where(CouponInfo.coupon_id.in_(coupon)).dicts())
            card_info = []
            for i in coupons:
                card_info.append(dict(card_id=i.get("card_id"), qty=1, cost_center=None))
            _key = app.conf.MQ_CRMAPP_TASK
            action_item = dict(
                action='give_user_coupon',
                crm_id=crm_id,
                body=dict(card_info=card_info, member_no=member_no, event_at=datetime.now())
            )
            logger.info(f"push give_user_coupon {_key} -- {action_item}")
            await app.redis.lpush(_key, ujson.dumps(action_item, ensure_ascii=False))
    pass


async def get_old_linkid(app, enc_mobile):
    try:
        exists = await app.mgr.get(MobileLinkId.select().where(MobileLinkId.enc_mobile==enc_mobile))
        link_id = exists.link_id
        return link_id
    except DoesNotExist:
        return None


async def score_change_member(app, crm_id, member_no, change_score):
    """score值更改等级 增加等级权益 增加升级奖励"""
    # 用户当前等级
    member = await get_member_info(app.mgr, crm_id, member_no=member_no)
    old_score = member.score
    old_level = member.level
    enc_mobile = member.enc_mobile
    link_id = await get_old_linkid(app, enc_mobile=enc_mobile)
    # 历史最大等级
    if link_id:
        level_record = await app.mgr.execute(LevelUpRecord.select().where(
            LevelUpRecord.link_id == link_id).order_by(LevelUpRecord.level_no.desc))
    else:
        level_record = await app.mgr.execute(LevelUpRecord.select().where(
            LevelUpRecord.member_no == member_no).order_by(LevelUpRecord.level_no.desc))
    his_max_level = level_record[0].level_no if level_record else 0
    score = old_score + change_score
    # 目标等级
    levels = await app.mgr.execute(MemberLevelInfo.select().where(
        MemberLevelInfo.min_score <= score, MemberLevelInfo.crm_id==crm_id).order_by(MemberLevelInfo.level_no.desc))
    if not levels:
        logger.info(f"not found target level")
        return
    target_level = levels[0].level_no
    if his_max_level >= target_level:
        # 只升级 不给奖励
        await app.mgr.execute(MemberInfo.update(level=target_level, score=score).where(MemberInfo.member_no == member_no))
        return
    if target_level > old_level:
        # 升级 todo 如果跳级的化 目前先给最大等级的权益
        # 升级等级
        await app.mgr.execute(MemberInfo.update(level=target_level, score=score).where(MemberInfo.member_no == member_no))
        target_levinfo = await app.mgr.execute(MemberLevelInfo.select().where(MemberLevelInfo.level_no==target_level,
                                                                              MemberLevelInfo.crm_id==crm_id).dicts())
        target_levinfo = target_levinfo[0]  # member_level_info 数据
        logger.info(f"target_levinfo: {target_levinfo}")
        # 增加权益
        await member_add_benefit(app, crm_id, member_no, target_levinfo)
        # 增加奖励
        await member_add_bonus(app, crm_id, member_no, target_levinfo)

    # 记录等级变更
    in_obj = dict(crm_id=crm_id, member_no=member_no, level_no=target_level, link_id=link_id)
    await app.mgr.execute(LevelUpRecord.insert(in_obj))