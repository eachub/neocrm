# eros_crm/会员模块

## POST 绑定查询

POST /api/crm/member/{crm_id}/bind_query

> Body 请求参数

```json
{
  "mobile": "string",
  "member_no": "string",
  "platform": "string",
  "platform_info": {
    "ouid": "string",
    "mix_mobile": "string",
    "unionid": "string",
    "dy_openid": "string"
  }
}
```

### 请求参数

| 名称              | 位置   | 类型     | 必选  | 中文名       | 说明                                 |
|-----------------|------|--------|-----|-----------|------------------------------------|
| crm_id          | path | string | 是   || 实例id      |
| body            | body | object | 否   || none      |
| » mobile        | body | string | 是   | 手机号       | 手机号                                |
| » member_no     | body | string | 是   | 会员号       | mobile和member_no都有的情况下优先使用mobile查询 |
| » platform      | body | string | 是   || 平台标识      |
| » platform_info | body | object | 是   || 平台信息      |
| »» ouid         | body | string | 是   || 天猫渠道标识    |
| »» mix_mobile   | body | string | 是   || 天猫渠道加密手机号 |
| »» unionid      | body | string | 是   || 微信平台的标识   |
| »» dy_openid    | body | string | 是   || 抖音平台的用户标识 |

> 返回示例

> 成功

```json
{
  "code": 0,
  "msg": "用户可以绑定",
  "data": {
    "bind_able": true,
    "member_info": {
      "member_no": "M220627-936388997698",
      "platform": "wechat",
      "member_name": "笑而不语",
      "level": "lv1",
      "province": "河南",
      "city": "郑州",
      "birthday": "2005-01-30",
      "gender": 1,
      "invite_code": "NE181a3c61421xEsN",
      "create_time": "2022-06-27 14:07:56"
    }
  }
}
```

## 换绑手机号

请求路径: ***/api/crm/member/<crm_id>/unbind_mobile***

请求方法: POST

参数：
```json
{
  "member_no": "",
  "mobile": "",
  "origin_mobile": ""
}
```

参数解释：

| 参数            | 解释   | 类型     | 是否必填 |
|---------------|------|--------|------|
| member_no     | 会员号  | string | 是    |
| mobile        | 手机号  | string | 是    |
| origin_mobile | 原手机号 | string | 是    |

响应：
```json
{
    "code": 0,
    "msg": "换绑手机号成功"
}
```

## POST 会员注册

POST /api/crm/member/{crm_id}/register

> Body 请求参数

```json
{
  "mobile": "18182557482",
  "birthday": "2005-01-30",
  "nickname": "笑而不语",
  "province": "河南",
  "city": "郑州",
  "avatar": "123",
  "gender": 1,
  "source": {
    "channel_code": "28",
    "ip": "194.16.184.53",
    "campaign_code": "招新活动",
    "appid": "wx332340823dfjd",
    "path": "/index/login",
    "scene": "抽奖",
    "invite_code": "inviter_code333"
  },
  "geo_origin_from": "1",
  "platform": "wechat",
  "user_info": {
    "openId": "OPENID",
    "nickName": "笑而不语",
    "gender": 1,
    "city": "郑州市",
    "province": "河南省",
    "country": "中国",
    "avatarUrl": "http://...",
    "unionId": "UNIONID"
  }
}
```

### 请求参数

| 名称                | 位置   | 类型     | 必选  | 中文名                                     | 说明                       |
|-------------------|------|--------|-----|-----------------------------------------|--------------------------|
| crm_id            | path | string | 是   || 路径参数实例id                                |
| body              | body | object | 否   |||
| » mobile          | body | string | 是   | 手机号                                     | 手机号                      |
| » birthday        | body | string | 是   | 生日                                      | 生日                       |
| » source          | body | object | 否   || 来源信息                                    |
| »» channel_code   | body | string | 否   || 渠道编码                                    |
| »» campaign_code  ||| 否    |||
| »» ip             | body | string | 否   || none                                    |
| »» appid          | body | string | 否   || appid                                   |
| »» path           | body | string | 否   || 来源路径                                    |
| »»scene           | body | string | 否   || 来源场景                                    |
| »» invite_code    | body | string | 否   || 邀请码                                     |
| » geo_origin_from | body | string | 是   || 0来自平台<br/>1 手动填写<br/>2 来自ip<br/>3 来源手机号 |
| » platform        | body | string | 是   | 平台                                      | 来源平台 wechat tmall douyin |
| » user_info       | body | object | 是   | 渠道用户信息                                  | none                     |

> 成功

```json
{
  "code": 0,
  "msg": "注册成功",
  "data": {
    "member_no": "M220627936388997698"
  }
}
```

## POST 会员信息完善

POST /api/crm/member/{crm_id}/update

> Body 请求参数

```json
{
  "member_no": "string",
  "nickname": "string",
  "avatar": "string",
  "province": "string",
  "city": "string",
  "birthday": "string",
  "gender": "string",
  "hobby": [
    "string"
  ],
  "email": "string",
  "occupation": "string",
  "address": "string",
  "platform": "string",
  "user_info": {}
}
```

### 请求参数

|名称|位置|类型|必选| 中文名                  |说明|
|---|---|---|---|----------------------|---|
|crm_id|path|string| 是 || none                 |
|body|body|object| 否 || none                 |
|» member_no|body|string| 是 | 会员号                  |none|
|» nickname|body|string¦null| 是 | 昵称                   |none|
|» avatar|body|string¦null| 是 | 头像                   |头像|
|» province|body|string¦null| 是 || none                 |
|» city|body|string¦null| 是 || none                 |
|» birthday|body|string¦null| 是 | 生日                   |none|
|» gender|body|string¦null| 是 || gender 1男 2女 0其他(未知) |
|» hobby|body|[string]¦null| 是 | 兴趣爱好                 |none|
|» email|body|string¦null| 是 || none                 |
|» occupation|body|string¦null| 是 | 职业                   |none|
|» address|body|string¦null| 是 | 详细地址信息               |none|
|» platform|body|string¦null| 是 || 平台                   |
|» user_info|body|object| 是 || 平台的用户信息              |

> 返回示例

## POST 渠道会员绑定

POST /api/crm/member/{crm_id}/member_bind

> Body 请求参数

```json
{
  "member_no": "string",
  "platform": "string",
  "user_info": {
    "appid": "string",
    "openId": "string",
    "nickName": "string",
    "gender": 0
  }
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|crm_id|path|string| 是 ||none|
|body|body|object| 否 ||none|
|» member_no|body|string| 是 | 会员号|会员号|
|» platform|body|string| 是 | 平台|none|
|» user_info|body|object| 是 | 平台用户信息|平台用户信息 传参参考注册接口|
|»» appid|body|string| 是 ||none|
|»» openId|body|string| 是 ||none|
|»» nickName|body|string| 是 ||none|
|»» gender|body|integer| 是 ||none|

## 会员注销(加入黑名单)
- 请求 POST /api/crm/member/10080/cancel
- 请求参数

| 参数         | 类型     | 例子  | 必填  | 说明                       |
|------------|--------|-----|-----|--------------------------|
| member_no  | string |     | 是   |                          |
| mobile     | string |     | 否   |                          |
| block_time | string |     | 否   | 拉黑时间                     |
| desc       | string |     | 否   | 描述                       |
| operator   | string |     | 否   | 操作者                      |

- 请求例子

```shell
curl --location --request POST --X POST 'http://127.0.0.1:21200/api/crm/member/10080/cancel' \
--header 'Content-Type: application/json' \
--data '{
    "member_no":"",
    "mobile":"",
    "block_time":0,
    "desc":"注销的描述",
    "operator":"张三",
    "black_list": []
}'
```

## POST 家庭组添加

POST /api/crm/member/{crm_id}/family/add

> Body 请求参数

```json
{
  "member_no": "M220627-936388997698",
  "nickname": "三弟",
  "avatarUrl": "http://dummyimage.com/88x32",
  "gender": 1,
  "birthday": "2021-02-18",
  "relationship": 1,
  "occupation": "工程师"
}
```

### 请求参数

| 名称             | 位置   | 类型          | 必选  | 中文名                   | 说明   |
|----------------|------|-------------|-----|-----------------------|------|
| crm_id         | path | string      | 是   || none                  |
| body           | body | object      | 否   || none                  |
| » member_no    | body | string      | 是   | 会员名                   | none |
| » nickname     | body | string¦null | 是   | 昵称                    | none |
| » avatar       | body | string¦null | 是   || none                  |
| » gender       | body | integer     | 是   || none                  |
| » birthday     | body | string      | 否   || none                  |
| » relationship | body | int         | 否   || 角色1自己2父亲3母亲4配偶5孩子6其他人 |
| » occupation   | body | string      | 是   || none                  |
| » province     | body | string      | 是   || 省份                    |
| » city         | body | string      | 是   || 城市                    |

> 返回示例

> 成功

```json
{
  "code": 0,
  "msg": "添加成功",
  "data": 5
}
```

### 返回数据结构

状态码 **200**

| 名称     | 类型      | 必选   | 约束   | 中文名  | 说明  |
|--------|---------|------|------|------|-----|
| » code | integer | true | none || none |
| » msg  | string  | true | none || none |
| » data | integer | true | none || none |

## POST 家庭组修改

POST /api/crm/member/{crm_id}/family/update

> Body 请求参数

```json
{
  "family_uid": 0,
  "nickname": "string",
  "avatarUrl": "string",
  "gender": 0,
  "birthday": "string",
  "relationship": "string",
  "occupation": "string"
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|crm_id|path|string| 是 ||none|
|body|body|object| 否 ||none|
|» family_uid|body|integer| 是 | 会员名|none|
|» nickname|body|string¦null| 是 | 昵称|必填|
|» avatar|body|string¦null| 是 ||none|
|» gender|body|integer¦null| 是 ||none|
|» birthday|body|string¦null| 是 ||none|
|» relationship|body|string¦null| 是 ||none|
|» occupation|body|string¦null| 是 ||none|

> 返回示例

> 成功

```json
{
  "code": 0,
  "msg": "更新成功"
}
```

## POST 家庭组删除

POST /api/crm/member/{crm_id}/family/lot_delete

> Body 请求参数

```json
{
  "member_no": "string",
  "family_uid_li": [
    "string"
  ]
}
```

### 请求参数

|名称|位置|类型|必选|中文名|说明|
|---|---|---|---|---|---|
|crm_id|path|string| 是 ||none|
|body|body|object| 否 ||none|
|» member_no|body|string| 是 | 会员名|none|
|» family_uid_li|body|[string]| 是 ||none|

> 返回示例

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||none|
|» msg|string|true|none||none|
|» data|integer|true|none||none|

## POST 家庭组查看

POST /api/crm/member/{crm_id}/family/query

> Body 请求参数

```json
{
  "member_no": "string",
  "family_uid": "string"
}
```

### 请求参数

| 名称           | 位置   | 类型     | 必选  | 中文名     | 说明   |
|--------------|------|--------|-----|---------|------|
| crm_id       | path | string | 是   || none    |
| body         | body | object | 否   || none    |
| » member_no  | body | string | 是   | 会员名     | none |
| » family_uid | body | string | 是   | 家庭组成员id | none |

> 返回示例

> 成功

```json
{
  "code": 0,
  "msg": "OK",
  "data": {
    "items": [
      {
        "family_uid": 3,
        "member_no": "M220627-936388997698",
        "nickname": "",
        "gender": 1,
        "avatar": null,
        "birthday": "2021-02-18",
        "relationship": "sun",
        "occupation": "工程师",
        "create_time": "2022-06-27 23:17:57",
        "update_time": "2022-06-27 23:17:57"
      },
      {
        "family_uid": 4,
        "member_no": "M220627-936388997698",
        "nickname": "王小丽",
        "gender": 2,
        "avatar": null,
        "birthday": "1997-05-22",
        "relationship": "sun",
        "occupation": "工程师",
        "create_time": "2022-06-27 23:20:00",
        "update_time": "2022-06-27 23:28:22"
      }
    ]
  }
}
```

### 返回数据结构

状态码 **200**

|名称|类型|必选|约束|中文名|说明|
|---|---|---|---|---|---|
|» code|integer|true|none||返回code|
|» msg|string|true|none||信息|
|» data|object|true|none||data|
|»» items|[object]|true|none||none|
|»»» family_uid|integer|true|none||家庭组员id|
|»»» member_no|string|true|none||会员号|
|»»» nickname|string|true|none||昵称|
|»»» gender|integer|true|none||性别|
|»»» avatar|null|true|none||头像|
|»»» birthday|string|true|none||生日|
|»»» relationship|string|true|none||家庭组关系|
|»»» occupation|string|true|none||职业|
|»»» create_time|string|true|none||创建时间|
|»»» update_time|string|true|none||注册时间|

## /eros_crm/查询会员信息

#### 接口URL

> 127.0.0.1:21100/api/crm/member/10080/member_query

#### 请求方式

> POST

#### Content-Type

> application/json

#### 请求Body参数

```javascript
{
    "member_no":"M220701534161771542",
    "mobile":"",
    "platform":"wechat",
    "appid":"",
    "openid":"",
    "unionid":"",
    "mix_mobile":""
}
```

- 请求例子

```shell
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/crm/member/10080/member_query' \
--data '{
    "platform":"wechat",
    "appid":"wx71031dea78e9d57b",
    "openid":"oGlFU5bnTAT3vrt-bQsSW3j6Mmcs",
}'
```

| 参数名         | 示例值    | 参数类型   | 是否必填 | 参数描述                                                |
|-------------|--------|--------|------|-----------------------------------------------------|
| member_no   | 会员号    | String | 否    | 会员号                                                 |
| mobile      | 手机号    | String | 否    | 手机号码 会员号手机号同时优先使用mobile查询                           |
| platform    | wechat | String | 否    | 平台 wechat douyin tmall                              |
| appid       | -      | Object | 否    | 平台的参数appid                                          |
| openid      | -      | Object | 否    | 平台参数微信openid                                        |
| unionid     | -      | Object | 否    | 微信unionid                                           |
| mix_mobile  | -      | Object | 否    | 加密手机号                                               |
| t_platform  | -      | bool   | 否    | 是否返回平台信息的标识，如果t_platform、platform都有值 返回该platform的信息 |
| t_extend    | -      | bool   | 否    | 是否返回会员扩展信息的标识                                       |
| t_source    | -      | bool   | 否    | 是否返回会员来源信息的标识                                       |
| t_family    | -      | bool   | 否    | 是否返回家庭成员信息的标识                                       |
| plained     | -      | bool   | 否    | true 返回明文手机号                                        |
| invite_code | -      | string | 否    | 邀请码查询会员信息                                           |

#### 成功响应示例

```json
{
	"code": 0,
	"msg": "OK",
	"data": {
		"info": {
			"info_id": 11,
			"crm_id": "10080",
			"member_no": "M220701534161771542",
			"mobile": "18438610505",
			"platform": "wechat",
			"member_name": "君子如玉",
			"level": "lv1",
			"avatar": "123",
			"province": "未知",
			"city": "未知",
			"birthday": "1997-01-30",
			"gender": 2,
			"member_status": 0,
			"invite_code": "NE181b7ad5f34wRHt",
			"create_time": "2022-07-01 10:53:21",
			"update_time": "2022-07-01 10:53:21"
		},
		"extend_info": {
			"extend_id": 6,
			"crm_id": "10080",
			"member_no": "M220701534161771542",
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
			"create_time": "2022-07-01 10:53:21",
			"update_time": "2022-07-01 10:53:21"
		},
		"wechat_member_info": {
			"auto_id": 2,
			"crm_id": "10080",
			"member_no": "M220701534161771542",
			"appid": "wx71031dea78e9d57b",
			"unionid": "oGlFU5bnTAT3vrt-bQsSW3j6Mmcs",
			"openid": "oGlFU5bnTAT3vrt-bQsSW3j6Mmcs",
			"card_code": null,
			"nickname": "一只快乐的野指针",
			"country": "",
			"province": "",
			"city": "",
			"avatar": "https://thirdwx.qlogo.cn/mmopen/vi_32/ly3xana9KAsllLFbwqxuT0nm3B7iawlzdgFbCKY6f9wUpemksI2TeBCic9165cZ3cUEYR7MxI4a1o8tjiacTcibjzQ/132",
			"gender": 0,
			"status": 0,
			"extra": null,
			"create_time": "2022-07-01 10:53:21",
			"update_time": "2022-07-01 10:53:21"
		},
		"alipay_member_info": {},
		"douyin_member_info": {},
		"member_source_info": {
			"auto_id": 6,
			"crm_id": "10080",
			"member_no": "M220701534161771542",
			"channel_code": "0",
			"platform": "wechat",
			"campaign_code": "",
			"appid": "wx71031dea78e9d57b",
			"path": "",
			"scene": "",
			"invite_code": "",
			"extra": {
				"ip": "127.0.0.1"
			},
			"create_time": "2022-07-01 10:53:21",
			"update_time": "2022-07-01 10:53:21"
		}
	}
}
```

## GET 获取会员标签信息
- 请求 GET api/crm/member/10080/member_tags
- 请求参数 member_no
- 返回

| 名称                 | 类型     | 必选  | 说明     |
|--------------------|--------|-----|--------|
| code               | int    | 是   |        |
| msg                | string | 是   |        |
| data               | object | 是   |        |
| data.tags          | array  | 是   |        |
| data.tags.tag_id   | string | 是   | 标签id   |
| data.tags.leveles  | string | 是   | 标签等级信息 |
| data.tags.tag_name | string | 是   | 标签名称   |
| data.tags.category | string | 是   | 标签分类   |

> 说明： 分类：人口属性 标签:生日 标签等级属性：6月 


- 请求例子

```shell
curl --location --request GET --X GET 'http://127.0.0.1:21200/api/crm/member/10080/member_tags?member_no=M220704308572703018'
```
- 返回结果

```json
{
	"code": 0,
	"msg": "OK",
	"data": {
		"tags": [
			{
				"tag_id": 200006,
				"levels": [
					{
						"tag_id": 200006,
						"level_id": 6001780,
						"level_name": "微信"
					}
				],
				"tag_name": "注册引流渠道",
				"category": "会员行为"
			},
			{
				"tag_id": 200007,
				"levels": [
					{
						"tag_id": 200007,
						"level_id": 6001781,
						"level_name": "低频积分获取"
					}
				],
				"tag_name": "积分变更行为",
				"category": "会员行为"
			},
			{
				"tag_id": 200008,
				"levels": [
					{
						"tag_id": 200008,
						"level_id": 6001786,
						"level_name": "女"
					}
				],
				"tag_name": "性别",
				"category": "人口属性"
			},
			{
				"tag_id": 200009,
				"levels": [
					{
						"tag_id": 200009,
						"level_id": 6001792,
						"level_name": "20岁到40岁"
					}
				],
				"tag_name": "年龄",
				"category": "人口属性"
			},
			{
				"tag_id": 200010,
				"levels": [
					{
						"tag_id": 200010,
						"level_id": 6002252,
						"level_name": "6月"
					}
				],
				"tag_name": "生日",
				"category": "人口属性"
			},
			{
				"tag_id": 200011,
				"levels": [
					{
						"tag_id": 200011,
						"level_id": 6002261,
						"level_name": "等级3"
					}
				],
				"tag_name": "会员等级",
				"category": "人口属性"
			},
			{
				"tag_id": 200012,
				"levels": [
					{
						"tag_id": 200012,
						"level_id": 6001801,
						"level_name": "入会1周-1个月"
					}
				],
				"tag_name": "会龄区间",
				"category": "人口属性"
			},
			{
				"tag_id": 200013,
				"levels": [
					{
						"tag_id": 200013,
						"level_id": 6001806,
						"level_name": "中度活跃"
					}
				],
				"tag_name": "活跃状态",
				"category": "人口属性"
			},
			{
				"tag_id": 200014,
				"levels": [
					{
						"tag_id": 200014,
						"level_id": 6001808,
						"level_name": "少于2人"
					}
				],
				"tag_name": "家庭成员数量",
				"category": "人口属性"
			},
			{
				"tag_id": 200015,
				"levels": [
					{
						"tag_id": 200015,
						"level_id": 6002000,
						"level_name": "郑州市"
					}
				],
				"tag_name": "最近一次访问小程序出现的城市",
				"category": "人口属性"
			},
			{
				"tag_id": 200016,
				"levels": [
					{
						"tag_id": 200016,
						"level_id": 6001826,
						"level_name": "河南省"
					}
				],
				"tag_name": "最近一次访问小程序出现的省份",
				"category": "人口属性"
			},
			{
				"tag_id": 200017,
				"levels": [
					{
						"tag_id": 200017,
						"level_id": 6002202,
						"level_name": "低频购买"
					}
				],
				"tag_name": "近期购买频次",
				"category": "消费习惯"
			}
		]
	}
}
```

## 批量获取会员基础信息

- 请求 POST /api/crm/member/10080/batch_basic

- 参数 member_nos:会员号数组

- 请求例子

```shell
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/crm/member/10080/batch_basic' \
--header 'Content-Type: application/json' \
--data '{
    "member_nos": ["M220627-936388997698", "M220704308572703018"]
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
				"info_id": 9,
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
				"update_time": "2022-07-04 19:32:12"
			},
			{
				"info_id": 14,
				"crm_id": "10080",
				"member_no": "M220704308572703018",
				"mobile": "18438610505",
				"platform": "wechat",
				"nickname": "一只快乐",
				"level": "lv1",
				"avatar": "https://thirdwx.qlogo.cn/mmopen/vi_32/ly3xana9KAsllLFbwqxuT0nm3B7iawlzdgFbCKY6f9wUpemksI2TeBCic9165cZ3cUEYR7MxI4a1o8tjiacTcibjzQ/132",
				"province": "河南",
				"city": "洛阳",
				"birthday": null,
				"gender": 0,
				"member_status": 0,
				"invite_code": "NE181c8b81577xKrl",
				"create_time": "2022-07-04 18:18:36",
				"update_time": "2022-07-04 19:35:03"
			}
		]
	}
}
```


## 头像链接或文件转换为内部链接
- 请求 POST /api/crm/member/{crm_id}/image_convert

- 参数 (form-data)

| 参数         | 类型   | 必填  | 说明     |
|:-----------|:-----|:----|:-------|
| image_url  | text | 否   | 头像资源链接 |
| image_file | file | 否   | 头像文件   |

- 返回包体

```json
{
  "code": 0, "msg": "OK", "data": {
    "crm_url": "www.eachub.cn"
  }
}
```
