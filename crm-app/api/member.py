#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import os
from uuid import uuid4

import aiofiles
from mtkext.regex import is_mobile
from mtkext.utils import fetch_image_info

from biz.points import *
from common.biz.const import RC
from biz.member import *
from datetime import datetime
from common.models.helper import *
from utils.base_util import Utils
from utils.ip2region import isip
from biz.const import SUPPORT_PLATFORM, GeoOriginFrom
from common.models.member import GENDER
from biz import crm
from common.biz.wrapper import safe_crm_instance, except_decorator

bp = Blueprint('member', url_prefix="/member")


@bp.post('/<crm_id>/register')
@safe_crm_instance
async def api_member_register(request, crm_id):
    """
    普通用户注册"""
    try:
        assert crm_id, "实例id缺失"
        params_dict = request.json
        app = request.app
        # 参数校验
        # 实例是否存在
        logger.info(f"member_register {params_dict}")
        instance = await crm.get_instance_by_crm_id(app.mgr, crm_id)
        if instance is None:
            return json(dict(code=RC.DATA_NOT_FOUND, msg="实例不存在"))

        params = ["mobile", "source", "birthday",
                  "geo_origin_from", "platform", "user_info"]
        mobile, source, birthday, geo_origin_from, platform, user_info = Utils.get_dict_args(
            params_dict, *params)
        assert mobile and is_mobile(mobile), "手机号格式错误"
        assert not platform or platform in SUPPORT_PLATFORM, "平台信息错误"
        # 渠道来源信息
        assert type(source) is dict, "渠道信息错误"
        channel_code, ip = Utils.get_dict_args(source, "channel_code", "ip")
        assert channel_code, "渠道code参数缺失"
        source.update(dict(channel_code=channel_code.strip()))
        assert (not ip) or isip(ip), "IP信息不合法"
        # 用户信息
        assert type(user_info) is dict, "传入合法的user_info"
        # 30天内注销的不能再注销
        cancle_info = await can_register(app.mgr, crm_id, mobile)
        assert not cancle_info, "手机号注销后30天后进行注册"
        # 判断会员是否存在
        member_info = await MemberBiz.fetch_member_info(app.mgr, crm_id, mobile=mobile)
        assert not member_info, "手机号已被注册"

        ### 格式化平台会员信息
        code, user_info = UserInfo.format_platform_uinfo(platform, user_info)
        assert code == RC.OK, user_info
        # 判断平台会员是否注册
        if platform:
            platform_member = await MemberBiz.get_user_info_platform(
                app.mgr, crm_id, platform, user_info)
            logger.info(platform_member)
            if platform_member and platform_member.status != UserInfoStatus.CANCEL:
                member_no = platform_member.member_no
                return json(dict(code=RC.OK, msg="该用户platform已经被注册", data=dict(member_no=member_no)))

        # 计算用户地址
        if not GeoOriginFrom.contains_platform(geo_origin_from):
            geo_origin_from = GeoOriginFrom.FROM_MOBILE
        if geo_origin_from == GeoOriginFrom.FROM_FILL_IN:  # 地理信息为填写时省份城市不能为空
            province, city = Utils.get_dict_args(
                params_dict, "province", 'city')
            country, province, city = app.geo_filter.geo_format(
                "", province, city)
            assert province and city, "省份城市信息缺失"
        elif geo_origin_from == GeoOriginFrom.FROM_MOBILE:
            province, city = fetch_geo_from_mobile(app, mobile)
            assert province and city, "从手机号获取省份城市失败"
        elif geo_origin_from == GeoOriginFrom.FROM_IP:
            province, city = fetch_geo_from_ip(app, ip)
            logger.info(f"fetch_geo_from_ip province={province} city={city}")
            # assert province and city, "从IP获取省份城市失败"
        else:
            assert user_info, "平台信息缺失"
            province, city = Utils.get_dict_args(user_info, "province", 'city')
            country, province, city = app.geo_filter.geo_format(
                "", province, city)
        params_dict.update(dict(province=province, city=city))
        # TODO 其他渠道加密手机号注册 手机号加密注册
        # 1.判断手机号是否被注册过
        # 判断平台是否有注册过 解绑的平台无member_no
        # 2. 会员信息member_info 来源信息 source_info 平台信息 user_info 记录
        # 如果是密文手机号 解密; member_info 里面存在的各个渠道会员汇总信息
        resp = await handle_register(app, crm_id, params_dict, user_info, platform)
        return json(resp)
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg=f"处理错误{e}", data=None))


@bp.post('/<crm_id>/update')
@safe_crm_instance
async def api_member_update(request, crm_id):
    """
    更新会员信息
    :param member_no: 会员号
    :param member_info: 会员信息
    """
    # 要更新的字段分组
    try:
        params_dict = request.json
        app = request.app
        # 参数校验
        assert crm_id, "实例id缺失"
        member_no = Utils.get_dict_args(params_dict, "member_no")
        assert member_no, "会员号缺失"
        # 校验会员号
        member_obj = await MemberBiz.fetch_member_info(app.mgr, crm_id, member_no)
        assert member_obj, "未找到用户信息"
        platform = params_dict.get("platform")
        assert not platform or platform in SUPPORT_PLATFORM, "传入合法的platform参数"

        # 规范 member_udata
        status, member_data = UserInfo.check_format_member_info(params_dict)
        assert status == RC.OK, member_data
        resp = await handle_member_update(app, crm_id, member_no, platform, member_data, params_dict)
        return json(resp)
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post("/<crm_id>/bind_query")
@safe_crm_instance
async def api_member_bind_query(request, crm_id):
    """绑定查询
    存在：
        该平台没有：
            主表有:
                可绑定
            主表没有:
                可注册
        该平台存在：
            不可绑定 不可注册
        返回平台用户信息
        返回结果 可绑定 可注册 已经注册存在
    """
    try:
        # 参数 'unionid', 'mixmobile', 'mobile' platform_info: {}
        app = request.app
        params_dict = request.json
        platform, member_no, mobile = Utils.get_dict_args(
            params_dict, 'platform', 'member_no', 'mobile')
        assert platform in SUPPORT_PLATFORM, "不支持的平台"
        assert type(mobile) is str, "传入mobile参数"
        platform_info = params_dict.get("platform_info") or {}
        assert type(platform_info) is dict, "传入合法的platform_info参数"

        # 平台
        if platform:
            # 用这个平台相关的参数查询
            plat_user = await MemberBiz.get_platform_member_info(app.mgr, crm_id, platform, platform_info=platform_info)
            if plat_user:
                return json(
                    dict(code=RC.OK, msg="用户已存在该平台", data=dict(regist_able=False, bind_able=False, member_info=None)))
        # 查看主用户表是否存在
        member_obj = await MemberBiz.get_member_info(app.mgr, crm_id, mobile=mobile, active_flag=True)
        # 不存在可注册
        if not member_obj:
            return json(dict(code=RC.OK, msg="用户可以注册", data=dict(regist_able=True, member_info=None)))
        else:
            member_no = member_obj.member_no
            if platform:
                # 用member_no查询该平台
                plat_user = await MemberBiz.get_platform_member_info(app.mgr, crm_id, platform, member_no=member_no)
                if plat_user:
                    return json(dict(code=RC.OK, msg="用户已存在该平台",
                                     data=dict(regist_able=False, bind_able=False, member_info=None)))
            exclude = [MemberInfo.info_id, MemberInfo.crm_id, MemberInfo.update_time, MemberInfo.mobile,
                       MemberInfo.avatar, MemberInfo.member_status]
            result = model_to_dict(member_obj, exclude=exclude)
            return json(dict(code=RC.OK, msg="用户可以绑定", data=dict(bind_able=True, member_info=result)))
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post("/<crm_id>/member_query")
@safe_crm_instance
@except_decorator
async def api_member_info_query(request, crm_id):
    """查询单个会员信息
    优先 mobile member_no 
    用会员或手机号参数:
        查看主会员数据 扩展数据 来源数据 各个渠道表数据
    platform和平台参数
        查看去个渠道表 主会员数据 扩展数据 来源数据
    """
    app = request.app
    params_dict = request.json
    logger.info(f"member_query json:{params_dict}")
    member_no, mobile = Utils.get_dict_args(params_dict, 'member_no', 'mobile')
    t_extend = params_dict.get("t_extend") or False
    assert type(t_extend) is bool, "t_extend类型错误或缺失"
    t_platform = params_dict.get("t_platform") or False
    assert type(t_platform) is bool, "t_platform 类型错误或缺失"
    t_source = params_dict.get("t_source") or False
    assert type(t_source) is bool, "t_source 类型错误或缺失"

    t_family = params_dict.get("t_family") or False
    assert type(t_family) is bool, "t_family 类型错误或缺失"
    member = None
    invite_code = params_dict.get("invite_code")
    if mobile or member_no or invite_code:
        if mobile:
            enc_mobile = encrypt_item(app.cipher, mobile)
            member = await MemberBiz.get_member_info(app.mgr, crm_id, mobile=enc_mobile, active_flag=True)
        elif member_no:
            member = await MemberBiz.get_member_info(app.mgr, crm_id, member_no=member_no, active_flag=True)
        elif invite_code:
            member = await app.mgr.execute(MemberInfo.select().where(MemberInfo.invite_code==invite_code))
            if len(member):
                member = member[0]
        if not member:
            return json(dict(code=RC.DATA_NOT_FOUND, msg="没找到会员数据"))
        member_no = member.member_no
        platform = params_dict.get('platform')
        result = await MemberBiz.get_member_detail(app, crm_id, member_no, params_dict, t_extend=t_extend, t_platform=t_platform,
                                                   t_source=t_source, platform=platform, t_family=t_family)
        return json(dict(code=RC.OK, msg="OK", data=result))
    else:
        platform = params_dict.get("platform", "wechat")
        assert not platform or platform in SUPPORT_PLATFORM, "不支持的平台"
        plt_user = await MemberBiz.get_platform_member_info(app.mgr, crm_id, platform, platform_info=params_dict)
        if not plt_user:
            return json(dict(code=RC.HANDLER_ERROR, msg="平台中没找到会员信息"))
        member_no = plt_user.member_no

        result = await MemberBiz.get_member_detail(app, crm_id, member_no, params_dict, t_extend=t_extend, t_platform=t_platform,
                                                   t_source=t_source, platform=platform, t_family=t_family)
        return json(dict(code=RC.OK, msg="OK", data=result))


@bp.post("/<crm_id>/member_bind")
@safe_crm_instance
async def api_member_bind(request, crm_id):
    """渠道会员绑定
    """
    try:
        app = request.app
        params_dict = request.json
        platform = params_dict.get("platform")
        user_info = params_dict.get("user_info")
        assert platform in SUPPORT_PLATFORM, "不支持的平台"
        member_no = params_dict.get("member_no")
        assert type(member_no) is str, "member_no参数缺失或格式错误"
        member_obj = await MemberBiz.get_member_info(app.mgr, crm_id, member_no)
        if not member_obj:
            return json(dict(code=RC.PARAMS_INVALID, msg="未找到会员信息,无法绑定"))
        assert type(user_info) is dict, "user_info参数缺失或格式错误"
        code, user_info = UserInfo.format_platform_uinfo(platform, user_info)
        assert code == RC.OK, user_info
        # 更新平台会员信息
        resp = await handle_member_bind(app, crm_id, member_no, platform, user_info)
        return json(resp)
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post('/<crm_id>/family/add')
@safe_crm_instance
async def api_member_family_add(request, crm_id):
    """家庭组添加"""
    try:
        #
        app = request.app
        params_dict = request.json
        params = ['member_no', 'nickname', 'avatar', 'gender',
                  'birthday', 'relationship', 'occupation']
        member_no, name, avatar, gender, birthday, relationship, occupation = Utils.get_dict_args(
            params_dict, *params)
        assert type(member_no) is str, "传入合法的member_no参数"
        member_obj = await MemberBiz.fetch_member_info(app.mgr, crm_id, member_no)
        assert member_obj, "用户不存在或注销"
        assert type(name) is str, "传入合法的nickname参数"
        # 判断名称判断
        family_member = await MemberBiz.fetch_family_user(app.mgr, crm_id, member_no, name=name)
        if family_member:
            return json(dict(code=RC.PARAMS_INVALID, msg="家庭组会员已存在,更换家庭会员姓名"))
        # 校验生日 性别
        assert not birthday or Utils.check_birthday(birthday), "传入合法的birthday参数"
        assert not gender or (gender in GENDER.GENDER_LI), "传入合法的gender参数"

        resp = await handle_member_family_add(app, crm_id, member_no, params_dict)
        return json(resp)
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post('/<crm_id>/family/update')
@safe_crm_instance
async def api_member_family_update(request, crm_id):
    """家庭组更新"""
    try:
        app = request.app
        params_dict = request.json
        logger.info(f"family_update req={params_dict}")
        model = MemberFamily
        # 参数校验 family_uid
        family_uid = params_dict.pop("family_uid", None)
        assert type(family_uid) is int, "传入合法的family_uid"
        # 查看是否存在
        where = [model.family_uid == family_uid, model.status == 0]
        family_uinfo = await app.mgr.execute(model.select().where(*where))
        if not family_uinfo:
            return json(dict(code=RC.DATA_NOT_FOUND, msg="未查到家庭组数据"))
        # relationship=1 更新会员信息
        relationship = family_uinfo[0].relationship
        if relationship == 1:
            status, member_data = UserInfo.check_format_member_info(params_dict)
            member_no =family_uinfo[0].member_no
            resp = await handle_member_update(app, crm_id, member_no, None, member_data, params_dict)
            logger.info(f'update member_info {resp}')
        # 更新
        update_obj = peewee_normalize_dict(model, params_dict)
        await app.mgr.execute(model.update(update_obj).where(*where))
        return json(dict(code=RC.OK, msg="更新成功"))
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post('/<crm_id>/family/lot_delete')
@safe_crm_instance
async def api_member_family_delete(request, crm_id):
    """家庭组删除，可批量"""
    try:
        app = request.app
        params_dict = request.json
        model = MemberFamily
        family_uid_li = params_dict.get("family_uid_li")
        member_no = params_dict.get("member_no")
        assert type(member_no) is str, "传入合法的member_no"
        assert type(family_uid_li) is list, "传入合法的family_uid_li 参数"
        # 批量删除会员的家庭组
        await app.mgr.execute(model.update(status=1).where(
            model.family_uid.in_(family_uid_li), model.member_no == member_no))
        return json(dict(code=RC.OK, msg="OK"))
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post('/<crm_id>/family/query')
@safe_crm_instance
async def api_member_family_query(request, crm_id):
    """查看家庭组成员详情"""
    try:
        app = request.app
        params_dict = request.json
        model = MemberFamily
        member_no = params_dict.get("member_no")
        family_uid = params_dict.get("family_uid")
        role_ids = params_dict.get("role_ids")
        where = [model.crm_id == crm_id, model.status == 0]
        if member_no:
            where.append(model.member_no == member_no)
        elif family_uid:
            where.append(model.family_uid == family_uid)
        else:
            assert False, "member_no或family_uid必填"
        if role_ids:
            where.append(model.relationship.in_(role_ids))
        items = await app.mgr.execute(model.select().where(*where))
        exclude = [MemberFamily.status, MemberFamily.crm_id]
        result = [model_to_dict(item, exclude=exclude) for item in items]
        return json(dict(code=RC.OK, msg="OK", data=dict(items=result)))
    except (AssertionError, KeyError, TypeError, ValueError) as ex:
        return json(dict(code=RC.PARAMS_INVALID, msg=f"{ex}"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.INTERNAL_ERROR, msg="服务器错误，请稍后再试", data=None))


@bp.post('/<crm_id>/cancel')
@safe_crm_instance
async def api_member_cancel(request, crm_id):
    """会员注销"""
    # 注销 添加到黑名单里面
    # 会员状态更改成注销

    app = request.app
    params_dict = request.json
    member_no = params_dict.get("member_no")
    mobile = params_dict.get("mobile")
    block_time, desc, operator = Utils.get_dict_args(params_dict, "block_time", "desc", "operator")
    assert operator, "操作者缺失"
    block_time = int(block_time) if block_time else 0
    member = await MemberBiz.get_member_info(app.mgr, crm_id, member_no=member_no)
    assert member, "会员不存在无法注销"
    if not mobile:
        mobile = member.mobile
    if member.member_status == MemberStatus.CANCEL:
        return json(dict(code=RC.OK, msg="会员已经注销,不用重复注销"))
    resp = await handle_member_cancel(app, crm_id, member_no, mobile, block_time, params_dict)
    return json(resp)


@bp.get("/<crm_id>/member_tags")
@safe_crm_instance
async def api_get_member_tags(request, crm_id):
    """获取会员的标签"""
    app = request.app
    params_dict = request.args
    member_no = params_dict.get('member_no')
    # 获取会员的标签数据
    tags = []
    now = datetime.now()
    yestaday = now - timedelta(days=1)
    date_str = datetime.strftime(yestaday, "%Y%m%d")
    model = getUsertags(date_str=date_str)
    try:
        one = await app.mgr.execute(
            model.select().where(model.crm_id == crm_id, model.member_no == member_no).dicts())
    except DoesNotExist:
        one = []
    one = list(one)
    if one:
        one = one[0]
        tag_dict = await get_tag_dict(app, crm_id)
        tag_parent = await get_tag_dict(app, crm_id, key="parent_id")
        logger.info(one)
        for filed, value in one.items():
            logger.info(filed)
            if filed.startswith("tag_0"):
                if value:
                    for level_id in value.split(','):
                        # value中保存的是 level_id 列表
                        tag_id, tag = await level_ids_translate(app, crm_id, level_id)
                        if tag_id:
                            tag.update(dict(tag_name=tag_dict.get(tag_id), category=tag_dict.get(tag_parent.get(tag_id))))
                            tags.append(tag)
    return json(dict(code=RC.OK, msg="OK", data=dict(tags=tags)))


@bp.post("/<crm_id>/unbind_mobile")
async def member_rebind_mobile(request, crm_id):
    """会员手机号解绑更换手机号"""
    try:
        json_data = request.json
        json_data = verify_member_unbound_mobile_param(json_data)
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.PARAMS_INVALID, msg=str(e)))
    db = request.app.mgr
    app = request.app
    mobile = json_data.get("mobile")
    origin_mobile = json_data.get("origin_mobile")
    member_no = json_data.get("member_no")
    try:
        member = await MemberBiz.get_member_info(db, crm_id, member_no)
        old_enc_mobile = member.enc_mobile
        old_mobile = decrypt_item(app.cipher, old_enc_mobile)
        assert old_mobile == origin_mobile, "原手机号错误"
        if old_mobile == mobile:
            return json(dict(code=RC.OK, msg="手机号码未发生修改"))
        already_exist = await MemberBiz.get_member_info(db, crm_id, mobile=mobile)
        assert not already_exist, "该手机号已经被注册"
        # todo 待定逻辑
        can_bind = await is_mobile_can_register(db, mobile, crm_id)
        assert can_bind, "该手机号暂时不允许绑定"
        member.mobile = phone_add_mask(app.cipher, mobile)
        new_enc_mobile = encrypt_item(app.cipher, mobile)
        member.enc_mobile = new_enc_mobile

        # link_id的处理
        link_id = await mobile_link_process(app, old_mobile, old_enc_mobile)
        await app.mgr.execute(MobileLinkId.insert(link_id=link_id, enc_mobile=new_enc_mobile))

        await db.update(member)
        return json(dict(code=RC.OK, msg="换绑手机号成功"))
    except DoesNotExist:
        return json(dict(code=RC.DATA_NOT_FOUND, msg="会员不存在"))
    except Exception as e:
        logger.exception(e)
        return json(dict(code=RC.DATA_EXCEPTION, msg=str(e)))


@bp.post("/<crm_id>/batch_basic")
@except_decorator
async def api_batch_query_member_baseinfo(request, crm_id):
    app = request.app
    params_dict = request.json
    model = MemberInfo
    plained = params_dict.get("plained")
    member_nos = params_dict.get("member_nos")
    assert type(member_nos) is list, "member_nos缺失或格式错误"
    items = await app.mgr.execute(model.select().where(model.crm_id==crm_id, model.member_no.in_(member_nos)))
    items = [model_to_dict(item) for item in items]
    if plained:
        # 解析出明文手机号
        for info in items:
            info['mobile'] = decrypt_item(app.cipher, info.get("enc_mobile"))
    return json(dict(code=RC.OK, msg="OK", data=dict(items=items)))


@bp.post("/<crm_id>/members_by_invite_code")
@except_decorator
async def api_members_by_invite_code(request, crm_id):
    """invite_codes批量获取会员号"""
    app = request.app
    model = MemberInfo
    params = request.json or {}
    invite_code_li = params.get("invite_code_li")
    assert not invite_code_li or type(invite_code_li) is list, "invite_code_li参数格式错误"
    query = [model.member_no, model.invite_code]
    if invite_code_li:
        items = await app.mgr.execute(model.select(*query).where(model.crm_id==crm_id,
                                                                 model.invite_code.in_(invite_code_li)).dicts())
    else:
        items = []

    return json(dict(code=RC.OK, msg="OK", data=items))


@bp.post("/<crm_id>/image_convert")
@except_decorator
async def api_image_convert_inner_link(request, crm_id):
    app = request.app
    files = request.files or dict()
    image_file = files.get("image_file")
    form_params = request.form or dict()
    image_url = form_params.get("image_url")
    if (not image_url) and (not image_file):
        assert False, "image_url 或image_file 参数缺失"
    subpath = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(app.conf.MATERIAL_UPLOAD_DIR, subpath)
    if not os.path.isdir(path): os.makedirs(path)
    if image_url:
        # 请求图片链接保存到本地
        body = await app.http.get(image_url,parse_with_json=False, timeout=10)
        if not body:
            return json(dict(RC.HANDLER_ERROR, msg="获取图片链接资源失败"))
        w, h, mode, ext = fetch_image_info(body)
    elif image_file:
        filename, body = image_file.name, image_file.body
        ext = filename.split(".")[-1]
    else:
        return json(dict(code=RC.PARAMS_MISSING, msg="image_url 或image_file 参数缺失"))
    uuid_str = str(uuid4())
    fname = f"{uuid_str}.{ext}"
    base_path = os.path.join("/", subpath, fname)
    logger.debug(base_path)
    async with aiofiles.open(os.path.join("/", path, fname), mode='wb') as fp:
        await fp.write(body)
    IMG_PREFIX = app.conf.IMG_PREFIX
    crm_url = f"{IMG_PREFIX}{base_path}"
    return json(dict(code=RC.OK, msg="OK", data=dict(crm_url=crm_url)))