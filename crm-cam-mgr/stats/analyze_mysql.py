q_visit_user = """
select 
    cid, 
    {tdate} as tdate,
    {thour} as thour,
    count(DISTINCT member_no) as expose_people 
from db_neocam.t_cam_web_traffic_event 
where create_time  > {from_time} and create_time  <= {to_time}
group by cid
"""

# 从活动分库 里面获取
q_join_user = """
select
    campaign_id as cid,
    {tdate} as tdate,
    {thour} as thour,
    count(distinct member_no) as click_people
from db_neocam.t_cam_campaign_record_{table_date}
where event_type = 1 and create_time  > {from_time} and create_time  <= {to_time}
group by campaign_id
"""

q_accept_user = """
select
    campaign_id as cid,
    {tdate} as tdate,
    {thour} as thour,
    count(distinct member_no) as pick_people
from db_neocam.t_cam_campaign_record_{table_date}
where event_type = 2 and create_time  > {from_time} and create_time  <= {to_time}
group by campaign_id
"""

# 分享人数中间表获取
q_share_user = """
SELECT 
    cid, 
    {tdate} as tdate,
    {thour} as thour,
    COUNT(DISTINCT unionid) as share_gift_people
FROM db_neocam.t_cam_wmp_share_event
WHERE create_time > {from_time} and create_time <= {to_time} 
GROUP BY cid
"""

q_register_user_cid = """
SELECT
{tdate} as tdate,
{thour} as thour,
SUBSTRING(campaign_code, 9) as cid,
count(1) as register_member_people 
FROM  db_neocrm.t_crm_member_source_info 
WHERE create_time > {from_time} and create_time <= {to_time} and campaign_code != ''
group BY campaign_code
"""

q_province_city_by_cid = """
select 
    cid,
    province,
    city,
    {tdate} as tdate,
    {thour} as thour,
    count(DISTINCT member_no) as numbers 
from db_neocam.t_cam_web_traffic_event 
where create_time  >= {from_time} and create_time  < {to_time}
group by cid, province, city
"""
# province

# 活动访客：从 t_web_traffic_event 中取，按照 account_id(埋点用于哪个实例 从cam的instance里面获取)，
# site_id，path，qs做过滤，然后统计uuid的去重复数量
#
# t_web_traffic_event 按照account_id，path 和 qs 做过滤统计
# qs cid字段
# 读 kafaka 写到新表里面 kdfka的topic名称和表名一样 代码写在cam-mgr里面 读kafaka优化逻辑
#
# INSERT INTO `db_event`.`t_web_traffic_event` (`event_id`, `uuid`, `member_no`, `user_id`, `account_id`, `site_id`,
# `page_id`, `page_type`, `session_id`, `keyword`, `referer`, `screen`, `charset`, `language`, `title`, `version`, `ip`,
# `province`, `city`, `host`, `path`, `qs`, `utm_request_id`, `utm_source`, `utm_campaign`, `utm_medium`, `browser_family`, `browser_version`, `os_family`, `os_version`, `device_family`, `device_model`, `device_brand`, `is_pc`, `is_mobile`, `is_tablet`, `is_touch_capable`, `is_bot`, `create_time`) VALUES (426, '8bbba870-3ed9-4eeb-a392-d70a76e5077e', 'Member-00001', NULL, 1801, 101, NULL, NULL, '8bbba8703ed94eeba392d70a76e5077e.17ea4d37462', NULL, 'https://authsa127.alipay.com/', '1920x1080x24', 'UTF-8', 'zh-CN', '巴拉官网', '1.1.3', '218.29.76.18', '河南', '郑州', 'bala.quickshark.cn', '/cdn_file/cms/2022-07-24/view/8661fa25-a878-4663-b42f-6561a1987fa4/project/index.html', '{\"cid\":60001,\"auth_code\":\"02349275e1b24d5eb23e265d83dcQX26\",\"state\":\"alipay\",\"app_id\":\"2021003111611907\",\"source\":\"alipay_wallet\",\"scope\":\"auth_base,auth_user\"}', NULL, NULL, NULL, NULL, 'Edge', '96.0.105', 'Mac OS X', '10.15.7', 'Mac', 'Mac', 'Apple', 1, 0, 0, 0, 0, '2022-01-29 15:53:50');
#
# 分享从kafka中间表
# 活动分享：t_wmp_share_event，提取path中的参数做过滤，path的路径是/vendor/mtsdk/pages/web-view，query string中包含url参数，url参数中包含活动cid字段，按照cid来统计分享指标。
#
# 分享人数：同上 url 中需要带上 cid 和 campaign_id
#
#
# f"t_cam_campaign_record_{_date}"
# 活动参与：活动库会做一张按照天分区的活动参与记录数据表
# 领取人数：同上 event_type = 2
#
#
# 注册会员：从会员注册数据表中统计，按照utm_campaign，utm_campaign的格式是：cam_crm_{活动ID}
#
# 城市分布按照活动访客