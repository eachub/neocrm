from collections import defaultdict
from datetime import timedelta

from mtkext.db import sql_printf

from model.tag_model import TagInfo, getUsertags
import logging

logger = logging.getLogger(__name__)

campaign_code_sql = """
select member_no, campaign_code from db_neocrm.t_crm_member_source_info 
where create_time >= {from_time} and create_time < {to_time} and crm_id={crm_id}
and campaign_code={value0}
"""
channel_sql = """
select member_no from db_neocrm.t_crm_member_source_info 
where create_time >= {from_time} and create_time < {to_time} and crm_id={crm_id}
and channel_code={value0}
"""

points_change_sql = """
select (t1.member_no) from (
    select
		member_no, sum(points) as dim 
    from
		db_neocrm.t_crm_points_history
	group by member_no 
) t1 
where t1.dim >= {value0} and if({value1} is null, true, t1.dim < {value1})
"""
# 人口属性
# 性别
gender_sql = """
SELECT * FROM db_neocrm.t_crm_member_info tcmi 
WHERE update_time >= {from_time} and update_time < {to_time} AND  crm_id= {crm_id} 
AND gender={value0}
"""
# 职业
occupation_sql = """
select * from db_neocrm.t_crm_member_extend_info
where update_time >= {from_time} and update_time < {to_time} and crm_id = {crm_id}
and occupation like '%%{value0}%%'
"""

# 年龄
age_sql = """
SELECT * FROM db_neocrm.t_crm_member_info tcmi 
WHERE update_time >= {from_time} and  update_time < {to_time} AND  crm_id= {crm_id} and birthday is not null
AND TIMESTAMPDIFF(YEAR, birthday, CURDATE()) >= {value0} and if({value1} is null, true, TIMESTAMPDIFF(YEAR, birthday, CURDATE()) < {value1}) 
"""
# 生日
birth_month_sql = """
SELECT * FROM db_neocrm.t_crm_member_info tcmi 
WHERE update_time >= {from_time} and  update_time < {to_time} AND  crm_id= {crm_id} 
AND date_format(birthday ,'%%m')={value0}
"""
# 会员等级
member_level_sql = """
SELECT * FROM db_neocrm.t_crm_member_info tcmi 
WHERE update_time >= {from_time} and update_time < {to_time} AND  crm_id= {crm_id} 
AND level={value0}
"""
# 会领区间
vip_age_sql = """SELECT * FROM db_neocrm.t_crm_member_info tcmi WHERE  crm_id= {crm_id} 
AND IF ({value1} is null, true, TIMESTAMPDIFF(DAY, create_time, CURDATE())<{value1}) and TIMESTAMPDIFF(DAY, create_time, CURDATE()) >= {value0}
"""
# 活跃状态
active_sql = """
select * from (
    select unionid, count(1) as count from db_event.t_wmp_app_event
    where create_time > {from_time} and create_time <= {to_time} 
    group by unionid 
) t where t.count>={value0} and IF ({value1} is null, true, t.count<{value1})
"""
# 家庭成员数量
family_nums_sql = """
select
    member_no
from (
    select member_no, count(1) as count from db_neocrm.t_crm_member_family
    where crm_id={crm_id} 
) t1 where t1.count>={value0} and if({value1} is null, true, t1.count<={value1})
"""
# 城市
recent_city_sql = """
select member_no from db_neocrm.t_crm_member_info where crm_id={crm_id} 
and update_time >= {from_time} and  update_time < {to_time}
and city like '%%{value0}%%'
"""
# 省份  wmp_app_event ip地址转换一下
recent_region_sql = """
select * from (
SELECT  unionid, ip as value, max(create_time) as nums FROM db_event.t_wmp_app_event
where create_time > {from_time} and unionid != '' and {extra_conds}
group by unionid, ip
    ) t1 
where (unionid, nums) in ( 
    select 
        unionid,  max(nums) as nums
    from ( 
        SELECT  unionid, ip, max(create_time) as nums FROM db_event.t_wmp_app_event
        where create_time > {from_time} and unionid != '' and {extra_conds}
        group by unionid, ip
    ) t group by unionid
)

"""
# 购买频次
buy_times_sql = """
select 
    member_no
from (
    select member_no, count(1) as count from db_neocrm.t_crm_order_info 
    where update_time >= {from_time} and update_time < {to_time} and crm_id=crm_id
    group by member_no
) t1 where t1.count >= {value0} and if({value1} is null, true, t1.count <= {value1})
"""

# 近期购买支付金额
recent_pay_mounts_sql = """
select 
    member_no
from (
    select member_no, sum(pay_amount) as count from db_neocrm.t_crm_order_info 
    where update_time >= {from_time} and update_time < {to_time} and crm_id=crm_id
    group by member_no
) t1 where t1.count >= {value0} and if({value1} is null, true, t1.count <= {value1})
"""
# 最近一次购买距今天数
recent_buy_days_sql = """
select 
    member_no
from (
    select member_no, datediff(max(create_time), now()) as count from db_neocrm.t_crm_order_info 
    where update_time >= {from_time} and update_time < {to_time} and crm_id=crm_id
) t1 where t1.count >= {value0} and if({value1} is null, true, t1.count <= {value1})
"""
# 最近一次购买商品 无时间范围 一年前到现在的 防止数据太多
last_buy_goods_sql = """
select * from (
	SELECT  member_no, erp_sku_code, max(create_time) as nums FROM db_neocrm.t_crm_order_item 
	where create_time > {from_time} and create_time < {to_time} and crm_id={crm_id}
	group by member_no, erp_sku_code
	) t1 
where (member_no, nums) in ( 
	select 
		member_no,  max(nums) as nums
	from ( 
	    SELECT  member_no, erp_sku_code, max(create_time) as nums FROM db_neocrm.t_crm_order_item  
	    where create_time > {from_time} and create_time < {to_time} and crm_id={crm_id}
	    group by member_no, erp_sku_code
	) t group by member_no
)
"""
# 消费习惯
# 近期最近一次购买商品
recent_buy_goods_sql = """
select * from (
	SELECT  member_no, erp_sku_code as value, max(create_time) as nums FROM db_neocrm.t_crm_order_item 
	where create_time > {from_time} and create_time < {to_time} and crm_id={crm_id}
	group by member_no, erp_sku_code
	) t1 
where (member_no, nums) in ( 
	select 
		member_no,  max(nums) as nums
	from ( 
	    SELECT  member_no, erp_sku_code, max(create_time) as nums FROM db_neocrm.t_crm_order_item  
	    where create_time > {from_time} and create_time < {to_time} and crm_id={crm_id}
	    group by member_no, erp_sku_code
	) t group by member_no
)
"""

# todo 近期最多购买商品 这种计算逻辑要更改
recent_most_buy_goods = """
select * from (
	SELECT  member_no, erp_sku_code, count(erp_sku_code) as nums FROM db_neocrm.t_crm_order_item 
	where create_time > {from_time} and create_time < {to_time} and crm_id={crm_id}
	group by member_no, erp_sku_code
	) t1 
where (member_no, nums) in ( 
	select 
		member_no,  max(nums) as nums
	from ( 
	    SELECT  member_no, erp_sku_code, count(erp_sku_code) as nums FROM db_neocrm.t_crm_order_item  
	    where create_time > {from_time} and create_time < {to_time} and crm_id={crm_id}
	    group by member_no, erp_sku_code
	) t group by member_no  
)
"""

# 近期最近一次购买商品类目 近期最近一次购买商品 商品对应类目
recent_buy_category = """
select * from (
	select 
    	member_no, cat_id as value, max(create_time) as nums
    from (
        SELECT t1.member_no ,t1.goods_id ,t2.cat_id , t1.create_time  from db_neocrm.t_crm_order_item t1 
        left join db_neocrm.t_crm_category_goods t2 on t2.goods_id =t1.goods_id 
        left join db_neocrm.t_crm_category_node t3 on t3.cat_id =t2.cat_id 
        where t1.create_time > {from_time} and t1.create_time < {to_time}
    ) t group by t.member_no, cat_id
) t10 
where (member_no, nums) in ( 
	select 
		member_no,  max(nums) as nums
	from ( 
	    select 
        member_no, cat_id, max(create_time) as nums
        from (
            SELECT t1.member_no ,t1.goods_id ,t2.cat_id , t1.create_time  from db_neocrm.t_crm_order_item t1 
            left join db_neocrm.t_crm_category_goods t2 on t2.goods_id =t1.goods_id 
            left join db_neocrm.t_crm_category_node t3 on t3.cat_id =t2.cat_id 
            where t1.create_time > {from_time} and t1.create_time < {to_time}
        ) t group by t.member_no, cat_id
	) t9 group by member_no 
)
"""
# 近期最多购买商品类目
recent_most_buy_category = """
select * from (
	select 
    	member_no, cat_id as value, count(*) as nums
    from (
        SELECT t1.member_no ,t1.goods_id ,t2.cat_id , t3.name  from db_neocrm.t_crm_order_item t1 
        left join db_neocrm.t_crm_category_goods t2 on t2.goods_id =t1.goods_id 
        left join db_neocrm.t_crm_category_node t3 on t3.cat_id =t2.cat_id 
        where t1.create_time > {from_time} and t1.create_time < {to_time}
    ) t group by t.member_no, cat_id
) t10 
where (member_no, nums) in ( 
	select 
		member_no,  max(nums) as nums
	from ( 
	    select 
        member_no, cat_id, count(*) as nums
        from (
            SELECT t1.member_no ,t1.goods_id ,t2.cat_id , t3.name  from db_neocrm.t_crm_order_item t1 
            left join db_neocrm.t_crm_category_goods t2 on t2.goods_id =t1.goods_id 
            left join db_neocrm.t_crm_category_node t3 on t3.cat_id =t2.cat_id 
            where t1.create_time > {from_time} and t1.create_time < {to_time}
        ) t group by t.member_no, cat_id
	) t9 group by member_no 
)
"""

# 访问活动，从 t_wmp_custom_event
# 近期最近一次访问活动 t_cam_web_traffic_event
recent_in_activity = """
select * from (
	SELECT  member_no, cid as value, max(create_time) as nums FROM db_neocam.t_cam_web_traffic_event 
	where create_time > {from_time} and create_time < {to_time}
	group by member_no, cid
) t1 
where (member_no, nums) in ( 
	select 
		member_no,  max(nums) as nums
	from ( 
	    SELECT  member_no, cid as value, max(create_time) as nums FROM db_neocam.t_cam_web_traffic_event 
	    where create_time > {from_time} and create_time < {to_time}
	    group by member_no, cid
	) t group by member_no  
)
"""
# 近期最多访问活动 t_cam_web_traffic_event
recent_most_in_activity = """
select t1.member_no, t1.cid as value from (
	SELECT  member_no, cid, count(cid) as nums FROM db_neocam.t_cam_web_traffic_event 
	where create_time > {from_time} and create_time < {to_time}
	group by member_no, cid
) t1 
where (member_no, nums) in ( 
	select 
		member_no,  max(nums) as nums
	from ( 
	    SELECT  member_no, cid, count(cid) as nums FROM db_neocam.t_cam_web_traffic_event 
	    where create_time > {from_time} and create_time < {to_time}
	    group by member_no, cid
	) t group by member_no  
)
"""

# 数据源 --> level
# 近期最近一次领取优惠券
recent_receive_coupon = """
select t1.member_no, t1.card_id as value from (
	SELECT  member_no, card_id, max(received_time) as nums FROM db_neocrm.t_crm_coupon_user_info 
	where received_time > {from_time} and received_time < {to_time} and crm_id={crm_id}
	group by member_no, card_id
) t1 
where (member_no, nums) in ( 
	select 
		member_no,  max(nums) as nums
	from ( 
	    SELECT  member_no, card_id, max(received_time) as nums FROM db_neocrm.t_crm_coupon_user_info 
	    where received_time > {from_time} and received_time < {to_time} and crm_id={crm_id}
	    group by member_no, card_id
	) t group by member_no  
)
"""

# 近期最多领取优惠券
recent_most_receive_coupon = """
select t1.member_no, t1.card_id as value from (
	SELECT  member_no, card_id, count(card_id) as nums FROM db_neocrm.t_crm_coupon_user_info 
	where received_time > {from_time} and received_time < {to_time} and crm_id={crm_id}
	group by member_no, card_id
) t1 
where (member_no, nums) in ( 
	select 
		member_no,  max(nums) as nums
	from ( 
	    SELECT  member_no, card_id, count(card_id) as nums FROM db_neocrm.t_crm_coupon_user_info 
	    where received_time > {from_time} and received_time < {to_time} and crm_id={crm_id}
	    group by member_no, card_id
	) t group by member_no  
)
"""
# 近期最近一次核销优惠券
recent_redeem_coupon = """
select *  from (
	SELECT  member_no, card_id as value, max(redeem_time) as nums FROM db_neocrm.t_crm_coupon_user_info 
	where update_time > {from_time} and update_time < {to_time} and crm_id={crm_id} and redeem_time is not null
	group by member_no, card_id
) t1 
where (member_no, nums) in ( 
	select 
		member_no,  max(nums) as nums
	from ( 
	    SELECT  member_no, card_id, max(redeem_time) as nums FROM db_neocrm.t_crm_coupon_user_info 
	    where update_time > {from_time} and update_time < {to_time} and crm_id={crm_id} and redeem_time is not null
	    group by member_no, card_id
	) t group by member_no  
)
"""
# 近期最多核销优惠券
recent_most_redeem_coupon = """
select * from (
	SELECT  member_no, card_id as value, count(card_id) as nums FROM db_neocrm.t_crm_coupon_user_redeem_info 
	where update_time > {from_time} and update_time < {to_time} and crm_id={crm_id} and redeem_time is not null
	group by member_no, card_id
) t1 
where (member_no, nums) in ( 
	select 
		member_no,  max(nums) as nums
	from ( 
	    SELECT  member_no, card_id, count(card_id) as nums FROM db_neocrm.t_crm_coupon_user_redeem_info 
	    where update_time > {from_time} and update_time < {to_time} and crm_id={crm_id} and redeem_time is not null
	    group by member_no, card_id
	) t group by member_no  
)
"""

# 标签 计算方式的配置映射
tag_calculate_config1111111 = {
    "注册引流活动": campaign_code_sql,
    "注册引流渠道": channel_sql,
    "积分变更行为": points_change_sql,

    "性别": gender_sql,
    # "职业":
    "年龄": age_sql,
    "生日": birth_month_sql,
    "会员等级": member_level_sql,
    "会龄区间": vip_age_sql,
    "活跃状态": active_sql,
    "家庭成员数量": family_nums_sql,
    # "最近一次访问小程序出现的省份": recent_province_sql,
    # "最近一次访问小程序出现的城市": recent_city_sql,

    "近期购买频次": buy_times_sql,
    "近期购买支付金额": recent_pay_mounts_sql,
    "最近一次购买距今天数": recent_buy_days_sql,
    "最近一次购买商品": last_buy_goods_sql,

    "近期最近一次购买商品": recent_buy_goods_sql,
    "近期最多购买商品": recent_most_buy_goods,
    "近期最近一次购买商品类目": recent_buy_category,
    "近期最近最多购买商品类目": recent_most_buy_category,

    "近期最近一次访问活动": recent_in_activity,
    "近期最多访问活动": recent_most_in_activity,
    "近期最近一次领取优惠券": recent_receive_coupon,
    "近期最多领取优惠券":recent_most_receive_coupon,
    "近期最近一次核销优惠券": recent_redeem_coupon,
    "近期最多核销优惠券":recent_most_redeem_coupon

}


level_find_member_cfg = {
    "注册引流活动": campaign_code_sql,
    "注册引流渠道": channel_sql,
    "积分变更行为": points_change_sql,
    "性别": gender_sql,
    "职业": occupation_sql,
    "年龄": age_sql,
    "生日": birth_month_sql,
    "会员等级": member_level_sql,
    "会龄区间": vip_age_sql,
    # "活跃状态": active_sql,
    "家庭成员数量": family_nums_sql,
    # "最近一次访问小程序出现的省份": recent_province_sql,
    # "最近一次访问小程序出现的城市": recent_city_sql,
    #
    "近期购买频次": buy_times_sql,
    "近期购买支付金额": recent_pay_mounts_sql,
    "最近一次购买距今天数": recent_buy_days_sql,

}


async def save_update_user_tags(app, crm_id, member_no, bind_field, value):
    model = getUsertags()
    in_obj = {bind_field: value, "member_no":  member_no, "crm_id": crm_id}
    await app.mgr.execute(model.insert(in_obj).on_conflict(update=in_obj))
    logger.info(f"insert {bind_field}:{value} {member_no} {crm_id}")


async def handle_goods_level(app, crm_id, bind_field, from_date, to_date, value_field):
    # 最近一次购买 时间范围 一年到现在
    # 获取时间范围
    sql = recent_buy_goods_sql
    await data_find_member_no(app, crm_id, from_date, to_date, bind_field, value_field, sql)


async def handle_most_goods_level(app, crm_id, bind_field, from_date, to_date, value_field):
    sql = recent_most_buy_goods
    await data_find_member_no(app, crm_id, from_date, to_date, bind_field, value_field, sql)


async def handle_recent_buy_category(app, crm_id, bind_field, from_date, to_date, value_field):
    pass


async def handle_recent_most_buy_category():
    pass


async def handle_recent_in_activity(app, crm_id, bind_field, from_date, to_date, value_field):
    sql = recent_in_activity
    pass


async def handle_recent_most_in_activity(app, crm_id, bind_field, from_date, to_date, value_field):
    sql = recent_most_in_activity
    pass


async def data_find_member_no(app, crm_id, tag_id, from_date, to_date, bind_field, value_field, sql):
    this_sql = sql_printf(sql, crm_id=crm_id, from_time=from_date, to_time=to_date)
    logger.info(f"value_field:{value_field} bind_field:{bind_field} {this_sql}")
    results = await app.mgr.execute(TagInfo.raw(this_sql).dicts())
    # 结果更新的usertags 里面
    # 查看 rule.value
    result_dict = defaultdict(list)  # {'member_no'}
    for row in results:
        value_code = row.get(value_field)
        if not value_code:
            logger.info(f"sql no value")
            continue
        level_info = app.conf.levels_value.get(tag_id).get(value_code)
        logger.info(f"value:{value_code} -->find level_info:{level_info}")
        if not level_info:
            continue
        level_id = level_info.get("level_id")
        member_no = row.get("member_no")
        result_dict[member_no].append(level_id)
    # 拼接成sql保存
    for member_no, levels in result_dict.items():
        # 截取10条
        levels = [str(i) for i in levels[:10]]
        levels_id = ','.join(levels)
        await save_update_user_tags(app, crm_id, member_no, bind_field, levels_id)


# 近期最多购买 根据会员去计算
data_find_level_member_cfg = {


    "最近一次购买商品": handle_goods_level,
    #
    "近期最近一次购买商品": handle_goods_level,
    "近期最多购买商品": handle_most_goods_level,
    # "近期最近一次购买商品类目": handle_recent_buy_category,
    # "近期最近最多购买商品类目": handle_recent_most_buy_category,
    #
    "近期最近一次访问活动": handle_recent_in_activity,
    "近期最多访问活动": handle_recent_most_in_activity,
    "近期最近一次领取优惠券": recent_receive_coupon,
    "近期最多领取优惠券": recent_most_receive_coupon,
    "近期最近一次核销优惠券": recent_redeem_coupon,
    "近期最多核销优惠券":recent_most_redeem_coupon
}

data_find_level_sql_cfg = {
    "最近一次购买商品": recent_buy_goods_sql,

    "近期最近一次购买商品": recent_buy_goods_sql,
    "近期最多购买商品": recent_most_buy_goods,
    "近期最近一次购买商品类目": recent_buy_category,
    "近期最多购买商品类目": recent_most_buy_category,
    #
    "近期最近一次访问活动": recent_in_activity,
    "近期最多访问活动": recent_most_in_activity,
    "近期最近一次领取优惠券": recent_receive_coupon,
    "近期最多领取优惠券": recent_most_receive_coupon,
    "近期最近一次核销优惠券": recent_redeem_coupon,
    "近期最多核销优惠券":recent_most_redeem_coupon
}