## 积分规则/积分累加规则配置保存
- 接口 POST /api/crm/mgr/points/{crm_id}/rules/produce_scene
- 请求参数

| 参数名           | 示例值       | 参数类型    | 是否必填 | 参数描述              |
|---------------|-----------|---------|------|-------------------|
| rule_name     | 下单支付      | Text    | 是    | 规则名称              |
| action_scene  | order_pay | Text    | 是    | 规则场景              |
| points_type   | order     | Text    | 是    | event 或order      |
| expire_term   | 30        | Integer | 是    | 多久过期              |
| per_money     | 50        | Integer | 否    | 每多少元              |
| change_points | 10        | Number  | 是    | 改变的积分值            |
| freeze_term   | 3         | Integer | 否    | 冻结时间              |
| max_points    | 30        | Number  | 否    | 时间范围内最大积分         |
| max_times     | 10        | Number  | 否    | 时间范围内最大次数         |
| range_days    | 1         | Number  | 是    | 时间范围单位days 0无时间范围 |
| mul_rules     | true      | bool    | 否    | 多条规则的标识 true      |

- 请求包体
```json
{
    "rule_name": "下单支付",
    "action_scene":"order_pay",
    "points_type":"order",
    "expire_term": 30,
    "per_money": 50,
    "change_points": 10,
    "freeze_term":3,
    "max_points": 30,
    "max_times": 10,
    "range_days":1
}
```
- 返回 code msg

```json
{"code":0,"msg":"保存积分累加规则成功"}
```


## /eros_crm/积分规则/保存积分消耗规则


#### 接口URL

> 127.0.0.1:21100/api/crm/mgr/points/{crm_id}/rules/consume_scene

#### 请求方式

> POST

#### Content-Type

> json

#### 请求Body参数

```javascript
{
    "rule_name": "积分抵扣",
    "action_scene":"discount",
    "rules_li": [
        {"base_points": 50,
        "convert_money":2,
        "consume_level":1}
    ]
    
}
```

| 参数名        | 示例值        | 参数类型 | 是否必填 | 参数描述                     |
| ------------- | ------------- | -------- | -------- | ---------------------------- |
| rule_name     | 积分抵扣      | Text     | 是       | 规则名称                     |
| action_scene  | user_discount | Text     | 是       | 规则场景                     |
| rules_li  |  | array     | 是       | 积分规则的数组                     |
| rules_li.base_points   | 50            | Integer  | 是       | 多久过期                     |
| rules_li.convert_money | 2             | Integer  | 是       | 增加的积分值，订单为积分倍率 |
| rules_li.consume_level | 1             | Integer  | 否       | 每多少元                     |
| rules_li.goods_white   | -             | Object   | 是       | 商品白名单                   |


## /eros_crm/积分规则/积分消耗规则更新

#### 接口URL

> 127.0.0.1:21100/api/crm/mgr/points/{crm_id}/rules/consume_scene/update

#### 请求方式

> POST

#### Content-Type

> json

#### 请求Body参数

```javascript
{
    "rule_id": 1,
    "rule_name": "积分抵扣现金",
    "base_points": 50,
    "convert_money":2
}
```

| 参数名        | 示例值        | 参数类型 | 是否必填 | 参数描述 |
| ------------- | ------------- | -------- | -------- | -------- |
| rule_id       | 1             | Number   | 是       | -        |
| rule_name     | 积分抵扣      | String   | 否       | 规则名称 |
| action_scene  | user_discount | String   | 否       | 规则场景 |
| expire_term   | 30            | Number   | 否       | 多久过期 |
| base_points   | 50            | Number   | 否       | -        |
| convert_money | 2             | Number   | 否       | -        |

## /eros_crm/积分规则/积分累加规则修改

#### 接口URL

> 127.0.0.1:21100/api/crm/mgr/points/{crm_id}/rules/produce_scene/update

#### 请求方式

> POST

#### Content-Type

> json

#### 请求Body参数

```javascript
{
    "rule_id":1,
    "rule_name": "每日登录",
    "expire_term": 30,
    "per_money": 50,
    "change_points": 15,
    "freeze_term":3
}
```

| 参数名           | 示例值   | 参数类型 | 是否必填 | 参数描述 |
|---------------| -------- | -------- | -------- |--|
| rule_id       | 1        | Number   | 是       | - |
| rule_name     | 每日登录 | String   | 否       | 规则名称 |
| action_scene    | user_login  | String   | 否  | 积分场景编码 |
| points_type    | order  | String   | 否  | 积分类型 |
| expire_term   | 30       | Number   | 否       | 多久过期 |
| per_money     | 50       | Number   | 否       | 每多少元 |
| change_points | 15       | Number   | 否       | 多少积分 |
| freeze_term   | 3        | Number   | 否       | 冻结时间 |
| range_days    | 1        | Number   | 否       | 默认0：没有时间限制 时间周期 多长时间范围内最大积分、最大次数 |
| max_times    | 3        | Number   | 否       | 限制条件 时间周期内最大次数 |
| max_points    | 3        | Number   | 否       | 限制条件 时间周期内最大积分 |



## /eros_crm/积分规则/积分规则删除

#### 接口URL

> 127.0.0.1:21100/api/crm/mgr/points/{crm_id}/rules/lot_delete

#### 请求方式

> POST

#### Content-Type

> json

#### 请求Body参数

```javascript
{
    "rule_id": 1,
    "rule_type": "produce"
}
```

| 参数名        | 示例值  | 参数类型   | 是否必填 | 参数描述     |
|------------| ------- |--------| -------- |----------|
| rule_id_li | 1       | array  | 是       | 要删除的规则id |
| rule_type  | produce | String | 是       | 类型       |


## /eros_crm/积分规则/积分规则查询

#### 接口URL

> 127.0.0.1:21100/api/crm/mgr/points/{crm_id}/rules/query

#### 请求方式

> POST

#### Content-Type

> json

#### 请求Body参数

```javascript
{
    "rule_type": "produce",
    "action_scene":"user_login"
}
```

| 参数名       | 示例值     | 参数类型 | 是否必填 | 参数描述 |
| ------------ | ---------- | -------- | -------- | -------- |
| rule_type    | produce    | String   | 是       | 类型  积分累加produce 积分消耗consume    |
| action_scene | user_login | String   | 否       | 规则场景 |
| rule_name    | -          | Text     | 否       | 规则名称 |
| rule_id      | -          | Text     | 否       | 规则id   |
| page_id      | -          | Text     | 否       | -        |
| page_size    | -          | Text     | 否       | -        |


---
title: each v1.0.0




# eros_crm/积分分析

## GET 积分汇总接口

GET /api/crm/mgr/analyze/{crm_id}/points/total

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|crm_id|path|string| 是 |none|
|dr|query|string| 是 |时间范围|
|crm_id|query|string| 是 |none|

> 返回示例



## GET 积分趋势

GET /api/crm/mgr/analyze/{crm_id}/points/trend

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|crm_id|path|string| 是 |none|
|dr|query|string| 是 |时间范围|
|crm_id|query|string| 是 |none|

> 返回示例

> 成功

```json
{
  "code": 0,
  "msg": "OK",
  "data": {
    "prod_points": [
      0
    ],
    "prod_points_user": [
      0
    ],
    "total_prod": [
      0
    ],
    "total_prod_user": [
      0
    ],
    "consume_points": [
      0
    ],
    "consume_points_user": [
      0
    ],
    "total_consume": [
      0
    ],
    "total_consume_user": [
      0
    ],
    "total_active": [
      0
    ],
    "total_active_user": [
      0
    ],
    "total_transfer": [
      0
    ],
    "total_transfer_user": [
      0
    ],
    "total_accept": [
      0
    ],
    "total_accept_user": [
      0
    ],
    "expire_points": [
      0
    ],
    "expire_points_user": [
      0
    ],
    "total_expire": [
     
      0
    ],
    "total_expire_user": [
      0
    ],
    "tdate": [
      "2022-06-10",
      "2022-06-11",
      "2022-06-12",
      "2022-06-13",
      "2022-06-14",
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


## GET 积分分布

GET /api/crm/mgr/analyze/{crm_id}/points/distr

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|crm_id|path|string| 是 |none|
|dr|query|string| 是 |时间范围|
|crm_id|query|string| 是 |none|
|types|query|string| 是 |source积分来源 redu_source消耗来源|

> 返回示例

> 成功

```json
{
  "code": 0,
  "msg": "OK",
  "data": {
    "result": [
      {
        "label": "order_pay",
        "item": "order_pay",
        "counts": 120
      },
      {
        "label": "user_login",
        "item": "user_login",
        "counts": 20
      }
    ],
    "crm_id": "10080",
    "from_date": "2022-06-10",
    "to_date": "2022-07-01"
  }
}
```

## GET 积分分析导出

GET /api/crm/mgr/analyze/{crm_id}/points/export

### 请求参数

|名称|位置|类型|必选|说明|
|---|---|---|---|---|
|crm_id|path|string| 是 |none|
|dr|query|string| 是 |时间范围|
|crm_id|query|string| 是 |none|

> 返回示例


## /eros_crm/积分事件接口/积分明细查询

#### 接口URL

> 127.0.0.1:21100/api/crm/mgr/points/10080/history

#### 请求方式

> POST

#### Content-Type

> json

#### 请求Body参数

```javascript
{
    "event_type":"produce",
    "start_time":"2022-06-01 12:00:00",
    "end_time":"2022-07-01 12:00:00",
    "member_no":"ec_18165fd7455_JGhyfyLmX"
}
```

| 参数名        | 示例值                   | 参数类型 | 是否必填 | 参数描述                                                                |
| ------------- | ------------------------ | -------- | -------- |---------------------------------------------------------------------|
| event_type   | produce                  | String   | 是       | 搜索类型"produce", "consume", "transfer", "accept" expired freeze等见下面备注 |
| start_time    | 2022-06-01 12:00:00      | String   | 否       | 开始时间                                                                |
| end_time      | 2022-07-01 12:00:00      | String   | 否       | 结束时间                                                                |
| member_no     | ec_18165fd7455_JGhyfyLmX | String   | 否       | 会员名称                                                                |
| mobile        | 18608011234              | String   | 否       | 手机号码                                                                |
| action_scene  | -                        | Object   | 否       | 规则场景                                                                |
| campagin_code | -                        | Object   | 否       | -                                                                   |
| stroe_code    | -                        | Object   | 否       | -                                                                   |
| cost_center   | -                        | Object   | 否       | -                                                                   |
| page_id   | -                        | int   | 否       | 默认1                                                                 |
| page_size   | -                        | int   | 否       | 默认10                                                                |
| order_by   | -                        | string   | 否       | 默认update_time                                                       |
| order_asc   | -                        | int   | 否       | 默认0 0倒叙 1正序                                                         |

> event_type 字段备注:
> produce 累加
> consume 消耗
> transfer 转赠
> accept 领取转赠
> reverse_produce 反累加
> reverse_consume  反消耗
> reverse 代表的是冲正时间（包含reverse_produce reverse_consume ）


#### 成功响应示例

```javascript
{
    "code": 0,
    "msg": "OK",
    "data": {
        "total": 1,
        "items": [
            {
                "auto_id": 27,
                "crm_id": "10080",
                "member_no": "ec_18165fd7455_JGhyfyLmX",
                "event_no": "add20220615202826397549953512",
                "origin_event_no": null,
                "from_transfer_no": null,
                "action_scene": "order_pay",
                "event_type": "produce",
                "reverse_status": 0,
                "amount": null,
                "points": 30,
                "expire_time": "2022-12-13 10:10:00",
                "unfreeze_time": null,
                "store_code": "ec_mall",
                "cost_center": "cost_center001",
                "campagin_code": null,
                "operator": "小程序",
                "event_desc": "用户多了30积分,无冻结时间",
                "order_items": null,
                "create_time": "2022-06-16 11:45:23",
                "update_time": "2022-06-16 11:45:23"
            }
        ]
    }
}
```

| 参数名                      | 示例值                        | 参数类型 | 参数描述     |
| --------------------------- | ----------------------------- | -------- | ------------ |
| code                        | -                             | Number   |              |
| msg                         | OK                            | String   | 返回文字描述 |
| data                        | -                             | Object   | 返回数据     |
| data.total                  | 7                             | Number   | 返回的总数   |
| data.items                  | -                             | Object   |              |
| data.items.auto_id          | 27                            | Number   |              |
| data.items.crm_id           | 10080                         | String   |              |
| data.items.member_no        | ec_18165fd7455_JGhyfyLmX      | String   | 会员名称     |
| data.items.event_no         | add20220615202826397549953512 | String   | 事件no       |
| data.items.origin_event_no  | -                             | Object   | 要冲正的事件 |
| data.items.from_transfer_no | -                             | Object   |              |
| data.items.action_scene     | order_pay                     | String   | 规则场景     |
| data.items.event_type       | produce                       | String   |              |
| data.items.reverse_status   | -                             | Number   |              |
| data.items.amount           | -                             | Object   |              |
| data.items.points           | 30                            | Number   |              |
| data.items.expire_time      | 2022-12-13 10:10:00           | String   |              |
| data.items.unfreeze_time    | -                             | Object   |              |
| data.items.store_code       | ec_mall                       | String   |              |
| data.items.cost_center      | cost_center001                | String   |              |
| data.items.campagin_code    | -                             | Object   |              |
| data.items.operator         | 小程序                        | String   |              |
| data.items.event_desc       | 用户多了30积分,无冻结时间     | String   |              |
| data.items.order_items      | -                             | Object   |              |
| data.items.create_time      | 2022-06-16 11:45:23           | String   |              |
| data.items.update_time      | 2022-06-16 11:45:23           | String   |              |



## 积分场景信息
- GET /api/crm/mgr/points/{crm_id}/scene_info
- 请求参数 无
- 返回结果 produce_scene 累加场景 consume_scene 扣减场景

```json
{
    "code": 0,
    "msg": "OK",
    "data": {
        "produce_scene": [
            {
                "name": "用户登录",
                "code": "user_login"
            },
            {
                "name": "用户登录",
                "code": "user_login"
            },
            {
                "name": "签到打卡",
                "code": "user_sign"
            },
            {
                "name": "分享商品",
                "code": "share_goods"
            },
            {
                "name": "邀请新人入会送积分",
                "code": "invite_new"
            },
            {
                "name": "注册送积分",
                "code": "register"
            },
            {
                "name": "活动送积分",
                "code": "campaign"
            }
        ],
        "consume_scene": [
            {
                "name": "积分折扣",
                "code": "user_discount"
            }
        ]
    }
}
```

## 会员积分增量数据获取
- 请求路径
    - 积分明细 POST /api/crm/mgr/points/{crm_id}/history/increment
    - 会员积分概览信息 POST /api/crm/mgr/points/{crm_id}/summary/increment
    - 会员注册来源记录 POST /api/crm/mgr/member/{crm_id}/source/increment
    - 会员注册信息  POST  /api/crm/mgr/member/{crm_if}/info/increment
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

 - 请求例子

```shell
curl --location --request POST --X POST 'http://127.0.0.1:21100/api/crm/mgr/points/10080/history/increment' \
--header 'Content-Type: application/json' \
--data '{
    "page_id":1,
    "page_size":10,
    "order_by":"update_time",
    "order_asc":0,
    "time_start":0,
    "time_end": 1657184919
}'
```