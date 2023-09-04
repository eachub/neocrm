
# 会员注册 微信平台
curl --location --request POST 'http://127.0.0.1:21100/api/crm/member/10080/register' \
--header 'Content-Type: application/json' \
--data-raw '{
    "mobile": "18182557482",
    "birthday": "2005-01-30",
    "nickname": "笑而不语",
    "province":"河南",
    "city":"郑州",
    "avatar":"123",
    "gender": 1,
    "source": {
        "channel_code": "mini_program",
        "ip": "194.16.184.53",
        "campaign_code": "招新活动",
        "appid": "wx332340823dfjd",
        "path":"/index/login",
        "invite_code":"inviter_code333"
    },
    "geo_origin_from": "1",
    "platform": "wechat",
    "user_info": {
        "appid":"wx332340823dfjd",
        "openId": "OPENID",
        "nickName": "笑而不语",
        "gender": 1,
        "city": "郑州",
        "province": "河南",
        "country": "中国",
        "avatarUrl": "http://...",
        "unionId": "UNIONID"
    }
}'

# 会员注册 天猫平台


# 绑定查询 用户可以注册
curl --location --request POST 'http://127.0.0.1:21100/api/crm/member/10080/bind_query' \
--header 'Content-Type: application/json' \
--data-raw '{
    "mobile": "18666073632",
    "member_no": "adipisicing deserunt aliquip sed officia",
    "platform": "wechat",
    "platform_info": {
        "unionid": "unionid1001",
    }
}'

# 绑定查询 用户不能注册不能绑定
curl --location --request POST 'http://127.0.0.1:21100/api/crm/member/10080/bind_query' \
--header 'Content-Type: application/json' \
--data-raw '{
    "mobile": "18666073632",
    "platform": "wechat"
}'

# 用户可以绑定
curl --location --request POST 'http://127.0.0.1:21100/api/crm/member/10080/bind_query' \
--header 'Content-Type: application/json' \
--data-raw '{
    "mobile": "18182557482",
    "platform": "douyin",
    "platform_info": {
    }
}'

# 平台会员绑定
curl --location --request POST 'http://127.0.0.1:21100/api/crm/member/10080/member_bind' \
--header 'Content-Type: application/json' \
--data-raw '{
    "member_no": "M220627-936388997698",
    "platform": "douyin",
    "user_info": {
        "appid": "dy0fdsjfk00jdkfj",
        "openId": "dy_openId123xzdf",
        "nickName": "张二分",
        "gender": 1,
        "country": "中国",
        "province":"河南",
        "city": "郑州",
        "avatarUrl": "123"
    }
}'

# 完善会员信息
curl --location --request POST 'http://127.0.0.1:21100/api/crm/member/10080/update' \
--header 'Content-Type: application/json' \
--data-raw '{
    "member_no": "M220627-936388997698",
    "nickname": "sunday",
    "avatarUrl": "123",
    "province": "上海",
    "city": "上海",
    "birthday": "1980-01-02",
    "gender": 2,
    "hobby": ["篮球1","读书"],
    "email": "f.nfrc@qq.com",
    "occupation": "学生",
    "address": "香港特别行政区 香港岛 中西区"
}'

# 家庭组添加
curl --location --request POST 'http://127.0.0.1:21100/api/crm/member/10080/family/add' \
--header 'Content-Type: application/json' \
--data-raw '{
    "member_no": "M220627-936388997698",
    "nickname": "邵强",
    "avatarUrl": "http://dummyimage.com/88x31",
    "gender": 1,
    "birthday": "2021-02-18",
    "relationship": "sun",
    "occupation": "工程师"
}'

# 家庭组修改
curl --location --request POST 'http://127.0.0.1:21100/api/crm/member/10080/family/update' \
--header 'Content-Type: application/json' \
--data-raw '{
    "family_uid": 4,
    "nickname": "王小丽",
    "birthday": "1997-05-22",
    "relationship": "sun",
    "occupation": "工程师"
}'

# 家庭组删除
curl --location --request POST 'http://127.0.0.1:21100/api/crm/member/10080/family/lot_delete' \
--header 'Content-Type: application/json' \
--data-raw '{
    "member_no": "M220627-936388997698",
    "family_uid_li": [
        5
    ]
}'

# 家庭组查看
curl --location --request POST 'http://127.0.0.1:21100/api/crm/member/10080/family/query' \
--header 'User-Agent: apifox/1.0.0 (https://www.apifox.cn)' \
--header 'Content-Type: application/json' \
--data-raw '{
    "member_no": "M220627-936388997698"
}'

# 查看会员信息
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/crm/member/10080/detail' \
--header 'Content-Type: application/json' \
--data '{
    "member_no":"M220701534161771542"
}'