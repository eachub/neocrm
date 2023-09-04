# 会员列表
curl --location --request POST --X POST 'http://127.0.0.1:21200/api/crm/mgr/member/10080/list' \
--header 'Content-Type: application/json' \
--data '{
    "mobile":"",
    "member_no":"",
    "create_start": "2022-06-01 12:00:00",
    "create_end": "2022-06-30 12:00:00",
    "order_by": "create_time",
    "order_asc": 0,
    "page_id":1,
    "page_size":10
}'

#  渠道类型数据
curl --location --request GET --X GET 'http://127.0.0.1:21200/api/crm/mgr/10080/channel_types'

# 注册渠道添加
curl --location --request POST --X POST 'http://127.0.0.1:21200/api/crm/mgr/member/10080/channel/add' \
--header 'Content-Type: application/json' \
--data '{
	"channel_types": [
		{
			"type_id": 1,
			"parent_id": 0,
			"name": "线上渠道",
			"children": [
				{
					"type_id": 5,
					"parent_id": 1,
					"name": "微信",
					"children": [
						{
							"type_id": 9,
							"parent_id": 5,
							"name": "朋友圈广告"
						}
					]
				}
			]
		}
	],
	"channel_name": "渠道名称1"
}'

# 注册渠道数据修改

curl --location --request POST --X POST 'http://127.0.0.1:21200/api/crm/mgr/member/10080/channel/update' \
--header 'Content-Type: application/json' \
--data '{
    "channel_id": 100000,
    "channel_name":"618活动推广"
}'

# 注册渠道数据删除
curl --location --request POST --X POST 'http://127.0.0.1:21200/api/crm/mgr/member/10080/channel/delete' \
--header 'Content-Type: application/json' \
--data '{
    "channel_id": 100000
}'

#  积分分析 汇总数据
curl --location --request GET --X GET 'http://127.0.0.1:21200/api/crm/mgr/analyze/10080/member/total?dr=2022-06-15~2022-07-01' \
--header 'Content-Type: application/json' 

# 积分分析趋势
