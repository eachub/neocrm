

##  适配层接口
### 会员画像/指标计算

- 请求 GET /api/crm/mgr/adapt/member/10080/member_attrs
- 请求参数member_no

- 请求例子

```shell
curl --location --request GET --X GET 'http://127.0.0.1:21300/api/crm/mgr/adapt/member/10080/member_attrs?member_no=M220704308572703018'
```

- 返回结果

```json
{
	"code": 0,
	"msg": "OK",
	"data": {
		"all_mounts": null,
		"order_times_30": null,
		"mounts_30": null,
		"app_times_30": 0,
		"add_cards_30": 0
	}
}
```
### 会员画像/会员行为地铁图获取

- 请求 POST /api/crm/mgr/adapt/member/events

- 请求参数

| 参数                  | 类型     | 必须  | 说明           |
|:--------------------|:-------|:----|:-------------|
| member_no           | string | 是   |              |
| dr                  | string | 是   | ～连接的时间范围     |
| page_size           | int    | 是   | 页数           |
| max_create_time     | string | 否   | 请求返回的字段 分页使用 |

> 翻页逻辑：接口返回的 nex_page=true 则有下一页 携带上max_create_time参数进行下一页的请求
> 

- 请求例子

```shell
curl --location --request POST --X POST 'https://dev.quickshark.cn/api/crm/mgr/adapt/member/events' \
--header 'Content-Type: application/json' \
--data '{
    "member_no": "M220704308572703018",
    "dr": "2021-01-31~2022-06-01",
    "page_size": 10,
    "next_max_create_time": null
}
'
```

- 返回结果

```json
{
	"code": 0,
	"msg": "OK",
	"data": {
		"items": [
			{
				"date": "2021-09-01",
				"events": [
					{
						"event_name": "添加购物车",
						"create_time": "2021-09-01 14:22:48",
						"event_id": 7,
						"source": "wmp",
						"time_str": "14:22:48"
					},
					{
						"event_name": "添加购物车",
						"create_time": "2021-09-01 00:03:41",
						"event_id": 2,
						"source": "wmp",
						"time_str": "00:03:41"
					}
				]
			},
			{
				"date": "2021-08-31",
				"events": [
					{
						"event_name": "添加购物车",
						"create_time": "2021-08-31 23:39:41",
						"event_id": 1,
						"source": "wmp",
						"time_str": "23:39:41"
					}
				]
			}
		],
		"next_max_create_time": "2021-09-01 14:22:48",
		"nex_page": false,
		"page_size": 10
	}
}
```

### 会员列表/手动修改积分

- 请求 POST api/crm/mgr/adapt/points/change_points

- 请求参数

| 参数        | 类型     | 必须  | 说明                  |
|-----------|--------|-----|---------------------|
| member_no | string | 是   | 会员号                 |
| points    | int    | 是   | 变更的积分值              |
| type      | string | 是   | 增加produce 扣减consume |
| operator          | string | 否   | 操作者                 |
| expire_days          | int    | 否   | 过期时间 单位day 增加积分要填   | 

- 请求例子

```shell
curl --location --request POST --X POST 'http://127.0.0.1:21300/api/crm/mgr/adapt/points/change_points' \
--header 'Content-Type: application/json' \
--data '{
    "member_no": "M220704308572703018",
    "points": 10,
    "type": "produce",
    "operator": "后台管理",
    "expire_days": 90
}'
```
 
- 返回结果 code msg data


### 查询小程序页面路径接口

- 请求 GET api/crm/mgr/cms/application/list_with_page

- 请求例子

```shell
curl  'https://dev.quickshark.cn/api/crm/mgr/cms/application/list_with_page'
```

- 返回结果

```json
{
	"code": 0,
	"data": {
		"app_path": [{
			"app_id": "wx8d411ed85c2ea4aa",
			"app_name": "特洛益",
			"path": [{
				"app_id": "wx8d411ed85c2ea4aa",
				"app_name": "特洛益",
				"is_neoapp": false,
				"page_id": 12430,
				"page_path": "/pages/index/index",
				"page_name": "首页"
			}]
		}]
	},
	"msg": "处理成功"
}
```

### 查询用户信息

- 请求 GET api/crm/mgr/auth/center

- 请求例子

```shell
curl --header "AUTHORIZATION:Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJISmJoQTBlVGdxckZPM1RmbjJxYUg2LUkzMFJwdG5KRjBNRzZLZ3lPSGxZIn0.eyJleHAiOjE2NTkxMDgzNzUsImlhdCI6MTY1OTEwODA3NSwiYXV0aF90aW1lIjoxNjU5MTA2MjI0LCJqdGkiOiI5NDU2ZmRjYi1jOWZiLTRmY2EtYTk4OC1mMmI0N2M0OTE2N2UiLCJpc3MiOiJodHRwczovL2Rldi5xdWlja3NoYXJrLmNuL2tleWNsb2FrL3JlYWxtcy9UUk9ZIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6IjRiMmNkNmIyLWQ3ODUtNDYyNC04NDQwLTMxM2EzYWFlOTIxMCIsInR5cCI6IkJlYXJlciIsImF6cCI6IkNSTSIsInNlc3Npb25fc3RhdGUiOiIwMmFjNzIxNi00YWI5LTQ0MjItYTdlZS1iZTk2YzJiZDhiYTUiLCJhY3IiOiIwIiwiYWxsb3dlZC1vcmlnaW5zIjpbIiJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsImRlZmF1bHQtcm9sZXMtdHJveSJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfSwiQ1JNIjp7InJvbGVzIjpbIui_kOiQpeS6uuWRmCIsIueuoeeQhuWRmCJdfX0sInNjb3BlIjoicm9sZXMgcHJvZmlsZSBlbWFpbCIsInNpZCI6IjAyYWM3MjE2LTRhYjktNDQyMi1hN2VlLWJlOTZjMmJkOGJhNSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwibmFtZSI6Ium7hOm5pCIsInByZWZlcnJlZF91c2VybmFtZSI6Im5laWxAZWFjaHViLmNuIiwiZ2l2ZW5fbmFtZSI6Ium7hOm5pCIsImVtYWlsIjoibmVpbEBlYWNodWIuY24ifQ.aTg_sMLzqVAhLHmQDQLlCcaCc2FE2pdxHXzzibK8dZM51WUq6Zfl8Y2p5kZXQA1Lc0HXJetqC_gkwknSMv0nbS051Ly0KNRw2K3Zj5zViZKuxHlI-Sao9ZkqL3HB4X6Y0LNOtEu_5sR3ZnLnNdc3Ue0iqF1sF89Qp8h-2Mge08vqHTXwkdcCRiqitLDXMYcmFD0G22Vh2L84nVWF7HOrvofaDXDaVEFASfRwbk1aSf2kY23QuhaXA-GkN7jCgf5k44v2-ePYuopKDx93CHXk1Zwa4ecFyh22spGA_wWBITJ4UtRwvefn1NMWQyWaWKoOlFP_D2W6UceItwKomGPOFA" "https://dev.quickshark.cn/api/crm/mgr/auth/center"
```

- 返回结果

```python
{
	"code": 0,
	"msg": "ok",
	"data": {
		"user_id": "4b2cd6b2-d785-4624-8440-313a3aae9210",
		"nickname": "黄鹤",
		"instance_id": "neo_instance_id",
		"email": "neil@eachub.cn",
		"role": ["运营人员", "管理员"] #角色名称
	}
}
```


### 活动模版查看

- 请求 GET api/crm/mgr/cam/campaign/preview
- 请求参数

| 参数        | 类型     | 必须  | 说明                  |
|-----------|--------|-----|---------------------|
| campaign_id | string | 是   | 活动ID                 |
| child_campaign_no | string | 否   | 比如对于会员日活动的child_campaign_no                 |

- 请求例子

```shell
curl "https://dev.quickshark.cn/api/crm/mgr/cam/campaign/preview?campaign_id=60011"
```

- 返回结果 图片文件



### 商家券统计领取或者核销TOP
   * 入口：/api/crm/mgr/coupon/wxpay/statistical_top
   * 方法：get
   * curl命令样例：
```bash
领取top10
curl "https://dev.quickshark.cn/api/crm/mgr/coupon/wxpay/statistical_top?begin_time=2022-07-06%2000%3A00%3A00&end_time=2022-07-16%2023%3A59%3A59&event_type=receive&top=10"
核销top10
curl "https://dev.quickshark.cn/api/crm/mgr/coupon/wxpay/statistical_top?begin_time=2022-07-06%2000%3A00%3A00&end_time=2022-07-16%2023%3A59%3A59&event_type=redeem&top=10"
```
字段|类型|必填|取值样例|说明
---|---|---|---|---
begin_time|string|是|2022-07-16 00:00:00|事件开始时间
end_time|string|是|2022-07-16 23:59:59|事件结束时间
event_type|string|是|receive或者redeem|事件类型
top|int|是｜排名数量

### 统计商家券领取核销total值
   * 入口：/api/crm/mgr/coupon/wxpay/statistical_total
   * 方法：get
   * curl命令样例：
```bash
curl "https://dev.quickshark.cn/api/crm/mgr/coupon/wxpay/statistical_total?begin_time=2022-07-06&end_time=2022-07-16"
```
字段|类型|必填|取值样例|说明
---|---|---|---|---
begin_time|string|是|2022-07-16|事件开始时间
end_time|string|是|2022-07-16|事件结束时间

### 统计商家券领取核销趋势图
   * 入口：/api/crm/mgr/coupon/wxpay/statistical_time
   * 方法：get
   * curl命令样例：
```bash
curl "https://dev.quickshark.cn/api/crm/mgr/coupon/wxpay/statistical_time?begin_time=2022-07-06&end_time=2022-07-16"
curl "https://dev.quickshark.cn/api/crm/mgr/coupon/wxpay/statistical_time?begin_time=2022-07-15&end_time=2022-07-16"
```
字段|类型|必填|取值样例|说明
---|---|---|---|---
begin_time|string|是|2022-07-16|事件开始时间
end_time|string|是|2022-07-16|事件结束时间


### 卡券控制台查询商家券流水接口
   * 入口：/api/crm/mgr/coupon/get_member_coupon_list
   * 方法：post
   * curl命令样例：
```bash
curl -d '{"event_type":"receive","member_no":"M220803307210000852","page_size":5,"start_at":"2022-07-21","end_at":"2022-07-30"}' "https://dev.quickshark.cn/api/crm/mgr/coupon/get_member_coupon_list"
curl -d '{"event_type":"receive","mobile":"18516695622","page_size":5,"start_at":"2022-07-21","end_at":"2022-07-30"}' "https://dev.quickshark.cn/api/crm/mgr/coupon/get_member_coupon_list"
```
字段|类型|必填|取值样例|说明
---|---|---|---|---
event_type|string|是|receive|领取receive,核销redeem
member_no|string|否|M220803307210000852|会员号
page_size|int|否|10|页码记录数量
page|int|否|1|页码
start_at|string|否|2022-07-16|事件开始时间
end_at|string|否|2022-07-20|事件结束时间,不包含


### 卡券控制台导出商家券流水Excel表格
   * 入口：/api/crm/mgr/coupon/export_member_coupon_list
   * 方法：post
   * curl命令样例：
```bash
curl -d '{"event_type":"receive","event_id_list":[1315480]}' "https://dev.quickshark.cn/api/crm/mgr/coupon/export_member_coupon_list"
```
字段|类型|必填|取值样例|说明
---|---|---|---|---
event_type|string|是|receive|领取receive,核销redeem
event_id_list|array|是|[1315480]|导出的event id


###  搜索素材列表,支持审批状态
   + 入口：/api/crm/mgr/cms/material/search
   + 请求：GET
   + curl命令样例：
```bash
curl "https://dev.quickshark.cn/api/crm/mgr/cms/material/search?language=cn&mat_cat_id=30002&page_id=1&page_size=6&material_source=0&material_types=0%2C1%2C2%2C3%2C4%2C5%2C7%2C8%2C9&keyword=" --header "AUTHORIZATION:Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJISmJoQTBlVGdxckZPM1RmbjJxYUg2LUkzMFJwdG5KRjBNRzZLZ3lPSGxZIn0.eyJleHAiOjE2NjAzNjI1MDcsImlhdCI6MTY2MDM2MjIwNywiYXV0aF90aW1lIjoxNjYwMzYyMjA3LCJqdGkiOiI5OWFkNjJlMy1iYzZjLTRjZjAtYmMwMi05MjdmNzQ3YTVmZTUiLCJpc3MiOiJodHRwczovL21pbmlhcHAtdWF0LnRyb3lsaWZlLmNuL2F1dGgvcmVhbG1zL1RST1kiLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoiNGIyY2Q2YjItZDc4NS00NjI0LTg0NDAtMzEzYTNhYWU5MjEwIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiQ1JNIiwic2Vzc2lvbl9zdGF0ZSI6Ijg4ODA4M2RjLTY2NDctNDUyNC1hMzcxLTRiY2MwMjRjNWViOCIsImFjciI6IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIiwiZGVmYXVsdC1yb2xlcy10cm95Il19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiQ1JNIjp7InJvbGVzIjpbIueuoeeQhuWRmCJdfX0sInNjb3BlIjoicm9sZXMgcHJvZmlsZSBlbWFpbCIsInNpZCI6Ijg4ODA4M2RjLTY2NDctNDUyNC1hMzcxLTRiY2MwMjRjNWViOCIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwibmFtZSI6Ium7hOm5pCIsInByZWZlcnJlZF91c2VybmFtZSI6Im5laWxAZWFjaHViLmNuIiwiZ2l2ZW5fbmFtZSI6Ium7hOm5pCIsImVtYWlsIjoibmVpbEBlYWNodWIuY24ifQ.XkWV-LoMo691vHW0b8Vt6pRke6ZQS4Pwl40yEIP3pP0d1b2MFhxXSjAdZmmJFNDghfQYyQXZRyyQB189wJRZxV8Yt0J_Pk9o8EvqxIfoD-uscSBkVRV1tBhFzud94R7ix8YZ4VmJMkV6GQdac2f2UPalM5Ed7H9wbkt3M7T3w4sbhoMhu7l2rjw3dAZ7xZy7Rd8PjhSkDCQJWDVT5WPoV2rFNBeRWtiff9S8m1xc5zXGu5RTci84GxwQqtM4Rmdnej2HZ2v7-17R8npHY8LoEU43gfC_Bqjq8vmQH_dzq8gJ-YyhWwp-nO4ZD8kFAXgJW0BFT-8CLn3e45QZO8nuOQ"
```
   + 入参：
   + 
字段|类型|必填|取值样例|说明
---|---|---|---|---
tag|string|否|美白|标签，多个支持逗号分隔
mtype|int|否|0|类别（0普通图；1透明背景图；2视频；3长图；4音频；5虚拟偶像），多个支持逗号分隔
dtr|string|否|16011100000~16033300000|创建时间范围
mat_cat_id|int|否|30004|素材所属类目
page_id|int|否|1|第几页，从1开始
page_size|int|否|20|每页多少条，取值2-100
status|int|否|1|1已发布，0未发布。不传展示所有。在素材选择框中必须传status=1

   + 返回：
```json
{
    "code": 0,
    "msg": "搜索成功",
    "data": {
        "total": 1,
        "material_list": [{
            "material_id": 100000000,
            "instance_id": "mt000000000-neonft",
            "material_type": 0,
            "base_path": "/2020-11-30/354a023d-2101-457b-89e3-6ed9593af704.jpg",
            "width": 0,
            "height": 0,
            "size": 32864,
            "origin_material_id": null,
            "origin_filename": "t0.jpg",
            "tags": ["清纯", "靓丽"],
            "title": "t0",
            "cover": null,
            "apply_status": 1 #审批状态：#0，待审批, 1-审批中；2-已通过；3-已驳回；4-已撤销
        }]
    }
}
```


###  查询待审批的列表
   + 入口：/api/crm/mgr/cms/apply/search
   + 请求：GET
   + curl命令样例：
```bash
curl "https://dev.quickshark.cn/api/crm/mgr/cms/apply/search?language=cn&page_id=1&page_size=20" --header "AUTHORIZATION:Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJISmJoQTBlVGdxckZPM1RmbjJxYUg2LUkzMFJwdG5KRjBNRzZLZ3lPSGxZIn0.eyJleHAiOjE2NjAzNjI1MDcsImlhdCI6MTY2MDM2MjIwNywiYXV0aF90aW1lIjoxNjYwMzYyMjA3LCJqdGkiOiI5OWFkNjJlMy1iYzZjLTRjZjAtYmMwMi05MjdmNzQ3YTVmZTUiLCJpc3MiOiJodHRwczovL21pbmlhcHAtdWF0LnRyb3lsaWZlLmNuL2F1dGgvcmVhbG1zL1RST1kiLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoiNGIyY2Q2YjItZDc4NS00NjI0LTg0NDAtMzEzYTNhYWU5MjEwIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiQ1JNIiwic2Vzc2lvbl9zdGF0ZSI6Ijg4ODA4M2RjLTY2NDctNDUyNC1hMzcxLTRiY2MwMjRjNWViOCIsImFjciI6IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIiwiZGVmYXVsdC1yb2xlcy10cm95Il19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiQ1JNIjp7InJvbGVzIjpbIueuoeeQhuWRmCJdfX0sInNjb3BlIjoicm9sZXMgcHJvZmlsZSBlbWFpbCIsInNpZCI6Ijg4ODA4M2RjLTY2NDctNDUyNC1hMzcxLTRiY2MwMjRjNWViOCIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwibmFtZSI6Ium7hOm5pCIsInByZWZlcnJlZF91c2VybmFtZSI6Im5laWxAZWFjaHViLmNuIiwiZ2l2ZW5fbmFtZSI6Ium7hOm5pCIsImVtYWlsIjoibmVpbEBlYWNodWIuY24ifQ.XkWV-LoMo691vHW0b8Vt6pRke6ZQS4Pwl40yEIP3pP0d1b2MFhxXSjAdZmmJFNDghfQYyQXZRyyQB189wJRZxV8Yt0J_Pk9o8EvqxIfoD-uscSBkVRV1tBhFzud94R7ix8YZ4VmJMkV6GQdac2f2UPalM5Ed7H9wbkt3M7T3w4sbhoMhu7l2rjw3dAZ7xZy7Rd8PjhSkDCQJWDVT5WPoV2rFNBeRWtiff9S8m1xc5zXGu5RTci84GxwQqtM4Rmdnej2HZ2v7-17R8npHY8LoEU43gfC_Bqjq8vmQH_dzq8gJ-YyhWwp-nO4ZD8kFAXgJW0BFT-8CLn3e45QZO8nuOQ"
```
   + 入参：
   + 
字段|类型|必填|取值样例|说明
---|---|---|---|---
page_id|int|否|1|第几页，从1开始
page_size|int|否|20|每页多少条，取值2-100
   + 返回：
```json
{
	"code": 0,
	"msg": "ok",
	"data": {
		"list": [{
			"material_id": 10000454,
			"instance_id": "neo_instance_id",
			"material_type": 0,
			"base_path": "/2022-08-13/33b3f555-c6e4-47c6-bd27-039f2996f4e4.gif",
			"width": 580,
			"height": 772,
			"size": 468455,
			"origin_material_id": null,
			"origin_filename": "test.gif",
			"tags": null,
			"title": "pic123",
			"cover": null,
			"text": null,
			"macro_list": null,
			"mini_app_id": null,
			"mini_app_path": null,
			"h5_url": null,
			"h5_desc": null,
			"material_no": "qMERsj2kto6RsvKYEBRjJB",
			"platform": [0],
			"remark": "123",
			"status": 0,
			"create_time": "2022-08-13 13:26:20",
			"apply_status": 0,
			"third_no": "9RbqHUvkVjpD66sq6Djo2D"
		}],
		"total": 1
	}
}
```

###  创建审批任务
   + 入口：/api/crm/mgr/cms/apply/create
   + 请求：GET
   + curl命令样例：
```bash
curl -d '{"material_nos":["qMERsj2kto6RsvKYEBRjJB"],"remark":"测试123"}' "https://dev.quickshark.cn/api/crm/mgr/cms/apply/create" --header "AUTHORIZATION:Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJISmJoQTBlVGdxckZPM1RmbjJxYUg2LUkzMFJwdG5KRjBNRzZLZ3lPSGxZIn0.eyJleHAiOjE2NjAzNjI1MDcsImlhdCI6MTY2MDM2MjIwNywiYXV0aF90aW1lIjoxNjYwMzYyMjA3LCJqdGkiOiI5OWFkNjJlMy1iYzZjLTRjZjAtYmMwMi05MjdmNzQ3YTVmZTUiLCJpc3MiOiJodHRwczovL21pbmlhcHAtdWF0LnRyb3lsaWZlLmNuL2F1dGgvcmVhbG1zL1RST1kiLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoiNGIyY2Q2YjItZDc4NS00NjI0LTg0NDAtMzEzYTNhYWU5MjEwIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiQ1JNIiwic2Vzc2lvbl9zdGF0ZSI6Ijg4ODA4M2RjLTY2NDctNDUyNC1hMzcxLTRiY2MwMjRjNWViOCIsImFjciI6IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIiwiZGVmYXVsdC1yb2xlcy10cm95Il19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiQ1JNIjp7InJvbGVzIjpbIueuoeeQhuWRmCJdfX0sInNjb3BlIjoicm9sZXMgcHJvZmlsZSBlbWFpbCIsInNpZCI6Ijg4ODA4M2RjLTY2NDctNDUyNC1hMzcxLTRiY2MwMjRjNWViOCIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwibmFtZSI6Ium7hOm5pCIsInByZWZlcnJlZF91c2VybmFtZSI6Im5laWxAZWFjaHViLmNuIiwiZ2l2ZW5fbmFtZSI6Ium7hOm5pCIsImVtYWlsIjoibmVpbEBlYWNodWIuY24ifQ.XkWV-LoMo691vHW0b8Vt6pRke6ZQS4Pwl40yEIP3pP0d1b2MFhxXSjAdZmmJFNDghfQYyQXZRyyQB189wJRZxV8Yt0J_Pk9o8EvqxIfoD-uscSBkVRV1tBhFzud94R7ix8YZ4VmJMkV6GQdac2f2UPalM5Ed7H9wbkt3M7T3w4sbhoMhu7l2rjw3dAZ7xZy7Rd8PjhSkDCQJWDVT5WPoV2rFNBeRWtiff9S8m1xc5zXGu5RTci84GxwQqtM4Rmdnej2HZ2v7-17R8npHY8LoEU43gfC_Bqjq8vmQH_dzq8gJ-YyhWwp-nO4ZD8kFAXgJW0BFT-8CLn3e45QZO8nuOQ"
```
   + 入参：
   + 
字段|类型|必填|取值样例|说明
---|---|---|---|---
material_nos|array|是|1|素材编号数组
remark|string|是|20|备注
   + 返回：如果创建成功，返回图片。企微扫码可以获取third_no，remark参数
```json
{
	"code": 30402,
	"msg": "素材(qMERsj2kto6RsvKYEBRjJB)已经在审批处理，提交失败。"
}
```


###  按照审批编号查询素材
   + 入口：/api/crm/mgr/cms/apply/task
   + 请求：GET
   + curl命令样例：
```bash
curl -d '{"third_no":"9RbqHUvkVjpD66sq6Djo2D"}' "https://dev.quickshark.cn/api/crm/mgr/cms/apply/task" --header "X-SHARK-SESSION-ID:2bace912558c470bb8354e9b4ac4dccb"
```
   + 入参：
   + 
字段|类型|必填|取值样例|说明
---|---|---|---|---
third_no|string|是|9RbqHUvkVjpD66sq6Djo2D|任务编号。企微扫描二维码中获取
   + 返回：如果创建成功，返回图片
```json
{
	"code": 0,
	"msg": "ok",
	"data": [{
		"material_id": 10000454,
		"instance_id": "neo_instance_id",
		"material_type": 0,
		"base_path": "/2022-08-13/33b3f555-c6e4-47c6-bd27-039f2996f4e4.gif",
		"width": 580,
		"height": 772,
		"size": 468455,
		"origin_material_id": null,
		"origin_filename": "test.gif",
		"tags": null,
		"title": "pic123",
		"cover": null,
		"text": null,
		"macro_list": null,
		"mini_app_id": null,
		"mini_app_path": null,
		"h5_url": null,
		"h5_desc": null,
		"material_no": "qMERsj2kto6RsvKYEBRjJB",
		"platform": [0],
		"remark": "123",
		"status": 0,
		"create_time": "2022-08-13 13:26:20",
		"apply_status": 1,
		"third_no": "9RbqHUvkVjpD66sq6Djo2D"
	}]
}
```

