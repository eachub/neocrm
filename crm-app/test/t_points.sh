

# 积分累加by积分值
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/crm/points/10080/produce/direct' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "event_no": "EACH20220615202826397549953509",
    "member_no": "ec_18165fd7455_JGhyfyLmX",
    "action_scene": "order_pay",
    "event_type":"order",
    "points": 20,
    "event_at": "2022-06-15 18:00:00",
    "expire_days": 180,
    "freeze_hours": 48,
    "store_code": "ec_mall",
    "cost_center": "cost_center001",
    "operator":"小程序",
    "event_desc":"用户购买了100元酸奶"
}'

# 积分累加 积分值 无冻结时间
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/crm/points/10080/produce/direct' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "event_no": "EACH20220615202826397549953506",
    "member_no": "ec_18165fd7455_JGhyfyLmX",
    "action_scene": "order_pay",
    "event_type":"order",
    "points": 20,
    "event_at": "2022-06-16 09:00:00",
    "expire_days": 180,
    "freeze_hours": 0,
    "store_code": "ec_mall",
    "cost_center": "cost_center001",
    "operator":"小程序",
    "event_desc":"用户多了20积分,无冻结时间"
}'

# order_pay
# user_login
# share_goods
# register
# order_pay
# order_pay
# campaign
# campaign
# invite_new

# 积分累加通过事件
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/crm/points/10080/produce/by_rule' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "event_no": "EACH20220704173134352101975156",
    "member_no": "M220701534161771542",
    "action_scene": "user_login",
    "event_type":"event",
    "store_code": "ec_mini",
    "operator":"不语",
    "event_desc":"不语登录了系统"
}'

# 积分消耗指定积分值
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/crm/points/10080/consume/direct' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "event_no": "EACH20220615202826397549953504",
    "member_no": "ec_18165fd7455_JGhyfyLmX",
    "action_scene": "user_discount",
    "points": 10,
    "event_at": "2022-06-15 18:00:00",
    "store_code": "ec_mall",
    "cost_center": "cost_center001",
    "campaign_code": "618",
    "operator":"积分商城",
    "event_desc":"用户消耗了10个积分"
}'

# 转赠积分 通过积分值
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/crm/points/10080/transfer' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "transfer_no": "EACH20220615202826397549953505",
    "from_user": "ec_18165fd7455_JGhyfyLmX",
    "to_user": "mc_18165fd7455_JGhyfyLm2",
    "trans_type":"by_poins",
    "points": 10
}'

# 领取积分
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/crm/points/10080/accept' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "transfer_no": "EACH20220615202826397549953505",
    "member_no": "mc_18165fd7455_JGhyfyLm2"
}'

# 冲正反累加 完全冲正
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/crm/points/10080/reverse/produce' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "event_no": "20220615202826397549953507",
    "member_no": "ec_18165fd7455_JGhyfyLmX",
    "origin_event_no":"EACH20220615202826397549953506",
    "allow_negative": false
}'

# 冲正反累加 完全冲正 原事件30积分 冲正10积分
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/crm/points/10080/reverse/produce' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "event_no": "20220615202826397549953509",
    "member_no": "ec_18165fd7455_JGhyfyLmX",
    "origin_event_no":"20220615202826397549953508",
    "allow_negative": false,
    "reverse_points": 10
}'

# 冲正反扣减 完全冲正 原事件消费10积分 冲正10积分
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/crm/points/10080/reverse/consume' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "event_no": "20220615202826397549953512",
    "member_no": "ec_18165fd7455_JGhyfyLmX",
    "origin_event_no":"20220615202826397549953511"
}'

# 冲正反扣减 部分冲正 原事件消耗30积分， 冲正20积分
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/crm/points/10080/reverse/consume' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "event_no": "20220615202826397549953514",
    "member_no": "ec_18165fd7455_JGhyfyLmX",
    "origin_event_no":"20220615202826397549953513",
    "reverse_points":20
}'

# 积分历史明细
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/crm/points/10080/history' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "search_type":"produce",
    "start_time":"2022-06-01 12:00:00",
    "end_time":"2022-07-01 12:00:00",
    "member_no":"ec_18165fd7455_JGhyfyLmX"
}' 