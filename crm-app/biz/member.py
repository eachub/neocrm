# from peewee import DoesNotExist
import re
import string
from hashlib import md5

import ujson

from biz import crm
from biz.const import SUPPORT_PLATFORM
from common.biz.codec import encrypt_item, phone_add_mask
from common.biz.heads import *
from common.models.helper import add_record_from_dict, field_model_to_dict
from common.models.member import *
from utils.base_util import Utils
from common.biz.const import RC, GENDER
from mtkext.sn import create_sn18
from mtkext.regex import is_mobile
from utils.member import UserInfo
from mtkext.dt import getCurrentDatetime
from common.biz.codec import decrypt_item


class MemberBiz:
    """get 获取单个信息 返回 None 或者obj"""

    @staticmethod
    async def fetch_member_info(mgr, crm_id, member_no=None, mobile=None, active_flag=True):
        """active_flag: 非注销非拉黑的"""
        try:
            if (not member_no) and (not member_no):
                return logger.error(f"fetch_member_info member_no mobile必须填一个")
            model = MemberInfo
            where = [model.crm_id == crm_id]
            if mobile:
                where.append(model.mobile == mobile)
            if member_no:
                where.append(model.member_no == member_no)
            if active_flag:
                where.append(model.member_status.in_(MemberStatus.ACTIVE))
            items = await mgr.execute(model.select().where(*where))
            return items
        except Exception as ex:
            logger.info(f"not found member")
            return None

    @staticmethod
    async def get_member_info(mgr, crm_id, member_no=None, mobile=None, active_flag=True):
        """获取单个用户信息"""
        try:
            if (not member_no) and (not mobile):
                raise Exception("fetch_member_info member_no mobile必须填一个")
            model = MemberInfo
            where = [model.crm_id == crm_id]
            if mobile:
                where.append(model.enc_mobile == mobile)
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

    @staticmethod
    async def get_platform_member_info(mgr, crm_id, platform, platform_info=None, member_no=None):
        """获取渠道会员信息
        member_no: 主表中查到member_no 看平台信息表里有没有
        """
        model = MemberBiz.get_model_by_platform(platform)
        where = [model.crm_id == crm_id, model.status == UserInfoStatus.NORMAL]

        if member_no:
            where.append(model.member_no == member_no)
        else:
            if platform == 'wechat':
                # 通过 unionid 来查询
                unionid = platform_info.get('unionid')
                appid = platform_info.get('appid')
                openid = platform_info.get('openid')
                if unionid:
                    where.append(model.unionid == unionid)
                elif appid and openid:
                    where.append(model.openid == openid)
                    where.append(model.appid == appid)
            elif platform == "tmall":
                # 通过 ouid 或者 mix_mobile 来查
                ouid = platform_info.get('ouid')
                mix_mobile = platform_info.get('mix_mobile')
                if ouid: where.append(model.ouid == ouid)
                if mix_mobile: where.append(model.mix_mobile == mix_mobile)
            elif platform == "douyin":
                openid = platform_info.get('openid')
                if openid: where.append(model.openid == openid)
            else:
                # 增加新的渠道
                pass
        if len(where) <= 2:
            return None
        try:
            one = await mgr.get(model.select().where(*where))
            return one
        except DoesNotExist:
            return None

    @staticmethod
    async def generate_member_no(app, crm_id):
        crm_info = app.crm_info.get(crm_id) or {}
        member_code_rule = crm_info.get("member_code_rule")
        prefix, suffix = Utils.get_dict_args(member_code_rule, 'prefix', 'suffix')
        main_str = await create_sn18(redis=app.redis)
        member_no = f"{prefix}{main_str}{suffix}"
        member_no = member_no.replace('-', '')
        return member_no

    @staticmethod
    def generate_invite_code():

        def get_random_letter(length):
            c = string.ascii_letters
            d = []
            for i in range(length):
                d.append(random.choice(c))
            return "".join(d)

        timebase = hex(int(time.time() * 1000))[2:]
        rd = get_random_letter(4)
        return f"NE{timebase}{rd}"

    @staticmethod
    async def create_user_extend(mgr, user_extend):
        try:
            await mgr.execute(MemberExtendInfo.insert(**user_extend))
            return RC.OK, "创建用户扩展信息成功"
        except Exception as ex:
            logger.exception(ex)
            return RC.DATA_EXCEPTION, "创建用户扩展信息失败"

    @staticmethod
    async def get_user_info_by_wechat(mgr, crm_id, appid, openid, unionid=None):
        where = [WechatUserInfo.crm_id == crm_id]
        if unionid:
            where.append(WechatUserInfo.unionid == unionid)
        else:
            if not appid or not openid:
                return None
            where.extend([WechatUserInfo.appid == appid, WechatUserInfo.openid == openid, ])
        try:
            one = await mgr.get(WechatUserInfo.select().where(*where))
            return one
        except DoesNotExist:
            return None

    @staticmethod
    async def get_user_info_by_alipay(mgr, crm_id, user_id):
        where = [AlipayUserInfo.crm_id == crm_id, AlipayUserInfo.user_id == user_id]
        try:
            one = await mgr.get(AlipayUserInfo.select().where(*where))
            return one
        except DoesNotExist:
            return None

    @staticmethod
    async def get_user_info_by_douyin(mgr, crm_id, openid):
        where = [DouyinUserInfo.crm_id == crm_id, DouyinUserInfo.openid == openid]
        try:
            one = await mgr.get(DouyinUserInfo.select().where(*where))
            return one
        except DoesNotExist:
            return None

    @staticmethod
    async def get_user_info_platform(mgr, crm_id, platform, user_info):
        """user_info: 格式化后的平台uinfo"""
        if platform == 'wechat':
            unionid = user_info.get('unionid', None)
            openid = user_info.get('openid', None)
            appid = user_info.get('appid')
            return await MemberBiz.get_user_info_by_wechat(mgr, crm_id, appid, openid, unionid=unionid)
        elif platform == 'alipay':
            user_id = user_info.get('user_id', None)
            return await MemberBiz.get_user_info_by_alipay(mgr, crm_id, user_id)
        elif platform == 'douyin':
            openid = user_info.get('openid', None)
            return await MemberBiz.get_user_info_by_douyin(mgr, crm_id, openid)

    @staticmethod
    def get_model_by_platform(platform):
        if platform == 'wechat':
            return WechatUserInfo
        elif platform == 'alipay':
            return AlipayUserInfo
        elif platform == "douyin":
            return DouyinUserInfo
        return None

    @staticmethod
    async def get_user_extend(mgr, crm_id, member_no, select_field=None):
        """获取单个user_extend信息"""
        try:
            tb = MemberExtendInfo
            where = (tb.crm_id == crm_id, tb.member_no == member_no)
            if select_field and isinstance(select_field, tuple):
                field = select_field
                query = tb.select(*field).where(*where).dicts()
            else:
                query = tb.select().where(*where)
            info = await mgr.get(query)
            return info
        except DoesNotExist:
            return None
        except Exception as ex:
            logger.exception(ex)
            return None

    @staticmethod
    async def update_user_extend(mgr, crm_id, member_no, user_extend):
        try:
            got = await mgr.execute(MemberExtendInfo.update(**user_extend).
                                    where(MemberExtendInfo.crm_id == crm_id,
                                          MemberExtendInfo.member_no == member_no))
            logger.info(f"update MemberExtendInfo {member_no} {user_extend} ==> got={got}")
            return RC.OK, "更新用户扩展信息成功"
        except Exception as ex:
            logger.exception(ex)
            return RC.DATA_EXCEPTION, "更新用户扩展信息失败"

    @staticmethod
    async def fetch_family_user(mgr, crm_id, member_no, name=None, active_flag=True):
        try:
            where = [MemberFamily.crm_id == crm_id, MemberFamily.member_no == member_no]
            if active_flag:
                where.append(MemberFamily.status == 0)
            if name:
                where.append(MemberFamily.nickname == name)
            items = await mgr.execute(MemberFamily.select().where(*where))
            return items
        except Exception as ex:
            logger.exception(ex)
            return []

    @staticmethod
    async def get_member_detail(app, crm_id, member_no, params_dict, platform=None, t_extend=False, t_platform=False, t_source=False,
                                t_family=False):
        """根据member_no获取 会员 extend_info 各个平台user_info """
        result_dict = dict()
        mgr = app.mgr

        member_info = await MemberBiz.get_member_info(mgr, crm_id, member_no)
        plained = params_dict.get("plained")
        info = model_to_dict(member_info)
        if plained:
            info['mobile'] = decrypt_item(app.cipher, info.get("enc_mobile"))
        result_dict['info'] = info
        # 扩展信息
        if t_extend:
            try:
                extend_items = await mgr.get(MemberExtendInfo.select().where(MemberExtendInfo.crm_id == crm_id,
                                                                             MemberExtendInfo.member_no == member_no))
                extend_info = field_model_to_dict(extend_items, exclude=['crm_id', "create_time", 'update_time'])
            except DoesNotExist:
                extend_info = {}
            result_dict['extend_info'] = extend_info
        # 渠道信息
        # if t_platform:
        if platform:
            plt_range = [platform]
        else:
            if t_platform:
                plt_range = SUPPORT_PLATFORM
            else:
                plt_range = []
        for platform in plt_range:
            __model = MemberBiz.get_model_by_platform(platform)
            if __model:
                try:
                    plt_items = await mgr.get(__model.select().where(
                        __model.crm_id == crm_id, __model.member_no == member_no,
                        __model.status == MemberStatus.NORMAL))
                    plt_info = field_model_to_dict(plt_items,
                                                   exclude=['auto_id', 'crm_id'])
                except Exception as ex:
                    plt_info = {}
                result_dict[f"{platform}_member_info"] = plt_info
        # 来源信息
        if t_source:
            try:
                source_item = await mgr.get(MemberSourceInfo.select().where(
                    MemberSourceInfo.crm_id == crm_id, MemberSourceInfo.member_no == member_no))
                source_info = field_model_to_dict(source_item,
                                                  exclude=['auto_id', 'crm_id', 'create_time', 'update_time'])
            except DoesNotExist:
                source_info = {}
            result_dict['member_source_info'] = source_info
        # 家庭成员信息
        if t_family:
            family_objs = await mgr.execute(MemberFamily.select().where(
                MemberFamily.crm_id == crm_id, MemberFamily.member_no == member_no, MemberFamily.status == 0).dicts())
            # 映射职业为str
            for f in family_objs:
                relationship = f.get("relationship")
                relation_name = relationship_maping.get(relationship) or "未知"
                f['relation_name'] = relation_name
            result_dict['family'] = family_objs
        return result_dict


async def get_old_linkid(app, enc_mobile):
    try:
        exists = await app.mgr.get(MobileLinkId.select().where(MobileLinkId.enc_mobile==enc_mobile))
        link_id = exists.link_id
        return link_id
    except DoesNotExist:
        return None


async def mobile_link_process(app, mobile, enc_mobile):
    """手机号指向 绑定一个link_id 查询是否存在不写入"""
    link_id = await get_old_linkid(app, enc_mobile)
    if not link_id:
        link_id = md5(mobile.encode("utf-8")).hexdigest().upper()
        in_obj = dict(link_id=link_id, enc_mobile=enc_mobile)
        await app.mgr.execute(MobileLinkId.insert(in_obj))
        logger.info(f"mobile={mobile}, gen new link_id={link_id}")
    return link_id


async def member_register(app, crm_id, member_dict, source_dict):
    member_no = await MemberBiz.generate_member_no(app, crm_id)
    member_dict.update(dict(member_no=member_no))
    info_id = await app.mgr.execute(MemberInfo.insert(crm_id=crm_id, **member_dict))
    invite_code = MemberBiz.generate_invite_code()
    logger.info(f"{member_no}, {invite_code}")
    await app.mgr.execute(MemberInfo.update(invite_code=invite_code).where(
        MemberInfo.info_id == info_id))
    ip = source_dict.pop("ip", None)
    extra = dict(ip=ip)
    if ip:
        province, city = fetch_geo_from_ip(app, ip)
        extend_extra = dict(province=province, city=city)
        extra.update(extend_extra)
    await app.mgr.execute(MemberSourceInfo.insert(crm_id=crm_id,
                                                  extra=extra,
                                                  member_no=member_no, **source_dict))
    return member_no


async def handle_register(app, crm_id, params_dict, user_info, platform=None):
    """处理注册
    user_info: 格式化后的平台uinfo
    """
    mobile = params_dict.get('mobile')
    enc_mobile = encrypt_item(app.cipher, mobile)
    member_dict = dict(
        nickname=params_dict.get('nickname') or user_info.get('nickname'),
        avatar=params_dict.get('avatar') or user_info.get('avatar'),
        gender=params_dict.get('gender') or user_info.get('gender'),
        mobile=phone_add_mask(app.cipher, mobile),
        enc_mobile=enc_mobile,
        birthday=params_dict.get('birthday') or user_info.get("birthday"),
        province=params_dict.get('province') or user_info.get("province"),
        city=params_dict.get('city') or user_info.get("city"),
        level=0,
        platform=platform
    )
    source = params_dict.get("source")
    ip = source.get('ip')
    source.update(dict(platform=platform))
    #
    try:
        async with app.mgr.atomic() as t:
            # 会员主表数据写入
            member_no = await member_register(app, crm_id, member_dict, source)
            # 手机号指向link_id,不存在link_id md5生成
            await mobile_link_process(app, mobile, enc_mobile=enc_mobile)
            # 扩展数据写入
            extend_data = UserInfo.extend_member_info(params_dict, crm_id, member_no, ip)
            await add_record_from_dict(app.mgr, MemberExtendInfo, extend_data, on_conflict=3,
                                       target_keys=['crm_id', "member_no"])
            # 平台信息写入
            if platform:
                model = MemberBiz.get_model_by_platform(platform)
                user_info.update(dict(member_no=member_no, crm_id=crm_id, status=UserInfoStatus.NORMAL))
                logger.info(f"platform={platform} create platform_user={user_info}")
                await app.mgr.execute(model.insert(user_info).on_conflict(update=user_info))
        # 将注册会员推送到redis中，初始化用户积分
        _key = app.conf.MQ_CRM_TASK
        action_item = dict(
            action='user_register',
            crm_id=crm_id,
            body=dict(member_no=member_no, nickname=member_dict.get("nickname"),
                      event_at=datetime.now(), invite_code=None,
                      ),
        )
        logger.info(f"push register {_key} -- {action_item}")
        await app.redis.lpush(_key, ujson.dumps(action_item, ensure_ascii=False))
        return dict(code=RC.OK, msg="注册成功", data=dict(member_no=member_no))
    except Exception as ex:
        logger.exception(ex)
        await t.rollback()
        return dict(code=RC.DATA_EXCEPTION, msg="注册失败")


async def handle_member_update(app, crm_id, member_no, platform, member_data, params_dict):
    mgr = app.mgr
    try:
        member_data.update(dict(crm_id=crm_id, member_no=member_no))
        async with app.mgr.atomic() as t:
            update_obj = peewee_normalize_dict(MemberInfo, member_data)
            got1 = await app.mgr.execute(MemberInfo.update(update_obj).where(MemberInfo.member_no==member_no, MemberInfo.crm_id==crm_id))
            # got1 = await add_record_from_dict(
            #     app.mgr, MemberInfo, member_data, on_conflict=3, excluded=['crm_id', 'member_no'],
            #     target_keys=['crm_id', 'member_no'])
            logger.info(f"update member_no={member_no}, {member_data} MemberInfo.got1{got1}")
            # 更新渠道信息
            if platform:
                status, result = UserInfo.check_format_platform_meinfo(params_dict, platform,
                                                                       params_dict.get('user_info'))
                if not status:
                    await t.rollback()
                    return dict(code=RC.PARAMS_INVALID, msg=result)
            data = await MemberBiz.get_user_extend(mgr, crm_id, member_no)
            if not data:
                return dict(code=RC.PARAMS_INVALID, msg='会员数据查询失败')
            # 更新扩展信息
            extend_data = UserInfo.extend_member_info(params_dict, crm_id, member_no)
            model_dict = peewee_normalize_dict(MemberExtendInfo, extend_data)
            got2 = await mgr.execute(MemberExtendInfo.insert(model_dict).on_conflict(update=model_dict))
            logger.info(f'update extend_info got2 {got2}')
            return dict(code=RC.OK, msg="完善会员信息OK", data=member_no)
    except Exception as ex:
        logger.exception(ex)
        await t.rollback()
        return dict(code=RC.DATA_EXCEPTION, msg=str(ex))


async def handle_member_family_add(app, crm_id, member_no, params_dict):
    try:
        async with app.mgr.atomic() as t:
            # 添加到家庭会员表
            # 删除的更改为更新状态
            params_dict.update(dict(crm_id=crm_id, member_no=member_no, status=0))
            got = await add_record_from_dict(app.mgr, MemberFamily, params_dict, on_conflict=3,
                                             target_keys=['nickname', 'member_no'])
            # 更新会员状态为家庭
            await app.mgr.execute(MemberInfo.update(member_status=MemberStatus.FAMILY).where(
                MemberInfo.crm_id == crm_id, MemberInfo.member_no == member_no,
                MemberInfo.member_status.in_(MemberStatus.ACTIVE)))
            return dict(code=RC.OK, msg="添加成功", data=got)
    except Exception as ex:
        logger.error(ex)
        await t.rollback()
        return dict(code=RC.HANDLER_ERROR, msg="处理失败")


async def handle_member_bind(app, crm_id, member_no, platform, user_info):
    """处理平台会员绑定"""
    try:
        user = await MemberBiz.get_user_info_platform(app.mgr, crm_id, platform, user_info)
        logger.info(user)
        model = MemberBiz.get_model_by_platform(platform)
        if user:
            if user.status == UserInfoStatus.CANCEL:
                user.member_no = member_no
                user.status = UserInfoStatus.NORMAL
            else:
                if user.member_no == member_no:
                    return dict(code=RC.DATA_EXCEPTION, msg="平台信息已被绑定")
            for k, value in user_info.items():
                # add_record_from_dict
                key = getattr(model, k, None)
                if key:
                    setattr(user, key, value)
            logger.info(user.status)
            update_count = await app.mgr.update(user)
            if update_count < 1:
                return dict(code=RC.DATA_NOT_UPDATE, msg="未更新用户平台信息")
        else:
            await app.mgr.execute(model.insert(crm_id=crm_id, member_no=member_no, **user_info))
        return dict(code=RC.OK, msg="用户绑定到平台成功")
    except Exception as ex:
        logger.exception(ex)
        return dict(code=RC.DATA_EXCEPTION, msg=str(ex))


async def update_by_data(db, model, where=None, use_exp=False, **update_data):
    logger.info(f"update_by_data {model} {where} {update_data}")
    ud = model.update(**update_data)
    if use_exp:
        ud = ud.where(where)
    else:
        ud = ud.where(*where)
    logger.info(ud)
    return await db.execute(ud)


async def handle_member_cancel(app, crm_id, member_no, mobile, block_time, params_dict):
    try:
        async with app.mgr.atomic() as t:
            # 添加到黑名单表
            start_time = getCurrentDatetime()
            end_time = start_time + timedelta(days=block_time) if block_time else None
            desc = params_dict.get("desc")
            cancel_data = dict(crm_id=crm_id, member_no=member_no, mobile=mobile, cancel_time=start_time, status=1)
            # 会员注销进入 CancelMemberInfo 表
            await app.mgr.execute(CancelMemberInfo.insert(cancel_data).on_conflict(update=cancel_data))
            logger.info(f"in or update CancelMemberInfo member_no={member_no} {cancel_data}")
            # await app.mgr.execute(BlackMemberInfo.insert(cancel_data).on_conflict(update={
            #     BlackMemberInfo.block_days: block_time,
            #     BlackMemberInfo.start_time: start_time,
            #     BlackMemberInfo.end_time: end_time,
            #     BlackMemberInfo.status: 1,
            #     BlackMemberInfo.register_time: register_time,
            #     BlackMemberInfo.desc: desc
            # }))
            await app.mgr.execute(MemberInfo.update(member_status=MemberStatus.CANCEL).where(
                MemberInfo.member_no == member_no, MemberInfo.member_status != MemberStatus.CANCEL)
            )
            # 所有的家庭组全部逻辑删除
            await app.mgr.execute(MemberFamily.update(status=UserInfoStatus.CANCEL).where(MemberFamily.member_no==member_no))
            # TODO 其他渠道信息更新为 取消
            # 微信平台
            await app.mgr.execute(WechatUserInfo.update(status=UserInfoStatus.CANCEL).where(WechatUserInfo.member_no==member_no))

        return dict(code=RC.OK, msg="注销会员成功")
    except Exception as ex:
        await t.rollback()
        logger.exception(ex)
        return dict(code=RC.DATA_EXCEPTION, msg=str(ex))


async def fetch_member_info_by_no(mgr, crm_id, member_no):
    try:
        one = await mgr.get(MemberInfo, crm_id=crm_id, member_no=member_no)
    except DoesNotExist:
        logger.info(f"not found member")
        one = None
    return one


async def fetch_member_info_by_mobile(mgr, crm_id, mobile):
    try:
        return mgr.get(MemberInfo.select().where(
            MemberInfo.crm_id == crm_id, MemberInfo.mobile == mobile,
            MemberInfo.member_status.in_(MemberStatus.MEMBER_EXIST)
        ))
    except Exception as ex:
        return None


async def can_register(mgr, crm_id, mobile):
    try:
        return await mgr.get(CancelMemberInfo.select().where(
            CancelMemberInfo.crm_id == crm_id, CancelMemberInfo.mobile == mobile, CancelMemberInfo.status == 1
        ))
    except Exception as ex:
        logger.info("not found data")
        return None


def fetch_geo_from_mobile(app, mobile):
    status, region = app.mobile_finder.search(mobile)
    if status != RC.OK:
        return None, None
    return region.split('|')


def fetch_geo_from_ip(app, ip):
    city_id, region = app.ip_finder.search(ip)
    if not region:
        return None, None
    region_list = region.split('|')
    if len(region_list) < 4:
        return None, None
    province, city = region_list[2:4]
    if not province or province == '0' or not city or city == '0':
        return None, None
    province = Utils.format_region(province)
    city = Utils.format_region(city)
    return province, city


async def level_ids_translate(app, crm_id, level_id):
    """根据level_id 返回查找 tag_info 构造数据结构"""
    logger.info(level_id)
    # {"tag_id":20001,"tag_name":"性别", category:"人口属性" "levels":[{"level_id":600003,"level_name":"男"}]}
    levels = await app.mgr.execute(TagLevel.select(TagLevel.tag_id, TagLevel.level_id, TagLevel.level_name).where(
        TagLevel.level_id==level_id).dicts())
    if not levels:
        logger.info(f"not found level_id={level_id} may delete")
        return False, {}
    tag_id = levels[0].get('tag_id')
    return tag_id, dict(tag_id=tag_id, levels=levels)


def verify_member_unbound_mobile_param(update_data: dict):
    assert update_data, "缺失参数"
    mobile = update_data.get("mobile")
    member_no = update_data.get("member_no")
    origin_mobile = update_data.get("origin_mobile")
    if not all([mobile, origin_mobile, member_no]):
        raise ValueError("缺失参数")
    if not is_mobile(mobile) or not is_mobile(origin_mobile):
        raise ValueError("请输入正确的手机号码")
    return {"mobile": mobile, "member_no": member_no, "origin_mobile": origin_mobile}


async def is_mobile_can_register(db, mobile: str, crm_id: str):
    _query = CancelMemberInfo.select(CancelMemberInfo.info_id).where(
        CancelMemberInfo.crm_id == crm_id,
        CancelMemberInfo.mobile == mobile,
        CancelMemberInfo.status == 1
    )
    logger.info(f"手机号是否可以注册:{_query}")
    try:
        await db.get(_query)
    except DoesNotExist:
        return True
    return False
