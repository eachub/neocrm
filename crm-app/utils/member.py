from typing import Optional

from utils.base_util import Utils

CDP_crm_id = "ALL_crm_id"
from biz import member, crm
from peewee_async import Manager
from common.biz.const import RC
from sanic.log import logger
from hashlib import md5
from common.models.member import *


class UserInfo:
    
    @staticmethod
    def format_user_info(platform, base_info, user_info):
        if not platform:
            return RC.OK, dict(
                nickname=base_info.get('nickname'),
                avatar=base_info.get('avatar'),
                gender=base_info.get('gender'),
                mobile=base_info.get('mobile'),
                birthday=base_info.get('birthday'),
                level="lv1"
            )
        else:
            return RC.OK, dict(
                nickname=base_info.get('nickname') or user_info.get('nickname'),
                avatar=base_info.get('avatar') or user_info.get('avatar'),
                gender=base_info.get('gender') or UserInfo.format_plat_gender(user_info.get('gender')),
                mobile=base_info.get('mobile'),
                birthday=base_info.get('birthday'),
                level="lv1",
                platform=platform
            )
    
    @staticmethod
    def check_format_member_info(member_info):
        info_keys = ['nickname', 'avatar', 'province',
              'city', 'birthday', 'gender', 'hobby', 'email', "occupation", "address"]
        info = {}
        for key, value in member_info.items():
            if key not in info_keys:
                continue
            if key != 'gender' and not value:
                continue
            if key == 'birthday':
                if Utils.check_birthday(value):
                    info[key] = value
                else:
                    return RC.PARAMS_INVALID, "生日信息错误"
            if key == 'gender':
                if value in GENDER.GENDER_LI:
                    info[key] = value
                else:
                    return RC.PARAMS_INVALID, "性别信息错误"
            if value:
                info[key] = value
        return RC.OK, info

    @staticmethod
    def extend_member_info(data, crm_id, member_no, ip=None, extra=None):
        extend_list = ["store_id", "inviter", "province", "city", "region", "address", "email",
                       "occupation", "entrance", "hobby"]
        store_id, inviter, address_province, address_city, address_region, address, email, occupation, entrance, hobby = Utils.get_dict_args(
            data, *extend_list)
        info = {
            'crm_id': crm_id,
            'member_no': member_no,
        }
        if ip:
            info.update({'ip': ip})
        if store_id:
            info.update({'store_id': store_id})
        if inviter:
            info.update({'inviter': inviter})
        if address_province:
            info.update({'province': address_province})
        if address_city:
            info.update({'city': address_city})
        if address_region:
            info.update({'region': address_region})
        if address:
            info.update({'address': address})
        if email:
            info.update({'email': email})
        if occupation:
            info.update({'occupation': occupation})
        if entrance:
            info.update({'entrance': entrance})
        if hobby:
            info.update({'hobby': hobby})
        if extra:
            info.update(dict(extra=extra))
        return info

    @staticmethod
    def check_format_platform_meinfo(base_data, platform=None, platform_info={}):
        """格式化platfo 会员信息"""
        tmp_dict = {}
        if platform == "wechat":
            update_field = ['gender', 'birthday', 'card_code', 'nickname', 'country', 'province', 'city', 'avatar']
            for key in update_field:
                b_val = base_data.get(key)
                p_val = platform.get(key)
                val = b_val if b_val !=None else p_val  # 先使用baseinfo 再使用平台info
                if key == 'gender':
                    if val in GENDER.GENDER_SET:
                        tmp_dict[key] = val
                    else:
                        return False, "生日信息错误"
                elif key == 'birthday':
                    if Utils.check_birthday(val):
                        tmp_dict[key] = val
                    else:
                        return RC.PARAMS_INVALID, "生日信息错误"
                if val != None:
                    tmp_dict[key] = val
        elif platform == "alipay":
            pass
        elif platform == "tmall":
            pass
        elif platform == 'douyin':
            pass
        return True, tmp_dict
    
    @staticmethod
    def format_platform_uinfo(platform, user_info):
        logger.info(user_info)
        try:
            if platform == 'wechat':
                return RC.OK, dict(
                    appid=user_info.get('appId'),
                    unionid=user_info.get('unionId'),
                    openid=user_info.get('openId'),
                    nickname=user_info.get("nickName"),
                    gender=user_info.get('gender'),
                    country=user_info.get('country'),
                    province=user_info.get('province'),
                    city=user_info.get('city'),
                    avatar=user_info.get('avatarUrl')
                )
            elif platform == "tmall":
                return RC.OK, dict(
                    nickname=user_detail.get("nickName"),
                    mix_mobile=user_info.get('mix_mobile'),
                    ouid=user_info.get('ouid'),
                    omid=user_detail.get('omid'),
                    country_code=user_detail.get('country'),
                    province=user_detail.get('province'),
                    city=user_detail.get('city'),
                    avatar=user_detail.get('avatar')
                )
                pass
            elif platform == 'alipay':
                user_detail = user_info.get('response')
                return RC.OK, dict(
                    appid=user_info.get('appid'),
                    user_id=user_info.get('user_id'),
                    nickname=user_detail.get("nickName"),
                    gender=user_detail.get('gender'),
                    country_code=user_detail.get('countryCode'),
                    province=user_detail.get('province'),
                    city=user_detail.get('city'),
                    avatar=user_detail.get('avatar')
                )
                pass
            elif platform == 'douyin':
                # watermark = user_info.get("watermark")
                return RC.OK, dict(
                    appid=user_info.get('appid'),
                    openid=user_info.get('openId'),
                    nickname=user_info.get("nickName"),
                    gender=user_info.get('gender'),
                    country=user_info.get('country'),
                    province=user_info.get('province'),
                    city=user_info.get('city'),
                    avatar=user_info.get('avatarUrl'),
                    extra=dict(
                        language=user_info.get("language")
                    )
                )
        except Exception as ex:
            logger.exception(ex)
            return RC.PARAMS_INVALID, "平台信息出现错误"