#!/bin/bash
# 配置累积积分规则
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/mgr/points/10080/rules/produce_scene' \
--header 'Content-Type: application/json' \
--data '{
    "rule_name": "会员登录",
    "action_scene":"user_login",
    "points_type":"event",
    "expire_term": 30,
    "freeze_term":3,
    "change_points": 10,
    "range_days":1,
}'

# 下单支付
curl --location --request POST --X POST 'http://127.0.0.1:21200/api/crm/mgr/points/10080/rules/produce_scene' \
--header 'Content-Type: application/json' \
--data '{
    "rule_name": "下单支付",
    "action_scene":"order_pay",
    "points_type":"order",
    "expire_term": 30,
    "per_money": 50,
    "change_points": 10,
    "freeze_term":3
}'

# 分享商品
curl --location --request POST --X POST 'http://127.0.0.1:21200/api/crm/mgr/points/10080/rules/produce_scene' \
--header 'Content-Type: application/json' \
--data '{
    "rule_name": "分享商品",
    "action_scene":"share_goods",
    "points_type":"event",
    "expire_term": 30,
    "freeze_term":3,
    "change_points": 10,
    "max_times": 2,
    "range_days":1
}'

# 注册送积分
curl --location --request POST --X POST 'http://127.0.0.1:21200/api/crm/mgr/points/10080/rules/produce_scene' \
--header 'Content-Type: application/json' \
--data '{
    "rule_name": "注册送积分",
    "action_scene":"register",
    "points_type":"event",
    "expire_term": 30,
    "change_points": 10,
    "max_times": 1,
    "range_days":0
}'
# 邀请新人入会
curl --location --request POST --X POST 'http://127.0.0.1:21200/api/crm/mgr/points/10080/rules/produce_scene' \
--header 'Content-Type: application/json' \
--data '{
    "rule_name": "邀请新人入会50积分",
    "action_scene":"invite_new",
    "points_type":"event",
    "expire_term": 90,
    "freeze_term":1,
    "change_points": 50
}'

# 配置积分累积规则 订单
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/mgr/points/10080/rules/produce_scene' \
--header 'Content-Type: application/json' \
--data '{
    "rule_name": "下单支付",
    "action_scene":"order_pay",
    "points_type":"order",
    "expire_term": 30,
    "per_money": 50,
    "convert_points": 10,
    "freeze_term":3
}'

# 修改积分累积规则
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/mgr/points/10080/rules/produce_scene/update' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "rule_id":1,
    "rule_name": "每日登录",
    "expire_term": 30,
    "per_money": 50,
    "convert_points": 15,
    "freeze_term":3
}'

# 积分消耗规则配置
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/mgr/points/10080/rules/consume_scene' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "rule_name": "积分抵扣",
    "action_scene":"user_discount",
    "expire_term": 30,
    "base_points": 50,
    "convert_money":2,
    "consume_level":1
}'

# 修改积分增加规则
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/mgr/points/10080/rules/consume_scene/update' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "rule_id": 1,
    "rule_name": "积分抵扣现金",
    "base_points": 50,
    "convert_money":2
}'

# 积分规则删除
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/mgr/points/10080/rules/delete' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "rule_id": 1,
    "rule_type": "produce"
}'

# 积分规则查询
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/mgr/points/10080/rules/query' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "rule_type": "produce",
    "action_scene":"user_login"
}'


# 获取积分概览
curl --location --request GET 'https://dev.quickshark.cn/api/crm/mgr/analyze/10080/points/total?dr=2022-06-10~2022-07-01&crm_id=10080' \

# 积分趋势图
curl --location --request GET 'http://127.0.0.1:21100/api/crm/mgr/analyze/10080/points/trend?dr=2022-06-10~2022-07-01&crm_id=10080' \

# 积分来源分布
curl --location --request GET 'http://127.0.0.1:21100/api/crm/mgr/analyze/10080/points/distr?dr=2022-06-10~2022-07-01&crm_id=10080&types=source' \

# 积分消耗来源分布
curl --location --request GET 'http://127.0.0.1:21100/api/mgr/analyze/10080/points/distr?dr=2022-06-10~2022-07-01&crm_id=10080&types=redu_source' \

# 获取crm实例积分场景信息
curl --location --request GET 'https://dev.quickshark.cn/api/crm/mgr/points/10080/scene_info'