campaign_code_sql = """
select member_no, campaign_code from db_neocrm.t_crm_member_source
where create_time >= {from_time} and create_time < {to_time} and crm_id={crm_id}
and campaign_code={value0}
"""
channel_sql = """
select member_no from db_neocrm.t_crm_member_source
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
where t1.dim > {value0} and t1.dim < {value1}
"""
# 人口属性
# 性别
gender_sql = """
SELECT * FROM db_neocrm.t_crm_member_info tcmi
WHERE update_time >= {from_time}  update_time < {to_time} AND  crm_id= {crm_id} AND gender={value0}
"""
# 年龄
age_sql = """
SELECT * FROM db_neocrm.t_crm_member_info tcmi
WHERE update_time >= {from_time}  update_time < {to_time} AND  crm_id= {crm_id}
AND birthday >{value0} and birthday<{value1}
"""
# 生日
birth_month_sql = """
SELECT * FROM db_neocrm.t_crm_member_info tcmi
WHERE update_time >= {from_time}  update_time < {to_time} AND  crm_id= {crm_id}
AND date_format(birthday ,'%m')={value0}
"""
# 会员等级
member_level_sql = """
SELECT * FROM db_neocrm.t_crm_member_info tcmi
WHERE update_time >= {from_time}  update_time < {to_time} AND  crm_id= {crm_id}
AND level={value0}
"""
# 会领区间
vip_age_sql = """
SELECT * FROM db_neocrm.t_crm_member_info tcmi
WHERE  crm_id= {crm_id}
AND create_time >= {value0} and create_time<{value1}
"""
# 活跃状态
active_sql = """
select openid from (
	select openid,count(1) as count from db_event.t_wmp_app_event
	where create_time > {from_time} and create_time <= {to_time}
	group by openid
) t where t.count > {value0} and t.count <= {value1}
"""
# 家庭成员数量
family_nums_sql = """
select
    member_no
from (
    select member_no, count(1) as count from db_neocrm.t_crm_member_family
    where crm_id={crm_id}
) t1 where t1.count>{value0} and t1.count<={value1}
"""
# 城市
recent_city_sql = """
select member_no from db_neocrm.t_crm_member_info where crm_id={crm_id}
and update_time >= {from_time}  update_time < {to_time}
and city like '%{value0}%'
"""
# 省份
recent_province_sql = """
select member_no from db_neocrm.t_crm_member_info where crm_id={crm_id}
and update_time >= {from_time}  update_time < {to_time}
and province like '%{value0}%'
"""
# 购买频次
buy_times_sql = """
select
    member_no
from (
    select member_no, sount(1) as count from db_neocrm.t_crm_order_info
    where update_time >= {from_time}  update_time < {to_time} and crm_id=crm_id
    group by member_no
) t1 where t1.count > {value0} and t1.count <= {value1}
"""

# 近期购买支付金额
recent_pay_mounts_sql = """
select
    member_no
from (
    select member_no, sum(pay_amount) as count from db_neocrm.t_crm_order_info
    where update_time >= {from_time}  update_time < {to_time} and crm_id=crm_id
    group by member_no
) t1 where t1.count > {value0} and t1.count <= {value1}
"""
# 最近一次购买距今天数
recent_buy_days_sql = """
select
    member_no
from (
    select member_no, datediff(max(create_time), now()) as count from db_neocrm.t_crm_order_info
    where update_time >= {from_time}  update_time < {to_time} and crm_id=crm_id
) t1 where t1.count > {value0} and t1.count <= {value1}
"""
# 最近一次购买商品
last_buy_goods_sql = """
select
    member_no
from (
    select member_no, max(create_time), sku_id from db_neocrm.t_crm_order_info
    where update_time >= {from_time}  update_time < {to_time} and crm_id=crm_id
) t1 where t1.sku_id = {value0}
"""
# 消费习惯
# 近期最近一次购买商品
recent_buy_goods_sql = """
select
    member_no
from (
    select member_no, max(create_time), sku_id from db_neocrm.t_crm_order_info
    where update_time >= {from_time}  update_time < {to_time} and crm_id=crm_id
) t1 where t1.sku_id = {value0}
"""

# todo 近期最多购买商品 这种计算逻辑要更改
recent_most_buy_goods = """
select
    member_no, sku_id as value
from (
    select member_no, count(discount sku_id) as count, sku_id from db_neocrm.t_crm_order_info
    where update_time >= {from_time}  update_time < {to_time} and crm_id=crm_id
    and sku_id={value0}
    group by member_no, sku_id
) t1 t1.count
"""
# 近期最近一次购买商品类目
recent_buy_category = """

"""
# 近期最多购买商品类目
recent_most_buy_category = """
"""
# 近期最近一次访问活动
recent_in_activity = """
"""
# 近期最多访问活动
recent_most_in_activity = """

"""

# 数据源 --> level
recent_receive_coupon = """
select * from (
	SELECT  member_no, card_id, max(received_time) as nums FROM db_neocrm.t_crm_coupon_user_info
	where create_time > {value0} and create_time < {value1} and crm_id={crm_id}
	group by member_no, card_id
) t1
where (member_no, nums) in (
	select
		member_no,  max(nums) as nums
	from (
	    SELECT  member_no, card_id, max(received_time) as nums FROM db_neocrm.t_crm_coupon_user_info
	    where create_time > {value0} and create_time < {value1} and crm_id={crm_id}
	    group by member_no, card_id
	) t group by member_no
)
"""

# 近期最多领取优惠券
recent_most_receive_coupon = """
select * from (
	SELECT  member_no, card_id, count(card_id) as nums FROM db_neocrm.t_crm_coupon_user_info
	where create_time > {value0} and create_time < {value1} and crm_id={crm_id}
	group by member_no, card_id
) t1
where (member_no, nums) in (
	select
		member_no,  max(nums) as nums
	from (
	    SELECT  member_no, card_id, count(card_id) as nums FROM db_neocrm.t_crm_coupon_user_info
	    where create_time > {value0} and create_time < {value1} and crm_id={crm_id}
	    group by member_no, card_id
	) t group by member_no
)
"""
# 近期最近一次核销优惠券
recent_redeem_coupon = """
SELECT member_no from (
	SELECT member_no, max(redeem_time) from db_neocrm.t_crm_coupon_user_redeem_info
	WHERE
	update_time > {from_time} and update_time <={to_time} and crm_id={crm_id}
	AND card_id={value0}
	group by member_no
) t
"""
# 近期最多核销优惠券
recent_most_redeem_coupon = """
select * from (
	SELECT  member_no, card_id, count(card_id) as nums FROM db_neocrm.t_crm_coupon_user_redeem_info
	where create_time > {value0} and create_time < {value1} and crm_id={crm_id}
	group by member_no, card_id
) t1
where (member_no, nums) in (
	select
		member_no,  max(nums) as nums
	from (
	    SELECT  member_no, card_id, count(card_id) as nums FROM db_neocrm.t_crm_coupon_user_redeem_info
	    where update_time > {value0} and update_time < {value1} and crm_id={crm_id}
	    group by member_no, card_id
	) t group by member_no
)
"""

# 标签 计算方式的配置映射
tag_calculate_config = {
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
    "最近一次访问小程序出现的省份": recent_province_sql,
    "最近一次访问小程序出现的城市": recent_city_sql,

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
    # "职业":
    "年龄": age_sql,
    "生日": birth_month_sql,
    "会员等级": member_level_sql,
    "会龄区间": vip_age_sql,
    "活跃状态": active_sql,
    "家庭成员数量": family_nums_sql,
    "最近一次访问小程序出现的省份": recent_province_sql,
    "最近一次访问小程序出现的城市": recent_city_sql,

    "近期购买频次": buy_times_sql,
    "近期购买支付金额": recent_pay_mounts_sql,
    "最近一次购买距今天数": recent_buy_days_sql,

}

# 近期最多购买 根据会员去计算
data_find_level_member_cfg = {
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