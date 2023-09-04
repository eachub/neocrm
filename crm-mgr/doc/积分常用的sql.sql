-- 查看可用增加的积分
select 
	crm_id, sum(points) as act_add 
from db_neocrm.t_crm_points_history  
where 
	event_type in ('produce', 'accept')
	and (expire_time > '2022-06-17 00:00:00' or expire_time is NULL)
	and (unfreeze_time < '2022-06-17 00:00:00' or unfreeze_time is NULL)
	and event_at < '2022-06-17 00:00:00'
	and reverse_status =0
group by crm_id

-- 查看积分减少
select 
	crm_id, sum(points) as act_reduce 
from db_neocrm.t_crm_points_history  
where 
	event_type in ("consume", 'present')
	and event_at < '2022-06-17 00:00:00'
	and reverse_status =0
group by crm_id


-- 新增积分
SELECT
    crm_id,
    SUM(points) as prod_points,
    count(DISTINCT member_no) as prod_points_user
FROM
    db_neocrm.t_crm_points_history
WHERE
    reverse_status = 0 and event_type in ('produce', 'accept')
    and event_at >= '2022-06-01 00:00:00'  AND event_at < '2022-06-17 00:00:00'
GROUP BY crm_id

-- 消耗积分
SELECT
    crm_id,
    SUM(points) as cons_points,
    count(DISTINCT member_no) as cons_points_user
FROM
    db_neocrm.t_crm_points_history
WHERE
    reverse_status = 0 and event_type in ('consume', 'present')
    and event_at >= '2022-06-01 00:00:00'  AND event_at < '2022-06-17 00:00:00'
GROUP BY crm_id

-- 过期积分
SELECT
    crm_id,
    SUM(points) as expire_points,
    count(DISTINCT member_no) as expire_points_user
FROM
    db_neocrm.t_crm_points_history
WHERE
    reverse_status = 0 and event_type in ('produce', 'accept')
    and expire_time is NOT  NULL
    and expire_time >= '2022-06-01 00:00:00' and expire_time<'2022-06-17 00:00:00'
GROUP BY crm_id

-- 转赠积分
SELECT
    crm_id,
    SUM(points) as trans_points,
    count(DISTINCT from_user) as trans_points_user
FROM
    db_neocrm.t_crm_points_transfer
WHERE
    create_time >= '2022-06-01 00:00:00'  AND create_time < '2022-06-17 00:00:00'
GROUP BY crm_id

-- 领取转赠积分
SELECT
    crm_id,
    SUM(points) as accept_points,
    count(DISTINCT to_user) as accept_points_user
FROM
    db_neocrm.t_crm_points_transfer
WHERE
	done=1
    and create_time >= '2022-06-01 00:00:00'  AND create_time < '2022-06-17 00:00:00'
GROUP BY crm_id



- 获取可用积分总值 可用积分人数
select
	crm_id,
	sum(act_points) as total_active,
	count(DISTINCT member_no) as total_active_user
from (
	select
		tt2.crm_id as crm_id,
		tt2.member_no as member_no,
		tt2.act_add -tt1.act_reduce as act_points
	from (
		select
			crm_id,
			sum(points) as act_reduce,
			member_no
		from t_crm_points_history
		where
			event_type in ('consume', 'present')
			and event_at < '2022-06-17 00:00:00'
			and reverse_status = 0
		group by crm_id, member_no
    ) tt1
	RIGHT JOIN (
		select
			crm_id,
			sum(points) as act_add,
			member_no
		from t_crm_points_history
		where
			event_type in ('produce', 'accept')
				and (expire_time > '2022-06-17 00:00:00'
					or expire_time is NULL)
				and (unfreeze_time < '2022-06-17 00:00:00'
					or unfreeze_time is NULL)
				and event_at < '2022-06-17 00:00:00'
				and reverse_status = 0
			group by crm_id, member_no  
    ) tt2 ON tt2.crm_id = tt1.crm_id and tt2.member_no = tt1.member_no
) tt3
group by tt3.crm_id