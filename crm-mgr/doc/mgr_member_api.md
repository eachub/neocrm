## /eros_crm/会员模块/后台会员列表


#### POST /api/crm/mgr/member/10080/list

#### 请求Body参数

```javascript
{
    "mobile":"",
    "member_no":"",
    "create_start": "2022-06-01 12:00:00",
    "create_end": "2022-06-30 12:00:00",
    "order_by": "create_time",
    "order_asc": 0,
    "page_id":1,
    "page_size":10
}
```

| 参数名          | 示例值                 | 参数类型   | 是否必填 | 参数描述                         |
|--------------|---------------------|--------|------|------------------------------|
| mobile       | -                   | Object | 否    | 手机号码                         |
| member_no    | -                   | Object | 否    | 会员名                          |
| create_start | 2022-06-01 12:00:00 | String | 否    | 注册开始时间                       |
| create_end   | 2022-06-15 12:00:00 | String | 否    | 注册结束时间                       |
| update_start | 2022-06-15 12:00:00 | String | 否    | 注册结束时间                       |
| update_end   | 2022-06-15 12:00:00 | String | 否    | 注册结束时间                       |
| order_by     | create_time         | String | 否    | 排序 默认create_time update_time |
| order_asc    | -                   | Number | 否    | 0倒叙 默认0                      |
| page_id      | 1                   | Number | 否    | 默认1                          |
| page_size    | 10                  | Number | 否    | 默认10                         |
| nickname     | 10                  | String | 否    | 昵称精准搜索                       |

#### 成功响应示例

```javascript
{
	"code": 0,
	"msg": "OK",
	"data": {
		"items": [
			{
				"member_no": "M220627-936388997698",
				"member_name": "笑而不语",
				"member_status": 5,
				"avatar": "123",
				"active_points": null,
				"birthday": "1980-01-02",
				"occupation": null,
				"create_time": "2022-06-27 14:07:56",
				"family": [
					{
						"family_uid": 3,
						"crm_id": "10080",
						"member_no": "M220627-936388997698",
						"nickname": "",
						"gender": 1,
						"avatar": null,
						"birthday": "2021-02-18",
						"relationship": 2,
						"occupation": "工程师",
						"status": 0,
						"create_time": "2022-06-27 23:17:57",
						"update_time": "2022-06-29 20:17:46"
					}
				]
			},
			{
				"member_no": "M220627-936388997698",
				"member_name": "笑而不语",
				"member_status": 5,
				"avatar": "123",
				"active_points": null,
				"birthday": "1980-01-02",
				"occupation": "学生",
				"create_time": "2022-06-27 14:07:56",
				"family": [
					{
						"family_uid": 3,
						"crm_id": "10080",
						"member_no": "M220627-936388997698",
						"nickname": "",
						"gender": 1,
						"avatar": null,
						"birthday": "2021-02-18",
						"relationship": 2,
						"occupation": "工程师",
						"status": 0,
						"create_time": "2022-06-27 23:17:57",
						"update_time": "2022-06-29 20:17:46"
					}
				]
			},
			{
				"member_no": "ec_18165fd7455_JGhyfyLmX",
				"member_name": "造梦师",
				"member_status": 1,
				"avatar": "123",
				"active_points": 40,
				"birthday": "1995-10-13",
				"occupation": null,
				"create_time": "2022-06-27 13:45:22"
			},
			{
				"member_no": "mc_18165fd7455_JGhyfyLm2",
				"member_name": "造梦师2",
				"member_status": 1,
				"avatar": "123",
				"active_points": 10,
				"birthday": "1995-10-13",
				"occupation": null,
				"create_time": "2022-06-27 13:45:22"
			}
		],
		"total": 4
	}
}
```

| 参数名                            | 示例值                  | 参数类型   | 参数描述                  |
|--------------------------------|----------------------|--------|-----------------------|
| code                           | -                    | Number |                       |
| msg                            | OK                   | String | 返回文字描述                |
| data                           | -                    | Object | 返回数据                  |
| data.items                     | -                    | Object |                       |
| data.items.member_no           | M220627-936388997698 | String | 会员名                   |
| data.items.member_name         | 笑而不语                 | String |                       |
| data.items.member_status       | 5                    | Number |                       |
| data.items.avatar              | 123                  | String |                       |
| data.items.active_points       | -                    | Object |                       |
| data.items.birthday            | 1980-01-02           | String | 生日                    |
| data.items.occupation          | -                    | Object | 职业                    |
| data.items.create_time         | 2022-06-27 14:07:56  | String |                       |
| data.items.family              | -                    | Object |                       |
| data.items.family.family_uid   | 3                    | Number |                       |
| data.items.family.crm_id       | 10080                | String |                       |
| data.items.family.member_no    | M220627-936388997698 | String | 会员名                   |
| data.items.family.nickname     | -                    | Object | 家庭组成员昵称               |
| data.items.family.gender       | 1                    | Number | 性别1男2女3其他             |
| data.items.family.avatar       | -                    | Object |                       |
| data.items.family.birthday     | 2021-02-18           | String | 生日                    |
| data.items.family.relationship | 2                    | Number | 角色1自己2父亲3母亲4配偶5孩子6其他人 |
| data.items.family.occupation   | 工程师                  | String | 职业                    |
| data.items.family.status       | -                    | Number |                       |
| data.items.family.create_time  | 2022-06-27 23:17:57  | String |                       |
| data.items.family.update_time  | 2022-06-29 20:17:46  | String |                       |
| data.total                     | 4                    | Number | 总数                    |

## 渠道类型数据获取

- GET /api/crm/mgr/member/{crm_id}/channel_types
- 请求  路径参数 crm_id=10080
- 返回结果


```json
{
	"code": 0,
	"msg": "OK",
	"data": [
		{
			"id": 1,
			"crm_id": "10080",
			"name": "线上渠道",
			"parent_id": 0,
			"create_time": "2022-06-30 15:25:57",
			"update_time": "2022-06-30 15:25:57",
			"children": [
				{
					"id": 4,
					"crm_id": "10080",
					"name": "微博",
					"parent_id": 1,
					"create_time": "2022-06-30 15:25:57",
					"update_time": "2022-06-30 15:25:57"
				},
				{
					"id": 5,
					"crm_id": "10080",
					"name": "微信",
					"parent_id": 1,
					"create_time": "2022-06-30 15:25:57",
					"update_time": "2022-06-30 15:25:57",
					"children": [
						{
							"id": 9,
							"crm_id": "10080",
							"name": "朋友圈广告",
							"parent_id": 5,
							"create_time": "2022-06-30 15:25:57",
							"update_time": "2022-06-30 15:25:57"
						}
					]
				}
				
			]
		},
		{
			"id": 2,
			"crm_id": "10080",
			"name": "线下渠道",
			"parent_id": 0,
			"create_time": "2022-06-30 15:25:57",
			"update_time": "2022-06-30 15:25:57"
		},
		{
			"id": 3,
			"crm_id": "10080",
			"name": "品牌合作",
			"parent_id": 0,
			"create_time": "2022-06-30 15:25:57",
			"update_time": "2022-06-30 15:25:57"
		}
	]
}
```

## /eros_crm/后台管理/会员模块/注册渠道添加


#### 接口URL
> 127.0.0.1:21200/api/crm/mgr/member/10080/channel/add

#### 请求方式
> POST

#### Content-Type
> application/json

#### 请求Body参数
```javascript
{
	"channel_type": [1,5,9],
	"channel_name": "双11引流2"
}
```
参数名 | 示例值 | 参数类型   | 是否必填 | 参数描述
--- | --- |--------| --- | ---
channel_type | - | array  | 是 | 渠道id列表 从父级别到子级别
channel_name | 渠道名称1 | String | 是 | 渠道名称
#### 预执行脚本
```javascript
暂无预执行脚本
```
#### 后执行脚本
```javascript
暂无后执行脚本
```
#### 成功响应示例
```javascript
{
	"code": 0,
	"msg": "保存成功"
}
```
## /eros_crm/后台管理/会员模块/渠道列表页面
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> 127.0.0.1:21200/api/crm/mgr/member/10080/channel/list

#### 请求方式
> POST

#### Content-Type
> application/json

#### 请求Body参数
```javascript
{
    "keyword": "渠道",
    "page_id":1,
    "page_size":10,
    "order_by":  "update_time",
    "order_asc": 0
}
```
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
keyword | 渠道 | String | 是 | 搜索关键词
page_id | 1 | Number | 是 | 默认1
page_size | 10 | Number | 是 | 默认10
order_by | update_time | String | 是 | 排序 默认create_time
order_asc | - | Number | 是 | 0倒序 默认0 1正序
#### 预执行脚本
```javascript
暂无预执行脚本
```
#### 后执行脚本
```javascript
暂无后执行脚本
```
#### 成功响应示例
```javascript
{
	"code": 0,
	"msg": "OK",
	"data": {
		"items": [
			{
				"channel_id": 100000,
				"crm_id": "10080",
				"channel_name": "渠道名称1",
				"channel_code": null,
				"channel_type": "线上渠道,微信,朋友圈广告",
				"desc": null,
				"create_time": "2022-06-30 18:56:47",
				"update_time": "2022-06-30 18:56:47"
			}
		],
		"total": 1
	}
}
```
## /eros_crm/后台管理/会员模块/注册渠道修改
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> 127.0.0.1:21200/api/crm/mgr/member/10080/channel/update

#### 请求方式
> POST

#### Content-Type
> json

#### 请求Body参数
```javascript
{
    "channel_id": 100000,
    // "channel_type":[],
    "channel_name":"618活动推广"
}
```
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
channel_id | 100000 | Number | 是 | 渠道id
channel_name | 618活动推广 | String | 否 | 渠道名称
channel_type | - | Object | 否 | 渠道类型

#### 成功响应示例
```javascript
{
	"code": 0,
	"msg": "更新成功"
}
```
## /eros_crm/后台管理/会员模块/注册渠道删除

#### 接口URL
> 127.0.0.1:21200/api/crm/mgr/member/10080/channel/delete

#### 请求方式
> POST

#### Content-Type
> json

#### 请求Body参数
```javascript
{
    "channel_id": 100000
}
```
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
channel_id | 100000 | Number | 是 | 渠道id
#### 成功响应示例
```javascript
{
	"code": 0,
	"msg": "删除成功"
}
```

## /eros_crm/后台管理/会员分析/会员分析导出


#### 接口URL
> 127.0.0.1:21100/api/crm/mgr/analyze/10080/member/export?dr=2022-06-15~2022-07-01

#### 请求方式
> GET


#### 请求Query参数
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
dr | 2022-06-15~2022-07-01 | Text | 是 | 时间范围 ～连接

#### 成功响应示例
```javascript
{
	"code": 0,
	"msg": "OK",
	"data": {
		"result": [
			{
				"label": null,
				"item": "inviter_code333",
				"counts": 2
			},
			{
				"label": null,
				"item": "",
				"counts": 1
			}
		],
		"crm_id": "10080",
		"from_date": "2022-06-15",
		"to_date": "2022-07-01"
	}
}
```
## /eros_crm/后台管理/会员分析/会员分析趋势数据

#### 接口URL
> 127.0.0.1:21100/api/crm/mgr/analyze/10080/member/trend?dr=2022-06-15~2022-07-01

#### 请求方式
> GET


#### 请求Query参数
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
dr | 2022-06-15~2022-07-01 | Text | 是 | 时间范围 ～连接


#### 成功响应示例
```javascript
{
	"code": 0,
	"msg": "OK",
	"data": {
		"new_user": [
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0
		],
		"cumulate_user": [
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0
		],
		"rece_card_user": [
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0
		],
		"cumulate_rece_card_user": [
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0,
			0
		],
		"tdate": [
			"2022-06-15",
			"2022-06-16",
			"2022-06-17",
			"2022-06-18",
			"2022-06-19",
			"2022-06-20",
			"2022-06-21",
			"2022-06-22",
			"2022-06-23",
			"2022-06-24",
			"2022-06-25",
			"2022-06-26",
			"2022-06-27",
			"2022-06-28",
			"2022-06-29",
			"2022-06-30",
			"2022-07-01"
		],
		"mode": "by_day"
	}
}
```
## /eros_crm/后台管理/会员分析/会员分析分布数据

#### 接口URL
> 127.0.0.1:21100/api/crm/mgr/analyze/10080/member/distr?dr=2022-06-15~2022-07-01&types=mp_source

#### 请求方式
> GET


#### 请求Query参数
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
dr | 2022-06-15~2022-07-01 | Text | 是 | 时间范围 ～连接
types | mp_source | Text | 是 | channel 渠道 mp_source 来源小程序 scene场景

#### 成功响应示例
```javascript
{
	"code": 0,
	"msg": "OK",
	"data": {
		"result": [
			{
				"label": "0",
				"item": "0",
				"counts": 1
			},
			{
				"label": "mini_program",
				"item": "mini_program",
				"counts": 2
			}
		],
		"crm_id": "10080",
		"from_date": "2022-06-15",
		"to_date": "2022-07-01"
	}
}
```
## /eros_crm/后台管理/会员分析/会员分析排行数据


#### 接口URL
> 127.0.0.1:21100/api/crm/mgr/analyze/10080/member/top?dr=2022-06-15~2022-07-01

#### 请求方式
> GET


#### 请求Query参数
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
dr | 2022-06-15~2022-07-01 | Text | 是 | 时间范围 ～连接

#### 成功响应示例
```javascript
{
	"code": 0,
	"msg": "OK",
	"data": {
		"result": [
			{
				"label": null,
				"item": "inviter_code333",
				"counts": 2
			},
			{
				"label": null,
				"item": "",
				"counts": 1
			}
		],
		"crm_id": "10080",
		"from_date": "2022-06-15",
		"to_date": "2022-07-01"
	}
}
```
## /eros_crm/后台管理/会员分析/会员分析汇总数据


#### 接口URL
> 127.0.0.1:21100/api/crm/mgr/analyze/10080/member/total?dr=2022-06-15~2022-07-01

#### 请求方式
> GET


#### 请求Query参数
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
dr | 2022-06-15~2022-07-01 | Text | 是 | 时间范围 ～连接

#### 成功响应示例
```javascript
{
	"code": 0,
	"msg": "OK",
	"data": {
		"items": [
			{
				"label": "新增会员",
				"description": "时间范围内新增加的会员数",
				"value": 4,
				"indicator": "new_member"
			},
			{
				"label": "累积会员",
				"description": "结束时间累积的会员数",
				"value": 4,
				"indicator": "total_member"
			},
			{
				"label": "新增家庭成员",
				"description": "时间范围内新增的家庭成员数",
				"value": 4,
				"indicator": "new_family"
			},
			{
				"label": "累积家庭成员",
				"description": "结束时间累积的家庭成员数",
				"value": 4,
				"indicator": "total_family"
			}
		]
	}
}
```

## 后台管理/标签/标签树获取接口

- 请求 GET /api/crm/mgr/member/10080/tag/tree

- 请求例子

```shell
curl --location --request GET --X GET 'http://127.0.0.1:21100/api/crm/mgr/member/10080/tag/tree' \
--header 'Content-Type: application/json' \
--data ''
```
- 返回

```json
{
	"code": 0,
	"msg": "ok",
	"data": [
		{
			"tag_id": 200000,
			"parent_id": 0,
			"tag_name": "会员行为",
			"only_folder": true,
			"active": true,
			"build_in": 0,
			"children": [
				{
					"tag_id": 200005,
					"parent_id": 200000,
					"tag_name": "注册引流活动",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200006,
					"parent_id": 200000,
					"tag_name": "注册引流渠道",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200007,
					"parent_id": 200000,
					"tag_name": "积分变更行为",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				}
			]
		},
		{
			"tag_id": 200001,
			"parent_id": 0,
			"tag_name": "人口属性",
			"only_folder": true,
			"active": true,
			"build_in": 0,
			"children": [
				{
					"tag_id": 200008,
					"parent_id": 200001,
					"tag_name": "性别",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200009,
					"parent_id": 200001,
					"tag_name": "年龄",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200010,
					"parent_id": 200001,
					"tag_name": "生日",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200011,
					"parent_id": 200001,
					"tag_name": "会员等级",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200012,
					"parent_id": 200001,
					"tag_name": "会龄区间",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200013,
					"parent_id": 200001,
					"tag_name": "活跃状态",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200014,
					"parent_id": 200001,
					"tag_name": "家庭成员数量",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200015,
					"parent_id": 200001,
					"tag_name": "最近一次访问小程序出现的城市",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200016,
					"parent_id": 200001,
					"tag_name": "最近一次访问小程序出现的省份",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				}
			]
		},
		{
			"tag_id": 200002,
			"parent_id": 0,
			"tag_name": "消费习惯",
			"only_folder": true,
			"active": true,
			"build_in": 0,
			"children": [
				{
					"tag_id": 200017,
					"parent_id": 200002,
					"tag_name": "近期购买频次",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200018,
					"parent_id": 200002,
					"tag_name": "近期购买支付金额",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200019,
					"parent_id": 200002,
					"tag_name": "最近一次购买距今天数",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200020,
					"parent_id": 200002,
					"tag_name": "最近一次购买商品",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				}
			]
		},
		{
			"tag_id": 200003,
			"parent_id": 0,
			"tag_name": "商品偏好",
			"only_folder": true,
			"active": true,
			"build_in": 0,
			"children": [
				{
					"tag_id": 200021,
					"parent_id": 200003,
					"tag_name": "近期最近一次购买商品",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200022,
					"parent_id": 200003,
					"tag_name": "近期最多购买商品",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200023,
					"parent_id": 200003,
					"tag_name": "近期最近一次购买商品类目",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200024,
					"parent_id": 200003,
					"tag_name": "最近最多购买商品类目",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				}
			]
		},
		{
			"tag_id": 200004,
			"parent_id": 0,
			"tag_name": "营销偏好",
			"only_folder": true,
			"active": true,
			"build_in": 0,
			"children": [
				{
					"tag_id": 200025,
					"parent_id": 200004,
					"tag_name": "近期最近一次访问活动",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200026,
					"parent_id": 200004,
					"tag_name": "近期最多访问活动",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200027,
					"parent_id": 200004,
					"tag_name": "近期最近一次领取优惠券",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200028,
					"parent_id": 200004,
					"tag_name": "近期最多领取优惠券",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200029,
					"parent_id": 200004,
					"tag_name": "近期最近一次核销优惠券",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				},
				{
					"tag_id": 200030,
					"parent_id": 200004,
					"tag_name": "近期最多核小优惠券",
					"only_folder": false,
					"active": true,
					"build_in": 0,
					"levels": []
				}
			]
		}
	]
}

```

## 后台管理/标签/标签详情接口

- 请求 GET /api/crm/mgr/member/10080/tag/detail?tag_id=200005

- 请求例子

```shell
curl --location --request GET --X GET 'http://127.0.0.1:21100/api/crm/mgr/member/10080/tag/detail?tag_id=200008'
```
- 返回结果

```json5
{
	"code": 0,
	"msg": "ok",
	"data": {
		"tag_id": 200008,
		"parent_id": 200001,
		"tag_name": "性别",
		"only_folder": false,
		"bind_field": "tag_004",
		"renew_mode": 2,
		"define_mode": 2,
		"desc": [
			{
				"dataset": {
					"data_type": "attr",
					"data": [],
					"combo_mode": "any"
				},
				"text": "性别",
				"name": "gender"
			}
		],
		"active": true,
		"activate_at": "2022-07-06 18:36:47",
		"qty": {
			"member_no": 1265
		},
		"create_time": "2022-07-06 18:36:47",
		"update_time": "2022-07-08 10:14:35",
		"levels": [
			{
				"level_id": 600001,
				"level_name": "未知",
				"qty": {
					"member_no": 5
				}
			},
			{
				"level_id": 600002,
				"level_name": "男",
				"qty": {
					"member_no": 265
				}
			},
			{
				"level_id": 600003,
				"level_name": "女",
				"qty": {
					"member_no": 255
				}
			}
		]
	}
}
```

## 后台管理/标签/标签level配置接口

- 请求 POST /api/crm/mgr/member/10080/tag/level_update
- 请求参数


| 参数   | 示例     | 类型     | 必填  | 说明  |
|--------|--------|--------|-----|-----|
| tag_id | 200007 | int    | 是   |     |
|  desc    |        | object | 是   |  配置信息的描述 详情页返回的desc信息   |

- 请求例子

```shell
curl --location --request POST --X POST 'http://127.0.0.1:21200/api/crm/mgr/member/10080/tag/level_update' \
--data '{
    "tag_id": 200007,
   "desc": [
			{
				"text": "积分变更行为",
				"name": "积分变更行为",
				"dr": [90],
				"spans": [
					{
						"level_name": "低频积分获取",
						"value": [
							null,
							200
						],
						"name": "points",
						"text": "积分值",
						"dr": [
							90
						],
						"level_id": 6000833
					},
					{
						"level_name": "中频积分获取",
						"value": [
							200,
							500
						],
						"name": "points",
						"text": "积分值",
						"dr": [
							90
						],
						"level_id": 6000834
					},
					{
						"level_name": "高频积分获取",
						"value": [
							500,
							null
						],
						"name": "points",
						"text": "积分值",
						"dr": [
							90
						],
						"level_id": 6000835
					}
				]
			}
		],
}'

```
- 返回结果

```json
{
	"code": 0,
	"msg": "OK",
	"data": {
		"tag_id": 200007,
		"crm_id": "10080",
		"parent_id": 200000,
		"tag_name": "积分变更行为",
		"only_folder": false,
		"bind_field": "tag_003",
		"renew_mode": 2,
		"define_mode": 3,
		"desc": [
			{
				"text": "积分变更行为",
				"name": "积分变更行为",
				"dr": [
					90
				],
				"spans": [
					{
						"level_name": "低频积分获取",
						"value": [
							null,
							200
						],
						"name": "points",
						"text": "积分值",
						"dr": [
							90
						],
						"level_id": 6000833
					},
					{
						"level_name": "中频积分获取",
						"value": [
							200,
							500
						],
						"name": "points",
						"text": "积分值",
						"dr": [
							90
						],
						"level_id": 6000834
					},
					{
						"level_name": "高频积分获取",
						"value": [
							500,
							null
						],
						"name": "points",
						"text": "积分值",
						"dr": [
							90
						],
						"level_id": 6000835
					}
				]
			}
		]
	}
}

```

## 后台管理/标签/标签历史指标数据

- 请求 POST 
- 请求参数

| 参数名       | 示例                    | 类型     | 是否必填            | 说明  |
|-----------|-----------------------|--------|-----------------|-----|
| dr        | 2022-07-06~2022-07-15 | String | ～连接的时间          |     |
| tag_id    | 200008                | int    | 标签id            |     |
| level_ids | []                    | array  | 标签等级列表[]为所有标签等级 |     |

- 请求例子

```shell
curl --location --request POST --X POST 'http://127.0.0.1:21200/api/crm/mgr/analyze/10080/tags_qty_his' \
--header 'Content-Type: application/json' \
--data '{
    "dr": "2022-07-06~2022-07-15",
    "tag_id": 200008,
    "level_ids":[],

}'
```

- 返回结果

```json
{
	"code": 0,
	"msg": "OK",
	"data": {
		"6001784": [
			0,
			1,
			0
		],
		"6001785": [
			0,
			2,
			0
		],
		"6001786": [
			0,
			1,
			0
		],
		"tdate": [
			"2022-07-13",
			"2022-07-14",
			"2022-07-15"
		],
		"mode": "by_day",
		"headers": {
			"6001784": "未知",
			"6001785": "男",
			"6001786": "女"
		}
	}
}
```

## 适配层接口/会员360画像/会员行为
- 请求 GET /api/crm/mgr/adapt/member/10080/events 
- 请求参数

| 参数名       |   示例  | 类型   |  是否必填   |   说明  |
|-----------|-----|-----|-----|-----|
| member_no | M220704308572703018    |   String  |  是   |     |

请求例子
```shell
curl --location --request GET --X GET 'http://127.0.0.1:21300/api/crm/mgr/adapt/member/10080/events?member_no=M220704308572703018'
```
- 返回结果

```json
{
	"code": 0,
	"msg": "OK",
	"data": {
		"total": 3,
		"items": [
			{
				"event_id": 31,
				"event_time": 1628352100,
				"ip": null,
				"uuid": "61275c875e74f20c",
				"appid": "wx71031dea78e9d57b",
				"appver": null,
				"sdkver": null,
				"create_time": "2021-10-08 16:26:01",
				"openid": "1",
				"unionid": "61275c875e74f20c",
				"event_name": "加入购物车",
				"param": "{\"sku_code\":\"Z000030001\",\"qty\":5}"
			}
		]
	}
}
```

## 增量获取会员信息列表

- 请求 POST /api/crm/mgr/member/10080/info/increment
- 使用方：OMS/CDP等外部系统
- 请求参数
  - 通用参数
  
| 参数名        | 参数类型   | 参数解释                            | 是否必传 | 默认值 |
|------------|--------|---------------------------------|------|-----|
| page_id    | int    | 页码，取值从1开始                       | 是    |     |
| page_size  | int    | 每页数据量 默认是20 区间2-500             | 否    | 20  |
| order_by   | string | 排序字段 只支持create_time和update_time | 是    |     |
| order_asc  | int    | 升序: 0表示否  1表示是                  | 否    | 0   |
| time_start | int    | unix-timestamp                  | 是    |     |
| time_end   | int    | unix-timestamp                  | 是    |     |

- 返回结果

| 名称                            | 类型     | 空    | 说明     |
|-------------------------------|--------|------|--------|
| code                          | int    |      |        |
| msg                           | string |      |        |
| data                          | object |      |        |
| data.crm_id                   |        |      |        |
| data.page_id                  |        |      |        |
| data.page_size                |        |      |        |
| data.total                    |        |      |        |
| data.items                    |        |      |        |
| data.items.extend             | object | 扩展信息 | 扩展信息   |
| data.items.source             | object |      | 来源信息   |
| data.items.points             | object |      | 积分信息   |
| data.items.family             | array  |      | 家庭组信息  |
| data.items.wechat_member_info | object |      | 微信信息   |
| data.items.douyin_member_info | object |      | 抖音平台信息 |
| data.items.tmall_member_info  | object |      | 天猫平台信息 |

- 请求例子

```shell
curl --location --request POST --X POST 'http://127.0.0.1:21200/api/crm/mgr/member/10080/info/increment' \
--data '{
    "page_id":1,
    "page_size":10,
    "order_by":"update_time",
    "order_asc":0,
    "time_start":0,
    "time_end": 1657184919
}'

```

- 返回结果

```json
{
	"code": 0,
	"msg": "OK",
	"data": {
		"crm_id": 10080,
		"page_id": 1,
		"page_size": 10,
		"total": 4,
		"items": [
			{
				"crm_id": "10080",
				"member_no": "M220627-936388997698",
				"mobile": "18182557482",
				"platform": "wechat",
				"nickname": "笑而不语123",
				"level": "lv1",
				"avatar": "123",
				"province": "上海",
				"city": "上海",
				"birthday": "1980-01-02",
				"gender": 2,
				"member_status": 5,
				"invite_code": "NE181a3c61421xEsN",
				"create_time": "2022-06-27 14:07:56",
				"update_time": "2022-07-04 19:32:12",
				"extend": {
					"extend_id": 9,
					"crm_id": "10080",
					"member_no": "M220627-936388997698",
					"grow_score": 0,
					"ip": null,
					"order_amount": 0,
					"inviter": null,
					"address": null,
					"email": null,
					"occupation": null,
					"hobby": null,
					"tags": null,
					"extra": null,
					"create_time": "2022-07-04 19:32:12",
					"update_time": "2022-07-04 19:32:12"
				},
				"source": {
					"auto_id": 4,
					"crm_id": "10080",
					"member_no": "M220627-936388997698",
					"channel_code": "mini_program",
					"platform": "wechat",
					"campaign_code": "招新活动",
					"appid": "wx332340823dfjd",
					"path": "/index/login",
					"scene": null,
					"invite_code": "inviter_code333",
					"extra": {
						"ip": "194.16.184.53"
					},
					"create_time": "2022-06-27 14:07:56",
					"update_time": "2022-06-27 14:15:27"
				},
				"points": {
					"detail_id": 23,
					"crm_id": "10080",
					"member_no": "M220627-936388997698",
					"total_points": 40,
					"freeze_points": 20,
					"expired_points": 0,
					"active_points": 20,
					"used_points": 0,
					"future_expired": 0,
					"create_time": "2022-07-04 18:17:17",
					"update_time": "2022-07-05 15:27:37"
				},
				"family": [
					{
						"family_uid": 3,
						"crm_id": "10080",
						"member_no": "M220627-936388997698",
						"nickname": "",
						"gender": 1,
						"avatar": null,
						"birthday": "2021-02-18",
						"relationship": 2,
						"occupation": "工程师",
						"status": 0,
						"create_time": "2022-06-27 23:17:57",
						"update_time": "2022-06-29 20:17:46"
					},
					{
						"family_uid": 4,
						"crm_id": "10080",
						"member_no": "M220627-936388997698",
						"nickname": "王小丽",
						"gender": 2,
						"avatar": null,
						"birthday": "1997-05-22",
						"relationship": 2,
						"occupation": "工程师",
						"status": 0,
						"create_time": "2022-06-27 23:20:00",
						"update_time": "2022-06-29 20:17:46"
					}
				],
				"wechat_member_info": {
					"auto_id": 1,
					"crm_id": "10080",
					"member_no": "M220627-936388997698",
					"appid": "wx332340823dfjd",
					"unionid": "UNIONID",
					"openid": "OPENID",
					"card_code": null,
					"nickname": "笑而不语",
					"country": "中国",
					"province": "河南省",
					"city": "郑州市",
					"avatar": "http://...",
					"gender": 1,
					"status": 0,
					"extra": null,
					"create_time": "2022-06-27 14:07:56",
					"update_time": "2022-06-27 14:07:56"
				},
				"douyin_member_info": {
					"info_id": 1,
					"crm_id": "10080",
					"member_no": "M220627-936388997698",
					"appid": "dy0fdsjfk00jdkfj",
					"openid": "dy_openId123xzdf",
					"card_code": null,
					"nickname": "张二分",
					"country": "中国",
					"province": "河南",
					"city": "郑州",
					"gender": 1,
					"avatar": "123",
					"status": 0,
					"extra": {
						"language": null
					},
					"create_time": "2022-06-27 21:50:45",
					"update_time": "2022-06-27 21:50:45"
				}
			}
		]
	}
}

```

## unionid或openid批量获取会员号
- POST /api/crm/mgr/member/<crm_id>/fetch_member_nos

- 请求json
```json
{
  "unionid_li": [],
  "openid_li": []
}
```

- 请求例子 client.member.fetch_member_nos({"unionid_li"=[], crm_id=10080})

```shell
curl --location --request POST --X POST 'http://127.0.0.1:21200/api/crm/mgr/member/10080/fetch_member_nos' \
--data '{
    "unionid_li": ["og3dN5vVdAjnM8cHQqv-VRJUNMM0", "oAXn65mwyky_O9TAb6_sueMp7DgM"]
}'
```

- 返回结果

```json
{
	"code": 0,
	"msg": "OK",
	"data": [
		{
			"unionid": "oAXn65mwyky_O9TAb6_sueMp7DgM",
			"member_no": "M220803307210000853",
			"openid": "oGlFU5eIwj1GvguBU1gD8fa9q9X2"
		},
		{
			"unionid": "og3dN5vVdAjnM8cHQqv-VRJUNMM0",
			"member_no": "M220802735842357323",
			"openid": "oGlFU5RwUiTnLqMJDbvHzVzJCy3c"
		}
	]
}
```


# 会员相关

## 注销列表查看

- 请求 POST /api/crm/mgr/member/{crm_id}/cancel_list
- 请求参数

| 参数         | 类型     | 必填  | 说明                            |
|:-----------|:-------|:----|:------------------------------|
| mobile     | string | 否   |                               |
| member_no  | string | 否   |                               |
| page_id    | int    | 是   | 默认1                           |
| page_size  | int    | 是   | 默认20                          |
| start_time | string | 否   | 2022-08-30 17:32:43 注销日期的开始时间 |
| end_time   | string | 否   | 同上 注销日期结束时间                   |
| order_asc  | int    | 否   | 0 倒序 1正序  根据注销时间排序            |

- 请求例子
- 返回结果
```json
{
	"code": 0,
	"msg": "OK",
	"data": {
		"items": [
			{
				"info_id": 1,
				"crm_id": "mt000000000-neocrm",
				"mobile": "158*****797",
				"member_no": "M220823706644727909",
				"cancel_time": "2023-02-03 13:59:41",
				"status": 1,
				"extra": null,
				"update_time": "2023-02-03 13:59:41",
				"avatar": "https://thirdwx.qlogo.cn/mmopen/vi_32/Q0j4TwGTfTIykVsmj7PDjA0DVyibrSNSsEUINjPITp8bicIjRAkU8icMe6CB6SFgmS0hl07usMG7bBoSLcTWvCic6w/132",
				"nickname": "付杭"
			}
		],
		"total": 1
	}
}
```

## 移除注销会员
- 请求 POST /api/crm/mgr/member/{crm_id}/cancel_remove
- 请求参数 member_no

- 请求例子

```shell
curl --location --request POST --X POST 'http://dev.quickshark.cn/api/neocrm/mgr/member/cancel_remove' \
--header 'Content-Type: application/json' \
--data '{
    "member_no": "M220823706644727909"
}'
```

- 返回结果
```json
{
	"code": 0,
	"msg": "移除注销成功"
}
```

## 黑名单列表查看

- 请求 POST /api/crm/mgr/member/{crm_id}/black_list

- 请求参数

| 参数         | 类型     | 必填  | 说明                  |
|:-----------|:-------|:----|:--------------------|
| mobile     | string | 否   |                     |
| member_no  | string | 否   |                     |
| page_id    | int    | 是   | 默认1                 |
| page_size  | int    | 是   | 默认20                |
| start_time | string | 否   | 2022-08-30 17:32:43 |
| end_time   | string | 否   | 同上                  |
| order_asc  | int    | 否   | 0 倒序 1正序            |

- 请求例子

```shell
curl --location --request POST --X POST 'http://dev.quickshark.cn/api/neocrm/mgr/member/black_list' \
--header 'Content-Type: application/json' \
--data '{
    "page_id":1,
    "page_size":20
}'
```

> start_time:注销时间
> 黑名单的状态：status 1 仅黑名单 2冻结积分状态 3 冻结账户 

- 返回结果

```json5
{
	"code": 0,
	"msg": "OK",
	"data": {
		"items": [
			{
				"auto_id": 22,
				"crm_id": "mt000000000-neocrm",
				"member_no": "M230119060502xjSbYPCR",
				"block_days": 0,
				"start_time": "2023-01-19 11:14:15",
				"end_time": null,
				"status": 1,
				"desc": null,  // 加入原因
				"operator": null,
				"extra": null,
				"register_time": "2023-01-19 06:05:02",
				"create_time": "2023-01-19 11:14:14",  // 加入黑名单时间
				"update_time": "2023-01-19 11:14:14",
				"avatar": "https://files.catbox.moe/8y0q4h.png",
				"nickname": "曹莉",
				"mobile": "186*****459",
				"freeze_points": 0,  // 冻结积分
				"active_points": 38  // 可用积分
			}
		],
		"total": 1
	}
}
```

## 加入黑名单
- 请求 POST /api/crm/mgr/member/{crm_id}/v2/black_add

- 请求参数

| 参数        | 类型     | 必填  | 说明        |
|-----------|--------|-----|-----------|
| member_no | string | 否   | 会员号       |
| mobile    | string | 否   | 会员号手机号二选一 | 
| desc      | string | 是   | 加入原因      | 



## 黑名单移除
- 请求 POST /api/crm/mgr/member/{crm_id}/black_remove
- 请求参数 member_no

- 请求例子

```shell
curl --location --request POST --X POST 'http://dev.quickshark.cn/api/neocrm/mgr/member/black_remove' \
--header 'Content-Type: application/json' \
--data '{
    "member_no": "M220823706644727909"
}'
```

- 返回结果

```json
{
	"code": 0,
	"msg": "移除黑名单成功"
}
```


## 设置黑名单--冻结积分/账户/限制活动
- 请求 POST /api/crm/mgr/member/{crm_id}/freeze
- 请求参数 
- 
| 参数        | 类型     | 必填  | 说明                                                 |
|-----------|--------|-----|----------------------------------------------------|
| member_no | string | 是   | 会员号                                                |
| status    | string | 是   | 操作类型 1代表黑名单(解冻、取消限制)  2冻结积分 3冻结账户 4限制活动 （注：1234互斥） |

- 请求例子

```shell
curl --location --request POST --X POST 'http://dev.quickshark.cn/api/neocrm/mgr/member/freeze' \
--header 'Content-Type: application/json' \
--data '{
    "member_no": "M220823706644727909",
    "status": 3
}'
```

- 返回结果

```json
{
	"code": 0,
	"msg": "冻结成功"
}
```


## 设置黑名单阈值
- 请求POST /api/crm/mgr/member/{crm_id}/black_cfg_save
- 请求包体
```json5
{
  "neg_points_limit": 10, // 退单负积分值上限
  "neg_points_times": 3  // 退单负积分次数
}
```
- 返回 code=0 msg=ok

## 查看黑名单阈值

- 请求 GET /api/crm/mgr/member/{crm_id}/black_cfg
- 返回结果

```json
{
  "code": 0,
  "msg": "OK",
  "data": {
    "black_cfg": {
      "neg_points_limit": 10,
      "neg_points_times": 3 
    }
  }
}
```


# 分析接口

## 标签历史统计信息接口
- 请求POST /api/crm/mgr/analyze/{crm_id}/tags_qty_his

- 请求例子

```shell
curl --location --request POST --X POST 'https://dev.quickshark.cn/api/crm/mgr/analyze/tags_qty_his' \
--data '{"tag_id":200007,"level_ids":[6002275,6001781,6002276],"dr":"2022-07-08~2022-07-15"}'
```

- 返回结果

```json
{
	"code": 0,
	"msg": "OK",
	"data": {
		"items": [
			{
				"tdate": "2022-07-12",
				"desc": null,
				"level_6002275": 0,
				"level_6001781": 0,
				"level_6002276": 0
			},
			{
				"tdate": "2022-07-13",
				"desc": null,
				"level_6002275": 0,
				"level_6001781": 0,
				"level_6002276": 0
			},
			{
				"tdate": "2022-07-14",
				"desc": [
					{
						"dataset": {
							"data_type": "attr",
							"data": [],
							"combo_mode": "any"
						},
						"text": "积分变更行为",
						"name": "积分变更行为",
						"spans": [
                          {
                            "level_name": "低频积分获取1",
                            "value": [
                              null,
                              "250"
                            ],
                            "name": "points",
                            "text": "积分值",
                            "dr": [
                              180
                            ],
                            "level_id": 6001781,
                            "start_value": null,
                            "end_value": "250"
                          }
						],
						"dr": [
							90
						]
					}
				],
				"level_6002275": 0,
				"level_6001781": 1,
				"level_6002276": 0
			},
			{
				"tdate": "2022-07-15",
				"desc": null,
				"level_6002275": 0,
				"level_6001781": 0,
				"level_6002276": 0
			}
		],
		"mode": "by_day"
	}
}
```


# 等级和权益接口

## 后台管理/获取实例会员基础配置

- 请求 GET /api/crm/mgr/member/10080/member_config

- 返回结果


| 名称                  | 类型     | 空   | 说明       |
|---------------------|--------|-----|----------|
| code                | int    |     |          |
| msg                 | string |     |          |
| data                | object |     |          |
| data.points_config  | object |     | 积分配置信息   |
| data.level_config   | object |     | 实例等级配置信息 |
| data.benefit_config | object |     | 实例权益配置信息 |

- level_config具体字段解释

| 名称                      | 类型     | 说明                               |
|-------------------------|--------|----------------------------------|
| give_rules              | object | 赠送规则                             |
| give_rules.action       | string | 类型编码                             |
| give_rules.text         | string | 中文描述                             |
| give_rules.change_score | string | 改变的成长值                           |
| give_rules.type         | string | 类型 type=1 用户行为(下面多个)             |
| give_rules.range_days   | string | 时间范围，1 1天内最大成长值                  |
| give_rules.per_money    | string | 每多少元                             |
| give_rules.max_score    | string | 最大成长值                            |
| deduct_rules            | object | 扣减规则                             |
| deduct_rules.xxx        | object | 参考give_rules下面的字段解释              |
| downgrade               | object | 降级策略                             |
| downgrade.type          | string | 类型 0:所有等级统一规则 1各等级分别设计(等级配置信息生效) |
| downgrade.not_down      | bool   | true 不降级                         |
| downgrade.shoping_times | int    | 年消费次数                            |

- benefit_config 具体字段解释

| 名称                          | 类型     | 说明     |
|-----------------------------|--------|--------|
| benefit_config.benefit_code | string | 权益类型   |
| benefit_config.benefit_text | string | 权益类型中文 |

```json
{
	"code": 0,
	"msg": "OK",
	"data": {
		"points_config": {
			"produce_scene": [
				{
					"name": "用户登录",
					"code": "user_login",
					"rules_num": 1
				},
				{
					"name": "签到打卡",
					"code": "user_sign",
					"type": "event",
					"rules_num": 1
				},
				{
					"name": "分享商品",
					"code": "share_goods",
					"type": "event",
					"rules_num": 1
				},
				{
					"name": "邀请新人入会送积分",
					"code": "invite_new",
					"type": "event",
					"rules_num": 1
				},
				{
					"name": "注册送积分",
					"code": "register",
					"type": "event",
					"rules_num": 1
				},
				{
					"name": "活动送积分",
					"code": "campaign",
					"type": "event",
					"rules_num": 0
				},
				{
					"name": "下单送积分",
					"code": "order_pay",
					"type": "order",
					"rules_num": 0
				}
			],
			"consume_scene": [
				{
					"name": "积分折扣",
					"code": "user_discount",
					"rules_num": 0
				}
			]
		},
		"level_config": {
			"give_rules": [
				{
					"action": "follow",
					"text": "关注公众号",
					"change_score": 0,
					"type": 0
				},
				{
					"action": "shopping",
					"text": "消费",
					"change_score": 1,
					"per_money": 100,
					"type": 0
				},
				{
					"action": "visit_shop",
					"text": "访问店铺",
					"change_score": 1,
					"max_score": 10,
					"range_days": 1,
					"type": 1
				},
				{
					"action": "share_shop",
					"text": "分享店铺",
					"change_score": 1,
					"max_score": 10,
					"range_days": 1,
					"type": 1
				},
				{
					"action": "life_record",
					"text": "记录饮食、饮水、锻炼、排便、益生菌",
					"change_score": 1,
					"max_score": 10,
					"range_days": 1,
					"type": 1
				}
			],
			"deduct_rules": [
				{
					"action": "after_sales",
					"text": "售后扣减",
					"per_money": 100,
					"change_score": 1,
					"type": 0
				}
			],
			"downgrade": {
				"type": 0,
				"not_down": true,
				"shoping_times": 10
			}
		},
		"benefit_config": [
          {"benefit_code":"be_ratio_points","benefit_text":"会员积分倍率"},
          {"benefit_code":"be_member_coupon","benefit_text":"会员专属券"},
          {"benefit_code":"be_ship_free","benefit_text":"会员包邮"},
          {"benefit_code":"be_customize","benefit_text":"自定义组合权益"}]
	}
}
```

## 实例配置信息更新

- 请求 POST /api/crm/mgr/member/10080/config_update

- 参数

| 参数名            | 例子  | 类型     | 必填  | 描述      |
|:---------------|:----|:-------|:----|:--------|
| points_config  | -   | object | 否   | 积分相关的配置 |
| level_config   | -   | object | 否   | 等级相关的配置 |
| benefit_config | -   | object | 否   | 权益相关的配置 |

> 更新的字段结构，参考返回的结果，修改部分字段后提交更新

## 等级详情页

- 请求 GET /api/crm/mgr/member/10080/level_detail

- 返回结果解释

| 名称                          | 类型     | 空   | 说明                            |
|:----------------------------|:-------|:----|:------------------------------|
| code                        | int    |||
| msg                         | string |||
| data                        | object |||
| data.level_config           | object | -   | 参考member_config里面level_config |
| data.level_list             | array  | -   | 等级权益信息                        |
| - level_list.level_benefit  | string | -   | 等级权益信息                        |
| - level_list.level_bonus    | string | -   | 等级权益信息                        |
| - level_list.level_id       | string | -   | 业务id                          |
| - level_list.level_no       | int    | -   | 等级数字编码                        |
| - level_list.min_score      | int    | -   | 升级条件                          |
| - level_list.degraded_type  | int    | -   | 降级策略类型 common统一规则 level各等级配置  |
| - level_list.down_able      | bool   | -   | 能否降级                          |
| - level_list.min_ship_times | int    | -   | 最小购物次数 如果可降级 如果自定义配置          |

- 请求例子

```shell
```

## 等级配置信息更新

-请求 POST /api/crm/mgr/member/10080/level_cfg_save

- 参数 参考level_detail返回的数据结构

| 参数名            | 示例值    | 参数类型    | 是否必填 | 参数描述   |
|:---------------|:-------|:--------|:-----|:-------|
| level_config   | 1      | Number  | 是    | `等级配置` |
| level_list     | 等级1    | String  | 否    | `等级列表` |

- 请求例子

```shell
curl --location --request POST --X POST 'http://127.0.0.1:21200/api/crm/mgr/member/10080/level_save' \
--data '{
    "level_no": 1,
    "name": "等级1",
    "min_score": 0,
    "degraded_type": "common",
    "down_able": false,
    "min_ship_times": 10
}'
```

- 返回结果 code msg data=level_id

## 等级的删除

-请求 POST /api/crm/mgr/member/10080/level_delete

- 请求参数(json) level_id = 30000

- 返回: code msg data

## 等级奖励保存
- 请求 POST /api/crm/mgr/member/10080/level_bonus_save

- 参数

| 参数名            | 示例值    | 参数类型    | 是否必填 | 参数描述                      |
|:---------------|:-------|:--------|:-----|:--------------------------|
| level_id       | 1      | Number  | 是    | 等级id                      |
| points         | 10     | int     | 否    | 积分值                       |
| score          | 10     | int     | 否    | 成长值                       |
| coupons        | common | array   | 否    | 优惠券的列表                    |

- 请求例子

```shell

```

- 返回结果 code msg data

## 等级权益保存

- 请求 POST /api/crm/mgr/member/10080/level_benefit_save

- 参数

| 参数名           | 示例值 | 参数类型   | 是否必填 | 参数描述    |
|:--------------|:----|:-------|:-----|:--------|
| level_id      | 1   | Number | 是    | 等级id    |
| benefit_id_li | []  | array  | 是    | 勾选的权益id |

- 请求例子

```shell
```

- 返回结果 code msg data

## 权益/权益详情信息查看

- 请求 POST /api/crm
- 请求参数 benefit_id 权益id

- 返回参数

| 参数    | 类型     | 能否为空 | 说明       |
|:------|:-------|:-----|:---------|
| code  |        |      |          |
| msg   |        |      |          |
| data  |        |      |          |
| data.benefit_info | object | 是    | 权益的基础信息  |
| data.rules_dict | object | 是    | 权益下的规则配置 |

> `rules_dict` 字段解释: 返回的是基础权益id对应的规则配置
>  如果是自定义规则配置 则会多个基础权益id 下对应各自的规则配置
> 


- 请求例子

```shell
curl --location --request POST --X POST 'http://127.0.0.1:21200/api/crm/mgr/member/10080/benefit_detail' \
--header 'Content-Type: application/json' \
--data '{
    "benefit_id": 400003
}'
```

- 返回结果

```json
{
	"code": 0,
	"msg": "OK",
	"data": {
		"benefit_info": {
			"benefit_id": 400003,
			"crm_id": "10080",
			"benefit_type": "be_customize",
			"title": "自定义",
			"icon": null,
			"describe": "自定义组合权益",
			"enable": false
		},
		"rules_dict": [
			{
				"benefit_rule_id": 500007,
				"benefit_id": 400003,
				"benefit_type": "be_customeze",
				"name": "自定义大礼包权益",
				"son_rules": [
					500004,
					500005
				],
				"content": {},
				"son_rule_list": [
					{
						"benefit_rule_id": 500004,
						"benefit_id": 400000,
						"benefit_type": "be_ratio_points",
						"name": "1元1.1积分",
						"son_rules": null,
						"content": {}
					},
					{
						"benefit_rule_id": 500005,
						"benefit_id": 400000,
						"benefit_type": "be_ratio_points",
						"name": "2元1.2倍积分",
						"son_rules": null,
						"content": {}
					}
				]
			}
		]
	}
}
```

## 权益/权益配置信息保存

- 请求 POST /api/crm/mgr/member/{crm_id}/benefit_cfg_save

- 参数

| 参数           | 类型     | 必填  | 描述     |
|:-------------|:-------|:----|:-------|
| benefit_info | object | 是   | 权益基础信息 |
| rules_dict   | object | 是   | 权益规则数据 |

- 请求例子

- 权益规则配置字段

- 积分倍率

```json
{"ratio_points":1.1,"produce_scene":[{"rule_id":"","rule_name":""}]}
```
- 会员包邮

```json
{
    "free_shipping_type": "1-2",
    "region": [{
        "code": 10010,
        "name": "北京"
    }]
}
```
- 晋级礼券
> send_week send_day send_hour send_minute 为int 非必需字段填null
> send_type: now: 立即发放 发放一次 month 每月发放 week 每周发放 interval 自定义 

```shell
{
    "coupon_list":[
        {"coupon_id":1, "coupon_name":2}
    ],
    "send_type": "now|month|week|interval",
    "send_week": "1-7",
    "send_day": "1-30",
    "send_hour": "0-23",
    "send_minute": "0-59"

}
```


```shell
curl --location --request POST --X POST 'https://dev.quickshark.cn/api/crm/mgr/member/benefit_cfg_save' \
--header 'User-Agent: Apipost client Runtime/+https://www.apipost.cn/' \
--header 'Content-Type: application/json' \
--data '{
    "benefit_info": {
        "benefit_id": 400003,
        "crm_id": "10080",
        "benefit_type": "be_customize",
        "title": "fred自定义",
        "icon": null,
        "describe": "自定义组合权益",
        "enable": false
    },
    "rules_dict": [
        {
            "benefit_rule_id": 500007,
            "benefit_id": 400003,
            "benefit_type": "be_customeze",
            "name": "自定义大礼包权益",
            "son_rules": [
                {
                    "base_rule_id": 500004,
                    "base_benefit_id": 400000
                },
                {
                    "base_rule_id": 500005,
                    "base_benefit_id": 400000
                }
            ],
            "content": {}
        }
    ]
}'
```

- 返回结果 code msg data


## 权益/会员权益基础信息更新(含自定义权益)

- 请求 POST /api/crm/mgr/member/10080/benefit_update
- 参数

| 参数名        | 示例值  | 参数类型   | 是否必填 | 参数描述        |
|:-----------|:-----|:-------|:-----|:------------|
| benefit_id | 1    | Number | 是    | 权益id        |
| title      | []   | string | 否    | 权益名称        |
| icon       | xxxx | string | 否    | 图标          |
| describe   | 描述   | object | 否    | 描述信息        |
| enable     | true | bool   | 否    | 是否启用 true启用 |



## 权益/权益类型添加规则

- 请求 POST /api/crm/mgr/member/10080/benefit_rule_add

- 参数

| 参数名               | 示例值    | 参数类型   | 是否必填 | 参数描述       |
|:------------------|:-------|:-------|:-----|:-----------|
| benefit_id        | 1      | Number | 是    | 权益id       |
| benefit_type      | []     | string | 是    | 权益类型见下面的解释 |
| name              | 会员积分倍率 | string | 是    | 名称         |
| content           | {}     | object |      | 配置信息的内容    |

> benefit_type 权益类型 积分倍率 be_ratio_points 会员专属券 be_member_coupon  会员包邮 be_ship_free 自定义组合be_customize
> 


## 权益/自定义权益规则保存

- 请求 POST /api/crm/mgr/member/10080/defined_benefit_save

- 请求参数

| 参数名        | 例子  | 类型     | 必填  | 描述                    |
|:-----------|:----|:-------|:----|:----------------------|
| benefit_id |     | int    | 否   | 更新数据，传递benefit_id否则新增 |
| config     |     | object | 否   | 配置信息 自定义勾选的权益，权益对应的规则 |
| config     |     | object | 否   | 配置信息 自定义勾选的权益，权益对应的规则 |

## 权益/权益列表树

- 请求 GET /api/crm/mgr/member/10080/benefit_tree
- 请求例子

```shell
curl --location --request GET --X GET 'http://127.0.0.1:21200/api/crm/mgr/member/10080/benefit_tree' 
```

- 返回结果

```json
{
	"code": 0,
	"msg": "OK",
	"data": [
		{
			"type": "system",
			"title": "系统权益",
			"rules": [
				{
					"benefit_id": 400003,
					"benefit_type": "be_customize",
					"title": "自定义",
					"rules": []
				}
			]
		},
		{
			"type": "customize",
			"title": "自定义权益",
			"rules": [
				{
					"benefit_id": 400000,
					"benefit_type": "be_ratio_points",
					"title": "积分倍率",
					"rules": [
						{
							"base_benefit_id": 400000,
							"benefit_rule_id": 500004,
							"title": "1元1.1积分"
						},
						{
							"base_benefit_id": 400000,
							"benefit_rule_id": 500005,
							"title": "2元1.2倍积分"
						}
					]
				},
				{
					"benefit_id": 400001,
					"benefit_type": "be_member_coupon",
					"title": "晋级礼券",
					"rules": []
				},
				{
					"benefit_id": 400002,
					"benefit_type": "be_ship_free",
					"title": "包邮",
					"rules": []
				}
			]
		}
	]
}
```
## 权益/权益列表

- POST /api/crm/mgr/member/10080/defined_list

- 请求参数 json keyword

- 请求例子

```shell
curl --location --request POST --X POST 'https://dev.quickshark.cn/api/crm/mgr/member/benefit_list' \
--header 'Content-Type: application/json' \
--data '{}' 
```

- 返回结果

```json
{
	"code": 0,
	"msg": "OK",
	"data": {
		"items": [
			{
				"benefit_id": 400000,
				"crm_id": "10080",
				"benefit_type": "be_ratio_points",
				"title": "积分倍率",
				"icon": null,
				"describe": "不同等级会员消费时赠送有差异倍数的积分",
				"enable": true,
				"custom_config": null,
				"deleted": false,
				"rules_num": 2
			},
			{
				"benefit_id": 400001,
				"crm_id": "10080",
				"benefit_type": "be_member_coupon",
				"title": "晋级礼券",
				"icon": null,
				"describe": "自动为用户发放优惠券",
				"enable": true,
				"custom_config": null,
				"deleted": false,
				"rules_num": 0
			},
			{
				"benefit_id": 400002,
				"crm_id": "10080",
				"benefit_type": "be_ship_free",
				"title": "包邮",
				"icon": null,
				"describe": "为拥有权益的会员用户免除邮费",
				"enable": false,
				"custom_config": null,
				"deleted": false,
				"rules_num": 0
			},
			{
				"benefit_id": 400003,
				"crm_id": "10080",
				"benefit_type": "be_customize",
				"title": "自定义",
				"icon": null,
				"describe": "自定义组合权益",
				"enable": false,
				"custom_config": [
					{
						"benefit_id": 40000,
						"rule_ids": []
					}
				],
				"deleted": false,
				"rules_num": 0
			}
		]
	}
}
```

## 权益删除(可批量)

- 请求 POST /api/crm/mgr/member/10080/benefit_delete

- 请求参数 benefit_ids: benefit_id的数组

- 返回 code msg data


# 实例基础信息

## 省份列表获取

- GET /api/crm/mgr/10080/province_info

- 请求例子

```json
{
	"code": 0,
	"msg": "OK",
	"data": [
		{
			"code": "110000",
			"name": "北京市"
		},
		{
			"code": "120000",
			"name": "天津市"
		}
	]
}
```

## 商品列表数据获取

- 请求 POST /api/crm/mgr/open/{crm_id}/goods_list

- 请求例子

```shell
curl --location --request POST --X POST 'http://127.0.0.1:21200/api/crm/mgr/open/10080/goods_list' \
--data '{
    "keyword":null,
    "page_id":1,
    "page_size":2
}'
```

- 返回结果

```json
{
	"code": 0,
	"msg": "OK",
	"data": {
		"items": [
			{
				"sku_code": null,
				"goods_name": "1+2+3 橙色组合套装2",
				"spec_value_1": "10 ml",
				"spec_value_2": null,
				"goods_id": 200532
			},
			{
				"sku_code": "12345678902",
				"goods_name": "特洛益益生菌21条装2#",
				"spec_value_1": "21",
				"spec_value_2": null,
				"goods_id": 200565
			}
		],
		"total": 44
	}
}
```

