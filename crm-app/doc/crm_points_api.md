
## /eros_crm/积分事件接口

## /eros_crm/积分事件接口/积分累积指定积分值

#### 接口URL

> 127.0.0.1:21100/api/crm/points/10080/produce/direct

#### 请求方式

> POST

#### Content-Type

> json

#### 请求Body参数

```javascript
{
    "event_no": "EACH20220615202826397549953503",
    "member_no": "ec_18165fd7455_JGhyfyLmX",
    "action_scene": "order_pay",
    "event_type":"order",
    "points": 20,
    "event_at": "2022-06-15 18:00:00",
    "expire_days": 180,
    "freeze_hours": 0,
    "store_code": "ec_mall",
    "cost_center": "cost_center001",
    "operator":"小程序",
    "event_desc":"用户购买了100元酸奶",
    "order_info":{}
}
```

| 参数名                   | 示例值                            | 参数类型   | 是否必填 | 参数描述            |
|-----------------------|--------------------------------|--------|------|-----------------|
| event_no              | EACH20220615202826397549953509 | String | 是    | -               |
| member_no             | ec_18165fd7455_JGhyfyLmX       | String | 是    | -               |
| action_scene          | order_pay                      | String | 否    | 规则场景 用于记录场景     |
| event_type            | order                          | String | 是    | -               |
| points                | 20                             | Number | 是    | -               |
| event_at              | 2022-06-15 18:00:00            | String | 否    | -               |
| expire_days           | 180                            | Number | 否    | -               |
| freeze_hours          | 48                             | Number | 否    | -               |
| store_code            | ec_mall                        | String | 否    | -               |
| cost_center           | cost_center001                 | String | 否    | -               |
| operator              | 小程序                            | String | 否    | -               |
| event_desc            | 用户购买了100元酸奶                    | String | 否    | -               |
| order_info            | 订单信息                           | object | 否    | 使用积分规则时填写订单商品信息 |
| order_info.order_sn   | 商品id                           | string | 是    | -               |
| order_info.pay_amount | 支付金额                           | int    | 是    | -               |
| order_info.item_list  | 商品信息                           | array  | 是    | -               |

> order_info 订单的标准信息


## /eros_crm/积分事件接口/积分累积by规则

#### 接口URL

> POST /api/crm/points/10080/produce/by_rule

#### 请求Body参数

```javascript
{
    "event_no": "EACH20220615202826397549953501",
    "member_no": "ec_18165fd7455_JGhyfyLmX",
    "action_scene": "user_login",
    "event_type":"event",
    "store_code": "ec_mini",
    "operator":"小程序登录",
    "event_desc":"用户登录了系统"
}
```

```javascript
{
    "event_no": "EACH20220615202826397549953503",
    "member_no": "ec_18165fd7455_JGhyfyLmX",
    "action_scene": "order_pay",
    "event_type":"order",
    "event_at": "2022-06-15 18:00:00",
    "expire_days": 180,
    "freeze_hours": 0,
    "store_code": "ec_mall",
    "cost_center": "cost_center001",
    "operator":"系统",
    "event_desc":"用户购买了100元酸奶",
    "order_items": {}
}
```

| 参数名           | 示例值                            | 参数类型    | 是否必填  | 参数描述                           |
|:--------------|:-------------------------------|:--------|:------|:-------------------------------|
| event_no      | EACH20220615202826397549953501 | String  | 是     | -                              |
| member_no     | ec_18165fd7455_JGhyfyLmX       | String  | 是     | -                              |
| action_scene  | user_login                     | String  | 是     | 规则场景                           |
| rule_id       | 1                              | int     | 否     | 场景规则id指定的话，使用这个规则来增加积分         |
| points        | 10                             | int     | 否     | 活动场景指定积分值，使用该积分值，积分规则只计算过期冻结时间 |
| event_type    | event                          | String  | 是     | order 或event                   |
| store_code    | ec_mini                        | String  | 是     | -                              |
| operator      | 小程序登录                          | String  | 是     | -                              |
| event_desc    | 用户登录了系统                        | String  | 是     | -                              |
| order_items   | 订单信息                           | object  | 否     | order类型必填 使用积分规则时填写订单信息        |

> order_items 字段解释 订单信息含商品item_list




## /eros_crm/积分事件接口/积分消耗指定积分

#### 接口URL

> 127.0.0.1:21100/api/crm/points/10080/consume/direct

#### 请求方式

> POST

#### Content-Type

> json

#### 请求Body参数

```javascript
{
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
}
```

| 参数名           | 示例值                            | 参数类型   | 是否必填 | 参数描述 |
|---------------|--------------------------------|--------|------|------|
| event_no      | EACH20220615202826397549953504 | String | 是    | -    |
| member_no     | ec_18165fd7455_JGhyfyLmX       | String | 是    | -    |
| action_scene  | user_discount                  | String | 否    | 规则场景 |
| points        | 10                             | Number | 是    | -    |
| event_at      | 2022-06-15 18:00:00            | String | 否    | -    |
| store_code    | ec_mall                        | String | 否    | -    |
| cost_center   | cost_center001                 | String | 否    | -    |
| campaign_code | 618                            | String | 否    | -    |
| operator      | 积分商城                           | String | 否    | -    |
| event_desc    | 用户消耗了10个积分                     | String | 否    | -    |



## /eros_crm/积分事件接口/积分转赠接口

#### 接口URL

> 127.0.0.1:21100/api/crm/points/10080/transfer

#### 请求方式

> POST

#### Content-Type

> json

#### 请求Body参数

```javascript
{
    "transfer_no": "EACH20220615202826397549953505",
    "from_user": "ec_18165fd7455_JGhyfyLmX",
    "to_user": "mc_18165fd7455_JGhyfyLm2",
    "trans_type":"by_poins",
    "points": 10
}
```

| 参数名      | 示例值                         | 参数类型 | 是否必填 | 参数描述 |
| ----------- | ------------------------------ | -------- | -------- | -------- |
| transfer_no | EACH20220615202826397549953505 | String   | 是       | -        |
| from_user   | ec_18165fd7455_JGhyfyLmX       | String   | 是       | -        |
| to_user     | mc_18165fd7455_JGhyfyLm2       | String   | 是       | -        |
| trans_type  | by_by_poins                    | String   | 是       | -        |
| points      | 10                             | Number   | 是       | -        |



## /eros_crm/积分事件接口/转赠领取积分





#### 接口URL

> 127.0.0.1:21100/api/crm/points/10080/accept

#### 请求方式

> POST

#### Content-Type

> json

#### 请求Body参数

```javascript
{
    "transfer_no": "EACH20220615202826397549953505",
    "member_no": "mc_18165fd7455_JGhyfyLm2"
}
```

| 参数名      | 示例值                         | 参数类型 | 是否必填 | 参数描述 |
| ----------- | ------------------------------ | -------- | -------- | -------- |
| transfer_no | EACH20220615202826397549953505 | String   | 是       | -        |
| from_user   | ec_18165fd7455_JGhyfyLmX       | String   | 是       | -        |
| to_user     | mc_18165fd7455_JGhyfyLm2       | String   | 是       | -        |
| trans_type  | by_by_poins                    | String   | 是       | -        |
| points      | 10                             | Number   | 是       | -        |



## /eros_crm/积分事件接口/冲正反累加





#### 接口URL

> 127.0.0.1:21100/api/crm/points/10080/reverse/produce

#### 请求方式

> POST

#### Content-Type

> json

#### 请求Body参数

```javascript
{
    "event_no": "20220615202826397549953509",
    "member_no": "ec_18165fd7455_JGhyfyLmX",
    "origin_event_no":"20220615202826397549953508",
    "allow_negative": false,
    "reverse_points": 10
}
```

| 参数名             | 示例值                            | 参数类型    | 是否必填 | 参数描述     |
|-----------------|--------------------------------|---------|------|----------|
| event_no        | 20220615202826397549953507     | String  | 是    | 事件no     |
| member_no       | ec_18165fd7455_JGhyfyLmX       | String  | 是    | 会员名称     |
| origin_event_no | EACH20220615202826397549953506 | String  | 是    | 要冲正的事件   |
| allow_negative  | -                              | Boolean | 是    | 是否允许冲正为负 |
| event_at        | 2022-06-16 09:00:00            | String  | 否    | 事件发生的时间  |
| refund_info     |                                | object  | 否    | 售后单信息    |

> refund_info字段解释: 如果是订单退单引起的冲正事件，需要传递售后单信息

## /eros_crm/积分事件接口/冲正反扣减





#### 接口URL

> 127.0.0.1:21100/api/crm/points/10080/reverse/consume

#### 请求方式

> POST

#### Content-Type

> json

#### 请求Body参数

```javascript
{
    "event_no": "20220615202826397549953514",
    "member_no": "ec_18165fd7455_JGhyfyLmX",
    "origin_event_no":"20220615202826397549953513",
    "reverse_points":20
}
```

| 参数名          | 示例值                         | 参数类型 | 是否必填 | 参数描述       |
| --------------- | ------------------------------ | -------- | -------- | -------------- |
| event_no        | 20220615202826397549953507     | String   | 是       | 事件no         |
| member_no       | ec_18165fd7455_JGhyfyLmX       | String   | 是       | 会员名称       |
| origin_event_no | EACH20220615202826397549953506 | String   | 是       | 要冲正的事件   |
| event_at        | 2022-06-16 09:00:00            | String   | 否       | 事件发生的时间 |
| reverse_points  | -                              | Integer  | 否       | 部分冲正积分数 |



## /eros_crm/积分事件接口/积分明细查询





#### 接口URL

> 127.0.0.1:21100/api/crm/points/10080/history

#### 请求方式

> POST

#### Content-Type

> json

#### 请求Body参数

```javascript
{
    "search_type":"produce",
    "start_time":"2022-06-01 12:00:00",
    "end_time":"2022-07-01 12:00:00",
    "member_no":"ec_18165fd7455_JGhyfyLmX"
}
```

| 参数名           | 示例值                      | 参数类型   | 是否必填 | 参数描述                                                          |
|---------------|--------------------------|--------|------|---------------------------------------------------------------|
| search_type   | produce                  | String | 否    | 搜索类型"produce", "consume", "transfer", "accept" expired freeze |
| start_time    | 2022-06-01 12:00:00      | String | 否    | 开始时间                                                          |
| end_time      | 2022-07-01 12:00:00      | String | 否    | 结束时间                                                          |
| member_no     | ec_18165fd7455_JGhyfyLmX | String | 否    | 会员名称                                                          |
| mobile        | 18608011234              | String | 否    | 手机号码                                                          |
| action_scene  | -                        | Object | 否    | 规则场景                                                          |
| campaign_code | -                        | Object | 否    | -                                                             |
| stroe_code    | -                        | Object | 否    | -                                                             |
| cost_center   | -                        | Object | 否    | -                                                             |



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
                "campaign_code": null,
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
| data.items.campaign_code    | -                             | Object   |              |
| data.items.operator         | 小程序                        | String   |              |
| data.items.event_desc       | 用户多了30积分,无冻结时间     | String   |              |
| data.items.order_items      | -                             | Object   |              |
| data.items.create_time      | 2022-06-16 11:45:23           | String   |              |
| data.items.update_time      | 2022-06-16 11:45:23           | String   |              |


## 积分概览
- 请求 GET /api/crm/points/{crm_id}/summary

- 请求例子

```shell
 curl --location --request GET --X GET 'https://dev.quickshark.cn/api/crm/mgr/app/points/summary?member_no=M220704308572703018'
```

- 返回结果  

| 字段             | 说明         |
|----------------|------------|
| total_points   | 累积积分       |
| freeze_points  | 冻结积分       |
| expired_points | 过期积分       |
| active_points  | 可用积分       |
| used_points    | 已使用积分(含转增) |
| future_expired | 7天快过期      |



```json
{
	"code": 0,
	"msg": "OK",
	"data": {
		"detail_id": 26,
		"crm_id": "10080",
		"member_no": "M220704308572703018",
		"total_points": 100030,
		"freeze_points": 0,
		"expired_points": 0,
		"active_points": 97799,
		"used_points": 2231,
		"future_expired": 0,
		"create_time": "2022-07-05 15:28:24",
		"update_time": "2022-07-21 16:47:53"
	}
}
```

## 积分模块

### 积分直接转赠接口
- 请求 POST  /api/crm/points/<crm_id>/transfer/direct
- 请求参数

| 参数          | 类型     | 必填  | 说明                |
|-------------|--------|-----|-------------------|
| transfer_no | string | yes | 转赠事件唯一id，小程序端控制唯一性 |
| from_user   | string | yes | 发起转赠会员号           |
| to_user     | string | yes | 接受转赠会员号           |  
| points      | float  | yes | 发起转赠的积分值  支持4位小数  |

- 请求例子
- 返回结果