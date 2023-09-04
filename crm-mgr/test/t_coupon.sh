#!/bin/bash
# 创建卡券自制券

# "/api/crm/mgr/card/<crm_id>/create ==(POST)==> bp_card.wrapper"
curl --location --request POST --X POST 'http://127.0.0.1:21200/api/crm/mgr/card/10080/create' \
--header 'Content-Type: application/json' \
--data '{
	"jump_path": "",
	"title": "测试额度卡",
	"subtitle": "测试额度卡",
	"get_limit": 100,
	"notice": "使用说明",
	"rule": "使用说明",
	"card_type": 0,
	"cash_condition": 100,
	"qty_condition": "",
	"cash_amount": 1,
	"date_type": 1,
	"total_quantity": 1000,
	"biz_type": "normal",
	"source": 1,
	"begin_time": "2022-11-01 00:00:00",
	"end_time": "2022-11-25 23:59:59",
	"interests_type": 1,
	"interests_amount": 1000000,
	"interests_period_type": 3,
	"interests_period_amount": 2000
}'

# 查看卡券列表
curl 'http://127.0.0.1:21200/api/crm/mgr/card/10080/list?language=cn&page=1&page_size=20&keyword=AJ3R3Q5CTEZN4DHY9TZATH&source=1'


# 查看卡券详情
curl 'http://127.0.0.1:21200/api/crm/mgr/card/10080/detail?language=cn&card_id=AJ3R3Q5CTEZN4DHY9TZATH'

# 修改卡券
curl --location --request POST --X POST 'http://127.0.0.1:21200/api/crm/mgr/card/10080/update' \
--header 'Content-Type: application/json' \
--data '{
	"title": "测试额度卡1",
	"subtitle": "测试额度卡2",
	"notice": "使用说明3",
	"rule": "使用说明4",
	"source": 1,
	"jump_path": "",
	"home_name": "",
	"bg_color": "",
	"begin_time": "2022-11-01 00:00:00",
	"end_time": "2022-11-25 23:59:59",
	"card_id": "AJ3R3Q5CTEZN4DHY9TZATH",
	"extra_info": {
    "bg_color": "",
    "miniapp_info": {
      "jump_path": "",
      "home_path": null,
      "home_name": "",
      "appid": "wx71031dea78e9d57b"
    }
  }
}'
