## 1. 活动发行

### 1.1 创建新活动
   + 入口：/campaign/{instance_id}/create
   + 请求：POST
   + 入参：json包体
字段|类型|必填|取值样例|说明
---|---|---|---|---
campaign_name|string|是|情人节活动|活动名称
campaign_type|int|是|101|活动类型：101：资源包签到活动,102：资源包抽奖活动,103：资源包发券页活动, 104：后台任务商品任务, 105：后台任务会员生日
begin_time|int|是|'2022-07-01 00:00:00'|开始时间
end_time|int|是|'2022-09-01 00:00:00'|结束时间
detail|object|否|{}|活动详细配置，按照campaign_type取值字段不同，如下表
campaign_path|String|否|/material/2022-02-21/uuid.zip|资源包路径
desc|String|否|描述|描述
status|int|不填|0|活动状态，0，暂停，1，运行中，2，删除，3，活动尚未开始或者已经结束(实时判断)


   + 示例：
```
curl "https://dev.quickshark.cn/api/crm/mgr/cam/campaign/create" -d '
{
    "campaign_name": "情人节活动",
    "campaign_type": 101,
    "begin_time": "2022-07-01 00:00:00",
    "end_time": "2022-09-01 00:00:00",
    "detail": {"digital_id":680000, "name": "我的第2个藏品", "area_codes":["210020","210030"], "hit": 0.001, "times":3, "days": 1},
    "campaign_path": "https://dev.quickshark.cn/"
}
'
```

### 1.2 修改活动
   + 入口：/campaign/{instance_id}/update
   + 请求：POST
   + 入参：json包体
字段|类型|必填|取值样例|说明
---|---|---|---|---
campaign_id|int|是|1|活动ID
campaign_name|string|是|情人节活动|活动名称
begin_time|int|是|'2022-07-01 00:00:00'|开始时间
end_time|int|是|'2022-09-01 00:00:00'|结束时间
detail|object|否|{}|活动详细配置，按照campaign_type取值字段不同，如下表
campaign_path|String|否|/material/2022-02-21/uuid.zip|资源包路径
status|int|否|0|活动状态，0，暂停，1，运行中，2，删除，3，活动尚未开始或者已经结束(实时判断)

   + 示例：
```
curl "https://dev.quickshark.cn/api/crm/mgr/cam/campaign/update" -d '
{
    "campaign_id":60001,
    "campaign_name": "情人节活动123",
    "begin_time": "2022-07-01 00:00:00",
    "end_time": "2022-09-01 00:00:00",
    "detail": {"digital_id":680000, "name": "我的第2个藏品", "area_codes":["210020","210030"], "hit": 0.001, "times":3, "days": 1},
    "campaign_path": "https://dev.eachub.cn/cdn_file/cms/2022-07-24/view/8661fa25-a878-4663-b42f-6561a1987fa4/project/index.html"
    "status": 0
}
'
```
> 【101-资源包签到活动】详细配置，详细待补充
字段|类型|必填|取值样例|说明
---|---|---|---|---

### 1.3 删除活动
   + 入口：/campaign/{instance_id}/remove
   + 请求：POST
   + 示例：
```
# 单个活动
curl "https://dev.quickshark.cn/api/crm/mgr/cam/campaign/remove" -d '
{
  "campaign_id": 50001
}
# 多个活动
curl -d '{"campaign_ids":[60012]}' "https://dev.quickshark.cn/api/crm/mgr/cam/campaign/remove"
'
```

### 1.4 搜索活动列表
   + 入口：/campaign/{instance_id}/search
   + 请求：GET
   + 入参：
字段|类型|必填|取值样例|说明
---|---|---|---|---
keyword|String|否|藏品|数字产品关键字
campaign_ids|array|否|campaign_ids=60001&campaign_ids=60002|活动数组
campaign_type|array|否|campaign_type=101&campaign_type=102|活动类型数组
   + 示例：
```
curl "https://dev.quickshark.cn/api/crm/mgr/cam/campaign/search?keyword=情人节&campaign_type=101&campaign_type=102"
```

### 1.5 读取活动详情
   + 入口：/campaign/{instance_id}/fetch
   + 请求：GET
   + 示例：
``` bash
curl "https://dev.quickshark.cn/api/crm/mgr/cam/campaign/fetch?campaign_id=60001"
```
### 1.6 读取活动日历
   + 入口：/calendar/{instance_id}/month
   + 请求：GET
   + 示例：
``` bash
curl "https://dev.quickshark.cn/api/crm/mgr/cam/calendar/month?year=2022&month=07"
```

   + 返回包体：
```json
{
	"code": 0,
	"msg": "ok",
	"data": [{
		"campaign_id": 60018,
		"campaign_name": "会员日测试",
		"campaign_type": 103,
		"begin_time": "2022-07-22 00:00:00",
		"end_time": "2022-08-07 00:00:00",
		"create_time": "2022-07-22 18:33:47",
		"detail": null,
		"source_type": 1,
		"activity_id": 60018,
		"activity_name": "会员日测试",
		"activity_begin_time": "2022-07-22 00:00:00",
		"activity_end_time": "2022-08-07 00:00:00",
		"activity_type": 103
	}]
}
```

### 1.7 查询活动日志列表
   + 入口：/campaign/{instance_id}/list
   + 请求：POST
   + 示例：
``` bash
curl  "https://dev.quickshark.cn/mn/api/cam/mgr/campaign/common/list"  -d '
{
    "member_no":"M220704308572703018",
    "create_start": "2022-07-20 00:00:00",
    "create_end": "2022-08-20 00:00:00",
    "page_size":5,
    "page_id":1,
    "order_by": "create_time",
    "order_asc": 1
}
'

curl  "https://dev.quickshark.cn/mn/api/cam/mgr/campaign/common/list"  -d '
{
    "update_start": "2022-07-20 00:00:00",
    "update_end": "2022-08-20 00:00:00"
}
'


curl  "https://dev.quickshark.cn/mn/api/cam/mgr/campaign/common/list"  -d '
{
    "member_no":"M220704308572703018"
}
'
```

   + 返回包体：
```json
{
	"code": 0,
	"msg": "OK",
	"data": {
		"items": [{
			"auto_id": 7,
			"campaign_id": 60011,
			"member_no": "M220704308572703021",
			"instance_id": "neo_instance_id",
			"campaign_type": 103,
			"event_type": "2",
			"prize_conf": "{\"coupon_type\":1,\"coupon_list\":[\"JEDTGWYYZ7BNKJB765FKOG\",\"8WM55SLEJWSEMSQRFKWQ9T\"]}",
			"utm_source": null,
			"create_time": "2022-07-25 00:13:31",
			"update_time": "2022-07-25 00:13:31"
		}],
		"total": 8
	}
}
```

## 2. 活动分析

### 2.1地区城市排行

- 请求 POST /api/cam/mgr/panel/{instance_id}/region_top

- 请求参数 

| 参数          | 类型     | 必须  | 说明        |
|-------------|--------|-----|-----------|
| from_date   | string | 是   |           |
| to_date     | string | 是   |           |
| activity_id | int    | 是   |           |
| types       | int    | 是   | 1省份 2城市排行 |


- 请求例子

```shell
curl --location --request POST --X POST 'http://127.0.0.1:21500/api/cam/mgr/panel/neo_instance_id/region_top' \
--header 'Content-Type: application/json' \
--data '{
    "from_date":"2022-07-20",
    "to_date":"2022-07-26",
    "activity_id":"60010",
    "types": 2
}'
```

- 返回结果

```json
{
	"code": 0,
	"data": [
		{
			"name": "哈尔滨",
			"value": 125
		},
		{
			"name": "成都",
			"value": 120
		}
	],
	"msg": "处理成功"
}
```