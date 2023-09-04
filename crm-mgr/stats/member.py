# 新增会员 new_member
q_member_dim1 = """
SELECT
    crm_id,
    {tdate} as tdate,
    {thour} as thour,
    count(DISTINCT member_no) as new_member
FROM
    t_crm_member_info
WHERE
    create_time >= {from_time} AND create_time < {to_time} AND {extra_conds}
GROUP BY crm_id
"""

# 累积会员 total_member
q_member_dim2 = """
SELECT
    crm_id,
    {tdate} as tdate,
    {thour} as thour,
    count(DISTINCT member_no) as total_member
FROM
    t_crm_member_info
WHERE
    create_time < {to_time} AND {extra_conds}
GROUP BY crm_id
"""

# 新增家庭成员 new_family
q_member_dim3 = """
SELECT
    crm_id,
    {tdate} as tdate,
    {thour} as thour,
    count(1) as new_family
FROM
    t_crm_member_family
WHERE
    create_time >= {from_time} AND create_time < {to_time} AND {extra_conds}
GROUP BY crm_id
"""

# 累积家庭成员 total_family
q_member_dim4 = """
SELECT
    crm_id,
    {tdate} as tdate,
    {thour} as thour,
    count(1) as total_family
FROM
    t_crm_member_family
WHERE
    create_time < {to_time} AND {extra_conds}
GROUP BY crm_id
"""

# 注册渠道
q_member_by_source= """
SELECT 
    channel_code as label,
    channel_code as item,
    sum(1) as counts 
from t_crm_member_source_info 
where 
    create_time >= {from_time} and create_time < {to_time} and {extra_conds}
group by channel_code 
ORDER BY counts DESC 
LIMIT 10
"""
# 来源小程序
q_member_by_minip= """
SELECT 
    appid as label,
    appid as item,
    sum(1) as counts 
from t_crm_member_source_info 
where 
    create_time >= {from_time} and create_time < {to_time} and {extra_conds}
group by appid 
ORDER BY counts DESC 
LIMIT 10
"""

# 来源场景
q_member_by_scene= """
SELECT 
    scene as label,
    scene as item,
    sum(1) as counts 
from t_crm_member_source_info 
where 
    create_time >= {from_time} and create_time < {to_time} and LENGTH(scene)>0 and {extra_conds}
group by scene 
ORDER BY counts DESC 
LIMIT 10
"""
# 排行分布


q_user_by_invite_code = """
SELECT 
	t2.nickname AS label,
	t1.invite_code AS item,
	t1.counts AS counts
FROM (
	SELECT
		invite_code,
		COUNT(1) as counts
	FROM
		t_crm_member_source_info
	WHERE
	    create_time >= {from_time} AND create_time < {to_time} AND length(invite_code) > 1 AND {extra_conds}
	group by
		invite_code
) t1
LEFT JOIN t_crm_member_info t2
ON t2.invite_code =t1.invite_code
ORDER BY counts DESC 
LIMIT {tops}
"""
