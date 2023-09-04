# -*- coding: utf-8 -*-

# 统计tag_id对应bind_filed非空的数量
q_tag_qty = \
"""
SELECT
    arrayJoin(tag_id_list) AS tag_id,
    uniq(super_id) AS super_id,
    sum(ifNull(unionid, 0)) AS unionid,
    sum(ifNull(mobile, 0)) AS mobile,
    sum(ifNull(member_no, 0)) AS member_no
FROM (
    SELECT
        t0.super_id,
        t1.unionid,
        t1.mobile,
        t1.member_no,
        arrayFilter(x->x!=0, [{if_empty_fields}]) AS tag_id_list
    FROM db_core.t_tags t0

    LEFT JOIN (
        SELECT
            super_id,
            countIf(like(id,'%:unionid:%')) AS unionid,
            countIf(like(id,'%:mobile:%')) AS mobile,
            countIf(like(id,'%:member_no:%')) AS member_no
        FROM dw_neocdp.t_cdp_id_link
        WHERE instance_id={instance_id}
        GROUP BY super_id
    ) t1 ON t0.super_id = t1.super_id

    WHERE
        t0.uuid IN (SELECT argMax(uuid, create_time) FROM local_db_core.t_tags WHERE instance_id={instance_id} GROUP BY super_id)
        AND notEmpty(tag_id_list) AND ({extra_conds})
    SETTINGS join_use_nulls=1
)
GROUP BY tag_id
"""


q_tag_count_qty = \
"""
SELECT
    arrayJoin(tag_result) AS tag_count,
    uniq(super_id) AS super_id,
    sum(ifNull(unionid, 0)) AS unionid,
    sum(ifNull(mobile, 0)) AS mobile,
    sum(ifNull(member_no, 0)) AS member_no
FROM (
    SELECT
        t0.super_id,
        t1.unionid,
        t1.mobile,
        t1.member_no,
        t0.tag_result
    FROM (
        SELECT
            super_id,
            groupArray((tag_id,tag_count)) as tag_result
        FROM ( 
            SELECT super_id as super_id,
            arrayJoin(arrayFilter(x->x!=0, [{if_empty_fields}])) AS tag_id,
            count() as tag_count 
            FROM db_core.t_tags
            WHERE 
              uuid IN (SELECT argMax(uuid, create_time) FROM local_db_core.t_tags WHERE instance_id={instance_id} GROUP BY super_id)
              AND tag_id is not null 
              AND ({extra_conds})
            GROUP BY super_id, tag_id 
        ) group by super_id
    ) t0
    LEFT JOIN (
        SELECT
            super_id,
            countIf(like(id,'%:unionid:%')) AS unionid,
            countIf(like(id,'%:mobile:%')) AS mobile,
            countIf(like(id,'%:member_no:%')) AS member_no
        FROM dw_neocdp.t_cdp_id_link
        WHERE instance_id={instance_id}
        GROUP BY super_id
    ) t1 ON t0.super_id = t1.super_id
    SETTINGS join_use_nulls=1
)
GROUP BY tag_count
"""


q_level_qty = \
"""
SELECT
    arrayJoin(level_id_list) AS level_id,
    uniq(super_id) AS super_id,
    sum(ifNull(unionid, 0)) AS unionid,
    sum(ifNull(mobile, 0)) AS mobile,
    sum(ifNull(member_no, 0)) AS member_no
FROM (
    SELECT
        t0.super_id,
        t1.unionid,
        t1.mobile,
        t1.member_no,
        arrayFlatten([{tag_field_list}]) AS level_id_list
    FROM db_core.t_tags t0

    LEFT JOIN (
        SELECT
            super_id,
            countIf(like(id,'%:unionid:%')) AS unionid,
            countIf(like(id,'%:mobile:%')) AS mobile,
            countIf(like(id,'%:member_no:%')) AS member_no
        FROM dw_neocdp.t_cdp_id_link
        WHERE instance_id={instance_id}
        GROUP BY super_id
    ) t1 ON t0.super_id = t1.super_id

    WHERE
        t0.uuid IN (SELECT argMax(uuid, create_time) FROM local_db_core.t_tags WHERE instance_id={instance_id} GROUP BY super_id)
        AND notEmpty(level_id_list) AND ({extra_conds})
    SETTINGS join_use_nulls=1
)
GROUP BY level_id
"""


q_conds_ids = \
"""
SELECT
    t0.super_id,
    t1.unionid,
    t1.mobile,
    t1.member_no
FROM db_core.t_tags t0

LEFT JOIN (
    SELECT
        super_id,
        groupArray(IF(like(id,'%:unionid:%'), id, NULL)) AS unionid,
        groupArray(IF(like(id,'%:mobile:%'), id, NULL)) AS mobile,
        groupArray(IF(like(id,'%:member_no:%'), id, NULL)) AS member_no
    FROM dw_neocdp.t_cdp_id_link
    WHERE instance_id={instance_id}
    GROUP BY super_id
) t1 ON t0.super_id = t1.super_id

WHERE
    t0.uuid IN (SELECT argMax(uuid, create_time) FROM local_db_core.t_tags WHERE instance_id={instance_id} GROUP BY super_id)
    AND ({extra_conds})
SETTINGS join_use_nulls=1
"""

q_conds_cnt = \
"""
SELECT
    uniq(t0.super_id) AS super_id,
    sum(ifNull(t1.unionid, 0)) AS unionid,
    sum(ifNull(t1.mobile, 0)) AS mobile,
    sum(ifNull(t1.member_no, 0)) AS member_no
FROM db_core.t_tags t0

LEFT JOIN (
    SELECT
        super_id,
        countIf(like(id,'%:unionid:%')) AS unionid,
        countIf(like(id,'%:mobile:%')) AS mobile,
        countIf(like(id,'%:member_no:%')) AS member_no
    FROM dw_neocdp.t_cdp_id_link
    WHERE instance_id={instance_id}
    GROUP BY super_id
) t1 ON t0.super_id = t1.super_id

WHERE
    t0.uuid IN (SELECT argMax(uuid, create_time) FROM local_db_core.t_tags WHERE instance_id={instance_id} GROUP BY super_id)
    AND ({extra_conds})
SETTINGS join_use_nulls=1
"""
