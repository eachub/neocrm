

q_points_by_crm_id = """
SELECT
    {tdate} AS tdate,
    {thour} AS thour,
    t1.total_prod as total_prod,
    t1.total_prod_user as total_prod_user,
    t2.prod_points as prod_points,
    t2.prod_points_user as prod_points_user,
    t3.total_consume as total_consume,
    t3.total_consume_user as total_consume_user,
    t4.consume_points as consume_points,
    t4.consume_points_user as consume_points_user,
    t5.total_expire as total_expire,
    t5.total_expire_user as total_expire_user,
    t6.expire_points as expire_points,
    t6.expire_points_user as expire_points_user,
    t7.total_transfer as total_transfer,
    t7.total_transfer_user as total_transfer_user,
    t8.total_accept as total_accept,
    t8.total_accept_user as total_accept_user,
    (t10.act_add-t9.act_reduce) as total_active,
    (t10.act_add_user-t9.act_reduce_user) as total_active_user
FROM (
    SELECT
        crm_id,
        SUM(points) as total_prod,
        count(DISTINCT member_no) as total_prod_user
    FROM
        t_crm_points_history
    WHERE
        reverse_status = 0 and event_type in ('produce', 'accept')
        and event_at < {to_time} AND {extra_conds}
    GROUP BY crm_id
) t1 
FULL OUTER JOIN(
    SELECT
        crm_id,
        SUM(points) as prod_points,
        count(DISTINCT member_no) as prod_points_user
    FROM
        t_crm_points_history
    WHERE
        reverse_status = 0 and event_type in ('produce', 'accept')
        and event_at >= {from_time} AND event_at < {to_time} AND {extra_conds}
    GROUP BY crm_id
) t2 ON t2.crm_id=t1.crm_id
FULL OUTER JOIN(
    SELECT
        crm_id,
        SUM(points) as total_consume,
        count(DISTINCT member_no) as total_consume_user
    FROM
        t_crm_points_history
    WHERE
        reverse_status = 0 and event_type in ('consume', 'present')
        AND event_at < {to_time} AND {extra_conds}
    GROUP BY crm_id
) t3 ON t3.crm_id=t1.crm_id
FULL OUTER JOIN(
    SELECT
        crm_id,
        SUM(points) as consume_points,
        count(DISTINCT member_no) as consume_points_user
    FROM
        t_crm_points_history
    WHERE
        reverse_status = 0 and event_type in ('consume', 'present')
        and event_at >= {from_time}  AND event_at < {to_time} AND {extra_conds}
    GROUP BY crm_id
) t4 ON t4.crm_id=t1.crm_id
FULL OUTER JOIN(
    SELECT
        crm_id,
        SUM(points) as total_expire,
        count(DISTINCT member_no) as total_expire_user
    FROM
        t_crm_points_history
    WHERE
        reverse_status = 0 and event_type in ('produce', 'accept')
        and expire_time is NOT  NULL
        and expire_time >= {from_time} and expire_time < {to_time} AND {extra_conds}
    GROUP BY crm_id
) t5 ON t5.crm_id=t1.crm_id
FULL OUTER JOIN(
    SELECT
        crm_id,
        SUM(points) as expire_points,
        count(DISTINCT member_no) as expire_points_user
    FROM
        t_crm_points_history
    WHERE
        reverse_status = 0 and event_type in ('produce', 'accept')
        and expire_time is NOT  NULL
        and expire_time >= {from_time} and expire_time < {to_time} AND {extra_conds}
    GROUP BY crm_id
) t6 ON t6.crm_id=t1.crm_id
FULL OUTER JOIN(
    SELECT
        crm_id,
        SUM(points) as total_transfer,
        count(DISTINCT from_user) as total_transfer_user
    FROM
        t_crm_points_transfer
    WHERE
        create_time < {to_time} AND {extra_conds}
    GROUP BY crm_id
) t7 ON t7.crm_id = t1.crm_id
FULL OUTER JOIN(
    SELECT
        crm_id,
        SUM(points) as total_accept,
        count(DISTINCT to_user) as total_accept_user
    FROM
        t_crm_points_transfer
    WHERE
        done=1
        and create_time < {to_time} AND {extra_conds}
    GROUP BY crm_id
) t8 ON t8.crm_id=t1.crm_id

FULL OUTER JOIN(
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
                and event_at < {to_time}
                and reverse_status = 0 AND {extra_conds}
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
                    and (expire_time > {to_time}
                        or expire_time is NULL)
                    and (unfreeze_time < {to_time}
                        or unfreeze_time is NULL)
                    and event_at < {to_time}
                    and reverse_status = 0 AND {extra_conds}
                group by crm_id, member_no  
        ) tt2 ON tt2.crm_id = tt1.crm_id and tt2.member_no = tt1.member_no
    ) tt3
    group by tt3.crm_id
) t9 on t9.crm_id=t1.crm_id
"""

q_points_total1 = """
SELECT
    crm_id,
    {tdate} as tdate,
    {thour} as thour,
    SUM(points) as total_prod,
    count(DISTINCT member_no) as total_prod_user
FROM
    t_crm_points_history
WHERE
    reverse_status = 0 and event_type in ('produce', 'accept')
    and event_at < {to_time} AND {extra_conds}
GROUP BY crm_id
"""
q_points_total2 = """
SELECT
    crm_id,
    {tdate} as tdate,
    {thour} as thour,
    SUM(points) as prod_points,
    count(DISTINCT member_no) as prod_points_user
FROM
    t_crm_points_history
WHERE
    reverse_status = 0 and event_type in ('produce', 'accept')
    and event_at >= {from_time} AND event_at < {to_time} AND {extra_conds}
GROUP BY crm_id
"""
q_points_total3 = """
SELECT
    crm_id,
    {tdate} as tdate,
    {thour} as thour,
    SUM(points) as total_consume,
    count(DISTINCT member_no) as total_consume_user
FROM
    t_crm_points_history
WHERE
    reverse_status = 0 and event_type in ('consume', 'present')
    AND event_at < {to_time} AND {extra_conds}
GROUP BY crm_id
"""
q_points_total4 = """
SELECT
    crm_id,
    {tdate} as tdate,
    {thour} as thour,
    SUM(points) as consume_points,
    count(DISTINCT member_no) as consume_points_user
FROM
    t_crm_points_history
WHERE
    reverse_status = 0 and event_type in ('consume', 'present')
    and event_at >= {from_time}  AND event_at < {to_time} AND {extra_conds}
GROUP BY crm_id
"""
q_points_total5 = """
SELECT
    crm_id,
    {tdate} as tdate,
    {thour} as thour,
    SUM(points) as total_expire,
    count(DISTINCT member_no) as total_expire_user
FROM
    t_crm_points_history
WHERE
    reverse_status = 0 and event_type in ('produce', 'accept')
    and expire_time is NOT  NULL
    and expire_time >= {from_time} and expire_time < {to_time} AND {extra_conds}
GROUP BY crm_id
"""
q_points_total6 = """
SELECT
    crm_id,
    {tdate} as tdate,
    {thour} as thour,
    SUM(points) as expire_points,
    count(DISTINCT member_no) as expire_points_user
FROM
    t_crm_points_history
WHERE
    reverse_status = 0 and event_type in ('produce', 'accept')
    and expire_time is NOT  NULL
    and expire_time >= {from_time} and expire_time < {to_time} AND {extra_conds}
GROUP BY crm_id
"""
q_points_total7 = """
SELECT
    crm_id,
    {tdate} as tdate,
    {thour} as thour,
    SUM(points) as total_transfer,
    count(DISTINCT from_user) as total_transfer_user
FROM
    t_crm_points_transfer
WHERE
    create_time < {to_time} AND {extra_conds}
GROUP BY crm_id
"""
q_points_total8 = """
SELECT
    crm_id,
    {tdate} as tdate,
    {thour} as thour,
    SUM(points) as total_accept,
    count(DISTINCT to_user) as total_accept_user
FROM
    t_crm_points_transfer
WHERE
    done=1
    and create_time < {to_time} AND {extra_conds}
GROUP BY crm_id
"""
q_points_total9_ = """
select
    crm_id,
    {tdate} as tdate,
    {thour} as thour,
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
            and event_at < {to_time}
            and reverse_status = 0 AND {extra_conds}
        group by crm_id, member_no
    ) tt1
    JOIN (
        select
            crm_id,
            sum(points) as act_add,
            member_no
        from t_crm_points_history
        where
            event_type in ('produce', 'accept')
                and (expire_time > {to_time}
                    or expire_time is NULL)
                and (unfreeze_time < {to_time}
                    or unfreeze_time is NULL)
                and event_at < {to_time}
                and reverse_status = 0 AND {extra_conds}
            group by crm_id, member_no  
    ) tt2 ON tt2.crm_id = tt1.crm_id and tt2.member_no = tt1.member_no
) tt3
group by tt3.crm_id
"""

q_points_total9 = """
select
    crm_id as crm_id,
    {tdate} as tdate,
    {thour} as thour,
    sum(points_value) as total_active,
    count(DISTINCT member_no) as total_active_user
from (
    select
        crm_id,
        sum(-points) as points_value,
        member_no
    from t_crm_points_history
    where
        event_type in ('consume', 'present')
        and event_at < {to_time}
        and reverse_status = 0 AND {extra_conds}
    group by crm_id, member_no
    UNION ALL
    select
        crm_id,
        sum(points) as points_value,
        member_no
    from t_crm_points_history
    where
        event_type in ('produce', 'accept')
        and (expire_time > {to_time}
            or expire_time is NULL)
        and (unfreeze_time < {to_time}
            or unfreeze_time is NULL)
        and event_at < {to_time}
        and reverse_status = 0 AND {extra_conds}
    group by crm_id, member_no  
) tt2
group by crm_id
"""

q_points_by_scene= """
SELECT 
    action_scene as label,
    action_scene as item,
    sum(points) as counts 
from t_crm_points_history 
where 
    event_type='produce'
    and event_at >= {from_time} and event_at < {to_time} and {extra_conds}
group by action_scene 
"""

q_reduce_by_scene = """
SELECT 
    action_scene as label,
    action_scene as item,
    sum(points) as counts 
from t_crm_points_history 
where 
    event_type='consume'
    and event_at >= {from_time} and event_at < {to_time} and {extra_conds}
group by action_scene 
"""