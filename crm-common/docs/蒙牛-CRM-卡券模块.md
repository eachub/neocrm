## /卡券看板-趋势
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/dashbord/<crm_id>/card_trend

#### 请求方式
> GET

#### Content-Type
> json

#### 请求Body参数
```javascript

```
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
	"msg": "ok",
	"data": {
		"receive_num": 100,
		"receive_member_num": 100,
		"receive_num_list": [
			100,
			101
		],
		"receive_member_num_list": [
			100,
			101
		],
		"redeem_member_num": 100,
		"redeem_num_list": [
			100,
			101
		],
		"redeem_member_num_list": [
			100,
			101
		],
		"present_num": 100,
		"present_member_num": 100,
		"present_num_list": [
			100,
			101
		],
		"present_member_num_list": [
			100,
			101
		],
		"tdate": [
			"2022-05-18",
			"2022-05-19"
		]
	}
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | 0 | Number | 
msg | ok | String | 返回文字描述
data | - | Object | 返回数据
data.receive_num | 100 | Number | 领取卡券数
data.receive_member_num | 100 | Number | 领取会员数
data.receive_num_list | 100 | Number | 领取卡券数列表
data.receive_member_num_list | 100 | Number | 领取会员数列表
data.redeem_member_num | 100 | Number | 核销卡券的会员数
data.redeem_num_list | 100 | Number | 核销卡券数列表
data.redeem_member_num_list | 100 | Number | 核销卡券的会员数列表
data.present_num | 100 | Number | 转赠卡券数
data.present_member_num | 100 | Number | 转赠卡券的会员数
data.present_num_list | 100 | Number | 转赠卡券数列表
data.present_member_num_list | 100 | Number | 转赠卡券的会员数列表
data.tdate | 2022-05-18 | Array | 日期列表
## /卡券看板 -渠道统计
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/dashbord/<crm_id>/card_channel

#### 请求方式
> GET

#### Content-Type
> json

#### 请求Body参数
```javascript

```
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
	"msg": "ok",
	"data": {
		"receive_channel_list": [
			{
				"channel_name": "618大促",
				"receive_num": 122
			}
		],
		"redeem_channel_list": [
			{
				"channel_name": "微信小程序",
				"redeem_num": 111
			}
		]
	}
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | 0 | Number | 
msg | ok | String | 返回文字描述
data | - | Object | 返回数据
data.receive_channel_list | - | Object | 领取渠道
data.receive_channel_list.channel_name | 618大促 | String | 渠道名称
data.receive_channel_list.receive_num | 122 | Number | 领券数量
data.redeem_channel_list | - | Object | 核销渠道列表
data.redeem_channel_list.channel_name | 微信小程序 | String | 渠道名称
data.redeem_channel_list.redeem_num | 111 | Number | 核销数量
## /卡券看板 -领取与核销top
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/dashbord/<crm_id>/card_top

#### 请求方式
> GET

#### Content-Type
> json

#### 请求Body参数
```javascript

```
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
	"msg": "ok",
	"data": {
		"receive_top": [
			{
				"receive_num": 122,
				"card_id": 111111,
				"title": "满100减10"
			}
		],
		"redeem_top": [
			{
				"receive_num": 122,
				"card_id": 111112,
				"title": "满100减10"
			}
		]
	}
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | 0 | Number | 
msg | ok | String | 返回文字描述
data | - | Object | 返回数据
data.receive_top | - | Object | 领券top
data.receive_top.receive_num | 122 | Number | 领取卡券数
data.receive_top.card_id | 111111 | String | 卡券id
data.receive_top.title | 满100减10 | String | 卡券名称
data.redeem_top | - | Object | 核销top
data.redeem_top.receive_num | 122 | Number | 核销卡券数
data.redeem_top.card_id | 111112 | String | 卡券id
data.redeem_top.title | 满100减10 | String | 卡券名称
## /卡券
```text
暂无描述
```
#### 公共Header参数
参数名 | 示例值 | 参数描述
--- | --- | ---
暂无参数
#### 公共Query参数
参数名 | 示例值 | 参数描述
--- | --- | ---
暂无参数
#### 公共Body参数
参数名 | 示例值 | 参数描述
--- | --- | ---
暂无参数
#### 预执行脚本
```javascript
暂无预执行脚本
```
#### 后执行脚本
```javascript
暂无后执行脚本
```
## /卡券/卡券详情
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/card/<crm_id>/detail?card_id=wrfqwfwqfer14

#### 请求方式
> GET

#### Content-Type
> json

#### 请求Query参数
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
card_id | wrfqwfwqfer14 | String | 是 | -
#### 请求Body参数
```javascript

```
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
	"msg": "获取卡券详情成功",
	"data": {
		"coupon_id": 1,
		"crm_id": "instance_id22222222",
		"card_id": "21008fdbabd30c04548a56be6eed016c",
		"card_type": 1,
		"title": "满100减10",
		"subtitle": "618满100减10",
		"source": 1,
		"scene": "web",
		"notice": "适用说明",
		"rule": "使用须知",
		"date_type": 1,
		"begin_time": 1655481600,
		"end_time": 1655740799,
		"start_day_count": null,
		"expire_day_count": null,
		"weekdays": "0,1,6",
		"monthdays": "1,11,18,28",
		"day_begin_time": 0,
		"day_end_time": 86399,
		"total_quantity": 10000,
		"get_limit": 0,
		"use_limit": 0,
		"can_give_friend": true,
		"generate_type": 1,
		"generate_file": null,
		"cash_amount": 10,
		"cash_condition": 100,
		"discount": 0,
		"icon": "aa/bb/cc.jpg",
		"store_codes": "store_01, store_02",
		"cost_center": "NO12312513",
		"cost_type": 1,
		"cost_value": 2,
		"extra_info": {
			"bg_color": "#1111111",
			"jump_now_path": "/page/card/",
			"custom_menu_name": "卡券",
			"menu_jump_path": "/page/custom/"
		},
		"create_time": "2021-08-18 16:25:56",
		"update_time": "2021-08-19 14:09:20",
		"generate_info": {
			"generated": 400000,
			"un_generate": 0,
			"total": 400000
		},
		"receive_info": {
			"received": 8
		}
	}
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | 0 | Number | 
msg | 获取卡券详情成功 | String | 返回文字描述
data | - | Object | 返回数据
data.coupon_id | 1 | Number | 卡券id
data.crm_id | instance_id22222222 | String | crm_id
data.card_id | 21008fdbabd30c04548a56be6eed016c | String | 卡券id
data.card_type | 1 | Number | 卡券类型 0:代金券；1:折扣券；2:兑换券；3:包邮券；4:赠品券
data.title | 618满100减10 | String | 卡券标题
data.subtitle | 100减10 | Number | 卡券副标题
data.source | 1 | Number | 卡券类型  1微信商家券   2自制券
data.scene | web | Object | 适用场景说明
data.notice | 适用说明 | String | 使用说明：字数上限为15个
data.rule | 使用须知 | String | 使用须知：64K
data.date_type | 1 | String | 时间类型：1:固定时间范围；2:动态时间；3:永久有效
data.begin_time | 1655481600 | Number | 开始时间
data.end_time | 1655740799 | String | 结束时间
data.start_day_count | 3 | Number | 领取后几天生效(date_type=2时有值)
data.expire_day_count | 3 | Number | 领取后几天有效(date_type=2时有值)
data.weekdays | 0,1,6 | Integer | 一周内可以使用的天数
data.monthdays | 1,11,18,28 | Number | 一月内可以使用的天数
data.day_begin_time | 0 | Number | 当天可用开始时间，单位：秒，1代表当天0点0分1秒。示例值：3600
data.day_end_time | 86399 | Number | 当天可用结束时间，单位：秒，86399代表当天23点59分59秒。示例值：86399
data.total_quantity | 10000 | Number | 发券量
data.get_limit | 0 | Number | 领取限制 默认是0 表示不受限 如果是其余整数表示只能领取该数量
data.use_limit | 0 | Number | 使用限制 默认是0 表示不受限 如果是其余整数表示只能使用该数量
data.can_give_friend | true | Boolean | 是否可以转增 默认True
data.generate_type | 1 | Number | 券码生成类型  1系统生成  2外部导入
data.generate_file | - | String | 外部导入券码文件url
data.cash_amount | 10 | Number | 代金券：减免金额
data.cash_condition | 100 | Number | 代金券、折扣券、包邮券：起用金额
data.discount | 0 | Number | 折扣券：折扣率（八折取值0.8）
data.icon | aa/bb/cc.jpg | String | 卡券图标
data.store_codes | store_01, store_02 | String | 适用门店code列表
data.cost_center | NO12312513 | String | 成本中心编号
data.cost_type | 1 | Number | 成本费用类型  1固定金额  2百分比
data.cost_value | 2 | Number | 成本费用(>=0) cost_type=2时，如百分之八十,传80
data.extra_info | - | Object | 额外信息
data.extra_info.bg_color | #1111111 | String | 卡券背景色
data.extra_info.jump_now_path | /page/card/ | String | 立即使用跳转链接
data.extra_info.custom_menu_name | 卡券 | String | 底部自定义菜单名称
data.extra_info.menu_jump_path | /page/custom/ | String | 底部自定义菜单跳转路径
data.create_time | 2021-08-18 16:25:56 | String | 添加时间
data.update_time | 2021-08-19 14:09:20 | String | 更新时间
data.generate_info | - | Object | 已生成的卡券信息
data.generate_info.generated | 400000 | Number | 已经生成的数量
data.generate_info.un_generate | 0 | Number | 还没有生成的数量
data.generate_info.total | 400000 | Number | 总量
data.receive_info | - | Object | 领券的卡券信息
data.receive_info.received | 8 | Number | 已经领取的卡券数量
## /卡券/卡券列表
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/card/<crm_id>/list?page_id=1&page_size=10&card_type=0&source=1&scene=web

#### 请求方式
> GET

#### Content-Type
> json

#### 请求Query参数
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
page_id | 1 | String | 否 | 分页id
page_size | 10 | String | 否 | 分页大小
card_type | 0 | String | 否 | 卡券类型 0:代金券；1:折扣券；2:兑换券；3:包邮券；4:赠品券
source | 1 | String | 否 | 类型id 1微信券 2自制券
scene | web | String | 否 | 筛选：适用场景
#### 请求Body参数
```javascript

```
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
	"msg": "获取卡券信息成功",
	"data": {
		"total": 4,
		"results": [
			{
				"coupon_id": 1,
				"crm_id": "instance_id22222222",
				"card_id": "21008fdbabd30c04548a56be6eed016c",
				"card_type": 1,
				"title": "满100减10",
				"subtitle": "618满100减10",
				"source": 1,
				"scene": "web",
				"notice": "适用说明",
				"rule": "使用须知",
				"date_type": 1,
				"begin_time": 1655481600,
				"end_time": 1655740799,
				"start_day_count": null,
				"expire_day_count": null,
				"weekdays": "0,1,6",
				"monthdays": "1,11,18,28",
				"day_begin_time": 0,
				"dayend_time": 86399,
				"total_quantity": 10000,
				"get_limit": 0,
				"use_limit": 0,
				"can_give_friend": true,
				"generate_type": 1,
				"generate_file": null,
				"cash_amount": 10,
				"cash_condition": 100,
				"discount": 0,
				"icon": "aa/bb/cc.jpg",
				"store_codes": "store_01, store_02",
				"cost_center": "NO12312513",
				"cost_type": 1,
				"cost_value": 2,
				"extra_info": {
					"bg_color": "#1111111",
					"jump_now_path": "/page/card/",
					"custom_menu_name": "卡券",
					"menu_jump_path": "/page/custom/"
				},
				"create_time": "2021-08-18 16:25:56",
				"update_time": "2021-08-19 14:09:20",
				"generate_info": {
					"generated": 400000,
					"un_generate": 0,
					"total": 400000
				},
				"receive_info": {
					"received": 8
				}
			}
		]
	}
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | 0 | Number | 
msg | 获取卡券信息成功 | String | 返回文字描述
data | - | Object | 返回数据
data.total | 4 | Number | 结果总数
data.results | - | Object | 结果列表
data.results.coupon_id | 1 | Number | 卡券iid
data.results.crm_id | instance_id22222222 | String | crm_id
data.results.card_id | 21008fdbabd30c04548a56be6eed016c | Number | 卡券id
data.results.card_type | 1 | Number | 卡券类型 0:代金券；1:折扣券；2:兑换券；3:包邮券；4:赠品券
data.results.title | 满100减10 | String | 卡券名称
data.results.subtitle | 618满100减10 | Number | 卡券副标题
data.results.source | 1 | Number | 卡券来源  1微信商家券  2自制券
data.results.scene | web | String | 适用场景
data.results.notice | 适用说明 | String | 适用说明
data.results.rule | 使用须知 | String | 使用须知
data.results.date_type | 1 | Number | 时间类型：1:固定时间范围；2:动态时间；3:永久有效
data.results.begin_time | 1655481600 | Number | 卡券有效期 开始时间
data.results.end_time | 1655740799 | Number | 卡券有效期 结束时间
data.results.start_day_count | - | Object | 领取后几天生效(date_type=2时有值)
data.results.expire_day_count | - | Object | 领取后几天有效(date_type=2时有值)
data.results.weekdays | 0,1,6 | Number | 一周内可以使用的天数
data.results.monthdays | 1,11,18,28 | Number | 一月内可以使用的天数
data.results.day_begin_time | 0 | Number | 当天可用开始时间，单位：秒，1代表当天0点0分1秒。示例值：3600
data.results.dayend_time | 86399 | Number | 当天可用结束时间，单位：秒，86399代表当天23点59分59秒。示例值：86399
data.results.total_quantity | 10000 | Number | 发券量
data.results.get_limit | 0 | Number | 领取限制 默认是0 表示不受限 如果是其余整数表示只能领取该数量
data.results.use_limit | 0 | Number | 使用限制 默认是0 表示不受限 如果是其余整数表示只能使用该数量
data.results.can_give_friend | true | - | 是否可以转增 默认True
data.results.generate_type | 1 | Number | 券码生成类型  1系统生成  2外部导入
data.results.generate_file | - | Object | 外部导入券码文件url
data.results.cash_amount | 10 | Number | 代金券：减免金额
data.results.cash_condition | 100 | Number | 代金券、折扣券、包邮券：起用金额
data.results.discount | 0 | Number | 折扣券：折扣率（八折取值0.8）
data.results.icon | aa/bb/cc.jpg | String | 卡券图标
data.results.store_codes | store_01, store_02 | String | 适用门店code列表
data.results.cost_center | NO12312513 | String | 成本中心编号
data.results.cost_type | 1 | Number | 成本费用类型  1固定金额  2百分比
data.results.cost_value | 2 | Number | 成本费用(>=0) cost_type=2时，如百分之八十,传80
data.results.extra_info | - | Object | 额外信息
data.results.extra_info.bg_color | #1111111 | String | 卡券背景色
data.results.extra_info.jump_now_path | /page/card/ | String | 立即使用跳转链接
data.results.extra_info.custom_menu_name | 卡券 | String | 底部自定义菜单名称
data.results.extra_info.menu_jump_path | /page/custom/ | String | 底部自定义菜单跳转路径
data.results.create_time | 2021-08-18 16:25:56 | Number | 创建时间
data.results.update_time | 2021-08-19 14:09:20 | Number | 更新时间
data.results.generate_info | - | Object | 已生成的卡券信息
data.results.generate_info.generated | 400000 | Number | 已经生成的数量
data.results.generate_info.un_generate | 0 | Number | 还没有生成的数量
data.results.generate_info.total | 400000 | Number | 总量
data.results.receive_info | - | Object | 领券的卡券信息
data.results.receive_info.received | 8 | Number | 已经领取的卡券数量
## /卡券/创建卡券
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/card/<crm_id>/create

#### 请求方式
> POST

#### Content-Type
> json

#### 请求Body参数
```javascript
{
	"card_type": 1,
	"title": "满100减10",
	"subtitle": "618满100减10",
	"source": 2,
	"scene": "web",
	"notice": "适用说明",
	"rule": "使用须知",
	"date_type": 1,
	"begin_time": 1655481600,
	"end_time": 1655740799,
	"start_day_count": null,
	"expire_day_count": null,
	"weekdays": "0,1,6",
	"monthdays": "1,11,18,28",
	"day_begin_time": 0,
	"day_end_time": 86399,
	"total_quantity": 10000,
	"get_limit": 0,
	"use_limit": 0,
	"can_give_friend": true,
	"generate_type": 1,
	"generate_file": null,
	"cash_amount": 10,
	"cash_condition": 100,
	"discount": 0,
	"icon": "aa/bb/cc.jpg",
	"store_codes": "store_01, store_02",
	"cost_center": "NO12312513",
	"cost_type": 1,
	"cost_value": 2,
	"extra_info": {
		"bg_color": "#1111111",
		"jump_now_path": "/page/card/",
		"custom_menu_name": "卡券",
		"menu_jump_path": "/page/custom/"
	}
}
```
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
card_type | 1 | Number | 是 | 卡券类型 0:代金券；1:折扣券；2:兑换券；3:包邮券；4:赠品券
title | 满100减10 | String | 是 | 卡券标题
subtitle | 618满100减10 | Number | 是 | 卡券副标题
source | 2 | Number | 是 | 类型  1微信商家券  2自制券
scene | web | String | 否 | 适用场景说明
notice | 适用说明 | String | 是 | 使用须知
rule | 使用须知 | String | 是 | 使用说明
date_type | 1 | String | 是 | 时间类型：1:固定时间范围；2:动态时间；3:永久有效
begin_time | 1655481600 | Number | 是 | 有效期开始时间
end_time | 1655740799 | Number | 是 | 有效期结束时间
start_day_count | - | Number | 否 | 领取后几天生效(date_type=2时有值)
expire_day_count | - | Number | 否 | 领取后几天有效(date_type=2时有值)
weekdays | 0,1,6 | String | 否 | 一周内可以使用的天数
monthdays | 1,11,18,28 | String | 否 | 一月内可以使用的天数
day_begin_time | 0 | Number | 否 | 当天可用开始时间，单位：秒，1代表当天0点0分1秒。示例值：3600
day_end_time | 86399 | Number | 否 | 当天可用结束时间，单位：秒，86399代表当天23点59分59秒。示例值：86399
total_quantity | 10000 | Number | 是 | 发行量
get_limit | 0 | Number | 否 | 领取限制 默认是0 表示不受限 如果是其余整数表示只能领取该数量
use_limit | 0 | Number | 否 | 使用限制 默认是0 表示不受限 如果是其余整数表示只能使用该数量
can_give_friend | true | Boolean | 否 | 是否可以转增 默认True
generate_type | 1 | Number | 是 | 券码生成类型  1系统生成  2外部导入
generate_file | - | Object | 是 | 外部导入券码文件url
cash_amount | 10 | Number | 否 | 代金券：减免金额
cash_condition | 100 | Number | 否 | 代金券、折扣券、包邮券：起用金额
discount | 0 | Number | 否 | 折扣券：折扣率（八折取值0.8）
icon | aa/bb/cc.jpg | String | 是 | 卡券图标
store_codes | store_01, store_02 | String | 否 | 适用门店
cost_center | NO12312513 | String | 否 | 成本中心编码
cost_type | 1 | Number | 否 | 成本费用类型  1固定金额  2百分比
cost_value | 2 | Number | 否 | 成本费用(>=0) cost_type=2时，如百分之八十,传80
extra_info | - | Object | 是 | 额外信息
extra_info.bg_color | #1111111 | String | 是 | 背景色
extra_info.jump_now_path | /page/card/ | String | 是 | 立即使用跳转链接
extra_info.custom_menu_name | 卡券 | String | 是 | 底部自定义菜单名称
extra_info.menu_jump_path | /page/custom/ | String | 是 | 底部自定义菜单跳转路径
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
	"msg": "创建卡券成功",
	"data": {
		"coupon_id": 1,
		"crm_id": "instance_id22222222",
		"card_id": "21008fdbabd30c04548a56be6eed016c",
		"card_type": 1,
		"title": "满100减10",
		"subtitle": "618满100减10",
		"source": 1,
		"scene": "web",
		"notice": "适用说明",
		"rule": "使用须知",
		"date_type": 1,
		"begin_time": 1655481600,
		"end_time": 1655740799,
		"start_day_count": null,
		"expire_day_count": null,
		"weekdays": "0,1,6",
		"monthdays": "1,11,18,28",
		"day_begin_time": 0,
		"day_end_time": 86399,
		"total_quantity": 10000,
		"get_limit": 0,
		"use_limit": 0,
		"can_give_friend": true,
		"generate_type": 1,
		"generate_file": null,
		"cash_amount": 10,
		"cash_condition": 100,
		"discount": 0,
		"icon": "aa/bb/cc.jpg",
		"store_codes": "store_01, store_02",
		"cost_center": "NO12312513",
		"cost_type": 1,
		"cost_value": 2,
		"extra_info": {
			"bg_color": "#1111111",
			"jump_now_path": "/page/card/",
			"custom_menu_name": "卡券",
			"menu_jump_path": "/page/custom/"
		},
		"create_time": "2021-08-18 16:25:56",
		"update_time": "2021-08-19 14:09:20",
		"generate_info": {
			"generated": 400000,
			"un_generate": 0,
			"total": 400000
		},
		"receive_info": {
			"received": 8
		}
	}
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | 0 | Number | 
msg | 创建卡券成功 | String | 返回文字描述
data | - | Object | 返回数据
data.coupon_id | 1 | Number | 卡券id
data.crm_id | instance_id22222222 | String | crm_id
data.card_id | 21008fdbabd30c04548a56be6eed016c | String | 卡券id
data.card_type | 1 | Number | 卡券类型 0:代金券；1:折扣券；2:兑换券；3:包邮券；4:赠品券
data.title | 满100减10 | String | 卡券标题
data.subtitle | 618满100减10 | Number | 卡券副标题
data.source | 1 | Number | 卡券类型  1微信商家券   2自制券
data.scene | web | Object | 适用场景说明
data.notice | 适用说明 | String | 使用说明：字数上限为15个
data.rule | 使用须知 | String | 使用须知：64K
data.date_type | 1 | String | 时间类型：1:固定时间范围；2:动态时间；3:永久有效
data.begin_time | 1655481600 | Number | 开始时间
data.end_time | 1655740799 | String | 结束时间
data.start_day_count | - | Object | 领取后几天生效(date_type=2时有值)
data.expire_day_count | - | Object | 领取后几天有效(date_type=2时有值)
data.weekdays | 0,1,6 | Object | 一周内可以使用的天数
data.monthdays | 1,11,18,28 | Number | 一月内可以使用的天数
data.day_begin_time | 0 | Number | 当天可用开始时间，单位：秒，1代表当天0点0分1秒。示例值：3600
data.day_end_time | 86399 | Number | 当天可用结束时间，单位：秒，86399代表当天23点59分59秒。示例值：86399
data.total_quantity | 10000 | Number | 发券量
data.get_limit | 0 | Number | 领取限制 默认是0 表示不受限 如果是其余整数表示只能领取该数量
data.use_limit | 0 | Number | 使用限制 默认是0 表示不受限 如果是其余整数表示只能使用该数量
data.can_give_friend | true | - | 是否可以转增 默认True
data.generate_type | 1 | Number | 券码生成类型  1系统生成  2外部导入
data.generate_file | - | Object | 外部导入券码文件url
data.cash_amount | 10 | Number | 代金券：减免金额
data.cash_condition | 100 | Number | 代金券、折扣券、包邮券：起用金额
data.discount | 0 | Number | 折扣券：折扣率（八折取值0.8）
data.icon | aa/bb/cc.jpg | String | 卡券图标
data.store_codes | store_01, store_02 | String | 适用门店code列表
data.cost_center | NO12312513 | String | 成本中心编号
data.cost_type | 1 | Number | 成本费用类型  1固定金额  2百分比
data.cost_value | 2 | Number | 成本费用(>=0) cost_type=2时，如百分之八十,传80
data.extra_info | - | Object | 额外信息
data.extra_info.bg_color | #1111111 | String | 卡券背景色
data.extra_info.jump_now_path | /page/card/ | String | 立即使用跳转链接
data.extra_info.custom_menu_name | 卡券 | String | 底部自定义菜单名称
data.extra_info.menu_jump_path | /page/custom/ | String | 底部自定义菜单跳转路径
data.create_time | 2021-08-18 16:25:56 | DateTime | 添加时间
data.update_time | 2021-08-19 14:09:20 | DateTime | 更新时间
data.generate_info | - | Object | 已生成的卡券信息
data.generate_info.generated | 400000 | Number | 已经生成的数量
data.generate_info.un_generate | 0 | Number | 还没有生成的数量
data.generate_info.total | 400000 | Number | 总量
data.receive_info | - | Object | 领券的卡券信息
data.receive_info.received | 8 | Number | 已经领取的卡券数量
## /卡券/卡券新增库存
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/card/<crm_id>/add/stock

#### 请求方式
> POST

#### Content-Type
> json

#### 请求Body参数
```javascript
{
        "card_id": "afagwui78hoiwf",
        "quantity": 8888,
        "generate_id": "orfhnsiwqfiwjoifw"
}
```
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
card_id | afagwui78hoiwf | String | 是 | 卡券id
quantity | 8888 | Number | 是 | 卡券数量
generate_id | orfhnsiwqfiwjoifw | String | 否 | 生成序列号， 用来防止重复生成
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
	"msg": "生成卡券任务创建成功,请等待卡券创建完成",
	"data": {
		"auto_id": 10,
		"crm_id": "instance_id22222222",
		"card_id": "21008fdbabd30c04548a56be6eed016c",
		"quantity": 2000,
		"generate_id": "generate_id_9",
		"is_generated": false,
		"create_time": null,
		"update_time": null
	}
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | 0 | Number | 
msg | 生成卡券任务创建成功,请等待卡券创建完成 | String | 返回文字描述
data | - | Object | 返回数据
data.auto_id | 10 | Number | 自增id
data.crm_id | instance_id22222222 | String | crm_id
data.card_id | 21008fdbabd30c04548a56be6eed016c | String | 卡券id
data.quantity | 2000 | Number | 卡券数量
data.generate_id | generate_id_9 | String | 生成序列号， 用来防止重复生成
data.is_generated | false | Boolean | 是否已经生成
data.create_time | - | String | 创建时间
data.update_time | - | String | 更新时间
## /卡券/删除卡券
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/card/<instance_id>/remove

#### 请求方式
> POST

#### Content-Type
> json

#### 请求Body参数
```javascript
{
    "card_id": "afof2f23rl"
}
```
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
card_id | afof2f23rl | String | 是 | 卡券id
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
	"msg": "删除卡券成功"
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | - | Number | 
msg | 删除卡券成功 | String | 返回文字描述
## /卡券/卡券领取
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/card/<crm_id>/member/receive

#### 请求方式
> POST

#### Content-Type
> json

#### 请求Body参数
```javascript
{
    "received_id": "received_id11111111",
    "member_no": "32880aa593b144508484cb8bb8261041",
    "out_str": "sim_data",
    "card_info": {
        "21008fdbabd30c04548a56be6eed016c_17b585dee1_2459274dad6dba47": 2,
        "21008fdbabd30c04548a56be6eed016c_17b5d049bd_3f96e2459650e415": 2,
        "21008fdbabd30c04548a56be6eed016c_17b5d05ccf_f29319499d606073": 2
    }
}
```
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
received_id | received_id11111111 | String | 是 | 领取id 防止重复领取
member_no | 32880aa593b144508484cb8bb8261041 | String | 是 | 会员号
out_str | sim_data | String | 是 | 来源
card_info | - | Object | 是 | 要领取的卡券信息  要领取的卡券信息 key是card_id, value是要领取的数量
card_info.21008fdbabd30c04548a56be6eed016c_17b585dee1_2459274dad6dba47 | 2 | Number | 是 | -
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
	"msg": "领券成功"
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | - | Number | 
msg | 领券成功 | String | 返回文字描述
## /卡券/卡券领取详情
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/card/<crm_id>/member/receive_detail?received_id=23r24tg13ed1d

#### 请求方式
> GET

#### Content-Type
> none

#### 请求Query参数
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
received_id | 23r24tg13ed1d | String | 是 | -
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
	"msg": "获取卡券领取详情成功",
	"data": [
		{
			"card_code": {
				"auto_id": 300032,
				"crm_id": "instance_id22222222",
				"card_code": "1428236189155983361",
				"card_id": "21008fdbabd30_2459274dad6dba47",
				"member_no": "32880aa593b144508484cb8bb8261041",
				"card_code_status": 1,
				"card_code_preuse_status": 1,
				"create_time": "2021-08-19 14:03:42",
				"update_time": "2021-08-19 15:27:17"
			},
			"card_info": {
				"auto_id": 9,
				"instance_id": "instance_id22222222",
				"received_id": "received_id11111",
				"card_id": "21008fdbabd30c04548a56be6eed016c",
				"member_no": "32880aa593b144508484cb8bb8261041",
				"card_code": "1428236189155983361",
				"start_time": "2021-08-18 00:00:00",
				"end_time": "2099-01-01 00:00:00",
				"out_str": "sim_data",
				"code_status": 1,
				"received_time": "2021-08-19 15:11:31",
				"redeem_time": null,
				"present_time": null,
				"expired_time": "2099-01-01 00:00:00",
				"obsoleted_time": "2021-08-19 15:27:17",
				"create_time": "2021-08-19 15:11:31",
				"update_time": "2021-08-19 15:27:17"
			}
		}
	]
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | 0 | Number | 
msg | 获取卡券领取详情成功 | String | 返回文字描述
data | - | Object | 返回数据
data.card_code | - | Object | 卡券code信息
data.card_code.auto_id | 300032 | Number | 自增id
data.card_code.crm_id | instance_id22222222 | String | crm_id
data.card_code.card_code | 1428236189155983361 | String | 卡券code
data.card_code.card_id | 21008fdbabd30_2459274dad6dba47 | String | 卡券id
data.card_code.member_no | 32880aa593b144508484cb8bb8261041 | String | 会员号
data.card_code.card_code_status | 1 | Number | 卡券是否被领取 0表示没有被领取 1 表示被领取了
data.card_code.card_code_preuse_status | 1 | Number | 卡券是否放在redis中 0 表示否 1表示是 一般来说， 因为领券都是从redis中拿，所以这个值必定是1
data.card_code.create_time | 2021-08-19 14:03:42 | String | 创建时间
data.card_code.update_time | 2021-08-19 15:27:17 | String | 更新时间
data.card_info | - | Object | 卡券领取信息
data.card_info.auto_id | 9 | Number | 自增id
data.card_info.instance_id | instance_id22222222 | String | 实例id
data.card_info.received_id | received_id11111 | String | 领取id 防止重复领取
data.card_info.card_id | 21008fdbabd30c04548a56be6eed016c | String | 卡券id
data.card_info.member_no | 32880aa593b144508484cb8bb8261041 | String | 会员号
data.card_info.card_code | 1428236189155983361 | String | 卡券code
data.card_info.start_time | 2021-08-18 00:00:00 | String | 卡券生效时间
data.card_info.end_time | 2099-01-01 00:00:00 | String | 卡券过期时间
data.card_info.out_str | sim_data | String | 领取渠道
data.card_info.code_status | 1 | Number | 卡券状态，1 可用，2 转赠中，3已核销，4 已过期，5 作废
data.card_info.received_time | 2021-08-19 15:11:31 | String | 卡券领取时间
data.card_info.redeem_time | - | String | 核销时间
data.card_info.present_time | - | String | 转赠时间
data.card_info.expired_time | 2099-01-01 00:00:00 | String | 过期时间
data.card_info.obsoleted_time | 2021-08-19 15:27:17 | String | 作废时间
data.card_info.create_time | 2021-08-19 15:11:31 | String | 创建时间
data.card_info.update_time | 2021-08-19 15:27:17 | String | 更新时间
## /卡券/卡券领取冲正
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/card/<crm_id>/member/receive_reverse

#### 请求方式
> POST

#### Content-Type
> json

#### 请求Body参数
```javascript
{
  "received_id": "2trf23fd2qtf"
}
```
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
received_id | 2trf23fd2qtf | String | 是 | 领取id
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
	"msg": "冲正成功"
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | - | Number | 
msg | 冲正成功 | String | 返回文字描述
## /卡券/卡券转增
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/card/<crm_id>/member/present

#### 请求方式
> POST

#### Content-Type
> json

#### 请求Body参数
```javascript
{
  "member_no": "2trf23fd2qtf",
  "card_id": "23fw3rf2wrf2q3rf",
  "card_code": "23rfi23r0921jf239rf23rf920rjf32",
  "presant_extra": "分享好券"
}
```
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
member_no | 2trf23fd2qtf | String | 是 | 会员号
card_id | 23fw3rf2wrf2q3rf | String | 是 | 卡券id
card_code | 23rfi23r0921jf239rf23rf920rjf32 | String | 是 | 卡券信息
presant_extra | 分享好券 | String | 是 | 赠送信息
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
	"msg": "转增成功"
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | - | Number | 
msg | 转增成功 | String | 返回文字描述
## /卡券/卡券转增领取
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/card/<crm_id>/member/present_receive

#### 请求方式
> POST

#### Content-Type
> json

#### 请求Body参数
```javascript
{
  "member_no": "23rf24tf23", 
  "present_id": "2f2rf13f1"
}
```
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
member_no | 23rf24tf23 | String | 是 | 会员号
present_id | 2f2rf13f1 | String | 是 | 转增id
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
	"msg": "领取成功"
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | - | Number | 
msg | 领取成功 | String | 返回文字描述
## /卡券/用户卡券列表
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/card/<crm_id>/member/card_list?member_no=agfwefafew&code_status=1&page_id=1&page_size=20

#### 请求方式
> GET

#### Content-Type
> json

#### 请求Query参数
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
member_no | agfwefafew | String | 是 | 会员id
code_status | 1 | String | 是 | 卡券状态
page_id | 1 | String | 是 | 分页页码
page_size | 20 | String | 是 | 分页大小
#### 请求Body参数
```javascript

```
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
	"msg": "获取用户卡券列表成功",
	"data": {
		"total": 18,
		"result": [
			{
				"auto_id": 32,
				"crm_id": "instance_id22222222",
				"received_id": "received_id11111111",
				"card_id": "210017b5d05ccf_f29319499d606073",
				"member_no": "32880aa593b144508484cb8bb8261041",
				"card_code": "1428237280476135432",
				"start_time": "2021-08-20 15:42:20",
				"end_time": "2021-08-27 15:42:20",
				"out_str": "sim_data",
				"code_status": 1,
				"received_time": "2021-08-19 15:42:19",
				"redeem_time": null,
				"present_time": null,
				"expired_time": "2021-08-27 15:42:20",
				"obsoleted_time": null,
				"create_time": "2021-08-19 15:42:19",
				"update_time": "2021-08-19 15:42:19"
			}
		]
	}
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | 0 | Number | 
msg | 获取用户卡券列表成功 | String | 返回文字描述
data | - | Object | 返回数据
data.result | - | Object | 
data.result.auto_id | 32 | Number | 
data.result.crm_id | instance_id22222222 | String | crm_id
data.result.received_id | received_id11111111 | String | 领券id
data.result.card_id | 210017b5d05ccf_f29319499d606073 | Number | card_id
data.result.member_no | 32880aa593b144508484cb8bb8261041 | Number | 会员id
data.result.card_code | 1428237280476135432 | Number | card_code
data.result.start_time | 2021-08-20 15:42:20 | Number | 有效期开始时间
data.result.end_time | 2021-08-27 15:42:20 | Number | 有效期结束时间
data.result.out_str | sim_data | String | 来源信息
data.result.code_status | 1 | Number | 卡券状态，1 可用，2 转赠中，3已核销，4 已过期，5 作废
data.result.received_time | 2021-08-19 15:42:19 | Number | 领取时间
data.result.redeem_time | - | Object | 核销时间
data.result.present_time | - | Object | 转赠时间
data.result.expired_time | 2021-08-27 15:42:20 | Number | 过期时间
data.result.obsoleted_time | - | Object | 作废时间
data.result.create_time | 2021-08-19 15:42:19 | Number | 添加时间
data.result.update_time | 2021-08-19 15:42:19 | Number | 更新时间
## /卡券/用户转增记录列表
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/card/<crm_id>/member/present_list

#### 请求方式
> GET

#### Content-Type
> json

#### 请求Query参数
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
page_id | 1 | String | 否 | 页码 默认是1|
page_size | 20 | String | 否 | 每页数据量 默认是20
member_no | 2r4f35tg1df2gf2 | String | 否 | 会员号
received | 0 | String | 否 | 是否已领取 0 表示没有 1表示已领取
#### 请求Body参数
```javascript

```
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
	"msg": "获取用户转增记录成功",
	"data": {
	    "total": 3,
		"data": [
			{
				"auto_id": 1,
				"instance_id": "instance_id22222222",
				"from_member_no": "32880aa593b144508484cb8bb8261041",
				"to_member_no": null,
				"card_id": "21008fdbabe1_2459274dad6dba47",
				"card_code": "1428236189390864394",
				"present_id": "2d5e31832df143f4b01516b835ed6763",
				"present_extra": "好券分享",
				"present_time": "2021-08-19 15:43:11",
				"received_time": null,
				"go_back_time": null,
				"create_time": "2021-08-19 15:43:12",
				"update_time": "2021-08-19 15:43:11"
			}
		]
		
	}
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | 0 | Number | 
msg | 获取用户转增记录成功 | String | 返回文字描述
data | - | Object | 返回数据
data.total | 3 | Number | 总量
data.data | - | Object | 返回数据
data.data.auto_id | 1 | Number | 自增id
data.data.instance_id | instance_id22222222 | String | 实例id
data.data.from_member_no | 32880aa593b144508484cb8bb8261041 | String | 转增者id
data.data.to_member_no | - | Object | 领取者id
data.data.card_id | 21008fdbabe1_2459274dad6dba47 | String | 卡券id
data.data.card_code | 1428236189390864394 | String | 卡券信息
data.data.present_id | 2d5e31832df143f4b01516b835ed6763 | String | 转增id
data.data.present_extra | 好券分享 | String | 赠送备注
data.data.present_time | 2021-08-19 15:43:11 | String | 转赠时间
data.data.received_time | - | String | 卡券领取时间
data.data.go_back_time | - | String | 回滚时间
data.data.create_time | 2021-08-19 15:43:12 | String | 创建时间
data.data.update_time | 2021-08-19 15:43:11 | String | 更新时间
## /卡券/用户转增记录详情
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/card/<crm_id>/member/present_detail?present_id=2rf212r5y2f

#### 请求方式
> GET

#### Content-Type
> json

#### 请求Query参数
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
present_id | 2rf212r5y2f | String | 是 | 转增id
#### 请求Body参数
```javascript

```
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
	"msg": "获取用户转增记录成功",
	"data": {
		"auto_id": 1,
		"instance_id": "instance_id22222222",
		"from_member_no": "32880aa593b144508484cb8bb8261041",
		"to_member_no": "93b144508484cb8bb82",
		"card_id": "21008fdbabd30c04548a56be6eed016c_17b585dee1_2459274dad6dba47",
		"card_code": "1428236189390864394",
		"present_id": "2d5e31832df143f4b01516b835ed6763",
		"present_extra": "好券分享",
		"present_time": "2021-08-19 15:43:11",
		"received_time": null,
		"go_back_time": null,
		"create_time": "2021-08-19 15:43:12",
		"update_time": "2021-08-19 15:43:11"
	}
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | 0 | Number | 
msg | 获取用户转增记录成功 | String | 返回文字描述
data | - | Object | 返回数据
data.auto_id | 1 | Number | 自增id
data.instance_id | instance_id22222222 | String | 实例id
data.from_member_no | 32880aa593b144508484cb8bb8261041 | Number | 转增者id
data.to_member_no | - | Object | 领取者id
data.card_id | 21008fdbabd30c04548a56be6eed016c_17b585dee1_2459274dad6dba47 | String | 卡券id
data.card_code | 1428236189390864394 | Object | 卡券code信息
data.present_id | 2d5e31832df143f4b01516b835ed6763 | Number | 转赠id
data.present_extra | 好久一个字 | String | 赠送备注
data.present_time | 2021-08-19 15:43:11 | Number | 转赠时间
data.received_time | - | Object | 领取时间
data.go_back_time | - | Object | 回滚时间
data.create_time | 2021-08-19 15:43:12 | String | 创建时间
data.update_time | 2021-08-19 15:43:11 | String | 更新时间
## /卡券/用户卡券详情
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/card/<crm_id>/member/card_detail

#### 请求方式
> GET

#### Content-Type
> json

#### 请求Query参数
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
member_no | 2rf2tf2f3rdwgf | String | 是 | 会员号
card_id | 34tg3t12rf2r | String | 是 | 卡券id
card_code | 4tg2erd2g3re | String | 是 | 卡券code
received_id | wrfr2t2fwqr1 | String | 是 | 领取id
#### 请求Body参数
```javascript

```
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
	"msg": "获取卡券详情成功",
	"data": {
		"auto_id": 35,
		"crm_id": "instance_id22222222",
		"received_id": "received_id23",
		"card_id": "21008fdbabd30c04548a56be6eed016c_17b5d049bd_3f96e2459650e415",
		"member_no": "32880aa593b144508484cb8bb8261041",
		"card_code": "1428237007485665289",
		"start_time": "2021-08-08 00:00:00",
		"end_time": "2021-09-10 23:59:59",
		"out_str": "sim_data",
		"code_status": 1,
		"received_time": "2021-08-20 12:25:25",
		"redeem_time": null,
		"present_time": null,
		"expired_time": "2021-09-10 23:59:59",
		"obsoleted_time": null,
		"create_time": "2021-08-20 12:25:25",
		"update_time": "2021-08-20 12:25:25"
	}
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | 0 | Number | 
msg | 获取卡券详情成功 | String | 返回文字描述
data | - | Object | 返回数据
data.auto_id | 35 | Number | 自增id
data.crm_id | instance_id22222222 | String | crm_id
data.received_id | received_id23 | String | 领取id
data.card_id | 21008fdbabd30c04548a56be6eed016c_17b5d049bd_3f96e2459650e415 | String | 卡券id
data.member_no | 32880aa593b144508484cb8bb8261041 | String | 会员号
data.card_code | 1428237007485665289 | String | 卡券code
data.start_time | 2021-08-08 00:00:00 | String | 卡券生效时间
data.end_time | 2021-09-10 23:59:59 | String | 卡券过期时间
data.out_str | sim_data | String | 领取渠道
data.code_status | 1 | Number | 卡券状态，1 可用，2 转赠中，3已核销，4 已过期，5 作废
data.received_time | 2021-08-20 12:25:25 | String | 卡券领取时间
data.redeem_time | - | String | 核销时间
data.present_time | - | String | 转赠时间
data.expired_time | 2021-09-10 23:59:59 | String | 过期时间
data.obsoleted_time | - | String | 作废时间
data.create_time | 2021-08-20 12:25:25 | String | 创建时间
data.update_time | 2021-08-20 12:25:25 | String | 更新时间
## /卡券/用户卡券核销
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/card/<crm_id>/member/redeem

#### 请求方式
> POST

#### Content-Type
> json

#### 请求Body参数
```javascript
{
        "member_no": "af2rf24",
        "card_id": "2f2rf2f",
        "card_code": "2tfg1fd2f3",
        "redeem_channel": "rfr21rf1",
        "redeem_id": "213rf2",
        "redeem_extra": "已核销"
}
```
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
member_no | af2rf24 | String | 是 | 会员号
card_id | 2f2rf2f | String | 是 | 卡券id
card_code | 2tfg1fd2f3 | String | 是 | 卡券信息
redeem_channel | rfr21rf1 | String | 是 | 核销渠道
redeem_id | 213rf2 | String | 是 | 核销id
redeem_extra | 已核销 | String | 是 | 核销备注
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
	"msg": "核销成功"
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | - | Number | 
msg | 核销成功 | String | 返回文字描述
## /卡券/用户核销冲正
```text
暂无描述
```
#### 接口状态
> 开发中

#### 接口URL
> /api/crm/card/<crm_id>/member/redeem_reverse

#### 请求方式
> POST

#### Content-Type
> json

#### 请求Body参数
```javascript
{
  "redeem_id": "2f2r3fgr"
}
```
参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述
--- | --- | --- | --- | ---
redeem_id | 2f2r3fgr | String | 是 | 核销id
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
	"msg": "冲正成功"
}
```
参数名 | 示例值 | 参数类型 | 参数描述
--- | --- | --- | ---
code | - | Number | 
msg | 核销成功 | String | 返回文字描述



# 数据结构设计
1. 卡券信息表  t_card_info

| 字段 | 类型 | 长度 |  注释 |
| -------- | -------- | -------- |------------|
|coupon_id	|int	|   |	自增编号|
|crm_id	|	varchar	|32		|crm_id|
|card_id	|	varchar |	32	|	卡券ID|
|source	|	int	|  |1		来源  1微信商家 2自制券|
|title	|	varchar	| 64		|卡券标题 |
|subtitle	|	varchar	| 128	|	卡券副标题 |
| scene	| varchar	 | 64	|	适用场景说明|
| card_type	|	smallint	| |	优惠券类型(0:代金券；1:折扣券；2:兑换券；3:包邮券；4:赠品券)
| use_with_other_offer	|	bool|   |			是否可与其它促销同时使用|
| use_with_other_coupon	 |	bool	|	   |	true：可与其他卡券同时使用|
| can_give_friend		| bool	|  |		是否可转赠朋友|
|notice	 |	varchar | 	32	|	使用说明：字数上限为15个|
|rule	 |	text |  |			使用须知：64K |
| date_type	 |	smallint	|   |		时间类型：1:固定时间范围；2:动态时间；3:永久有效|
| begin_time	|	int	 | |		生效时间 |
| end_time	|	int	| |		过期时间|
| start_day_count |		int	|  |		领取后几天生效(date_type=2时有值) |
| expire_day_count	|	int |  |			领取后几天有效(date_type=2时有值) |
|weekdays	|	varchar | 	64	|	一周内可以使用的天数1, 3, 5, 7 |
| monthdays	|	varchar	 | 128| 		一月内可以使用的天数1, 3, 5, 31|
|day_begin_time|		int|  		|当天可用开始时间，单位：秒，1代表当天0点0分1秒。示例值：3600|
|day_end_time|		int|  		|当天可用结束时间，单位：秒，86399代表当天23点59分59秒。示例值：86399|
|cash_amount	|	float | 	|		代金券：减免金额|
|cash_condition	|	float |		 |	代金券、折扣券、包邮券：起用金额
qty_condition	|	smallint	| |		启用件数：购满M件
discount	|	float	| |		折扣券：折扣率（八折取值0.8）
total_quantity	|	int	|		  | 发券量
generate_type	|	int	|		  | 券码生成方式  1系统生成  2外部导入
generate_file	|	varchar	|	128	  | 外部导入文件路径
get_limit		| smallint	|		|每人限领数量，0不限
use_limit	 |	smallint	|  |		每人限用数量，0不限
generate_type	 |	smallint	|  |		卡券生成方式1 系统生成 2外部生成
generate_file	|	varchar	| 128	|	外部生成的文件链接
icon	|	varchar	| 128	|	缩略图
extra_info	|	text	|  |		附加信息: bg_color ：背景颜色；jump_now_path ：立即使用跳转链接；custom_menu_name ：底部自定义菜单名称；menu_jump_path ：底部自定义菜单跳转路径
store_codes	|	text |  |			适用门店code列表
cost_center	 |	varchar|	64	|	成本中心code
cost_type	 |	smallint	|		|成本费用类型  1固定金额  2百分比
cost_value	|	float |   |			成本费用(>=0) cost_type=2时，如百分之八十,传80
removed		|bool |		|	是否删除
create_time		|datetime|   |			添加时间
update_time	 |	datetime |   |			更新时间

2. 用户卡券限制表  t_member_card_record

| 字段 | 类型 | 长度 |  注释 |
| -------- | -------- | -------- |------------|
auto_id	| int | | |			
crm_id	|	varchar	|32	|	实例ID
card_id	|	varchar|	32	|	卡券ID
member_no	|	varchar |	64	|	卡券全称
received_sum	|	int	|	|	领取条数，转赠不减次数
create_time	|	datetime	|	|	添加时间
update_time	|	datetime	|	|	更新时间


3. 用户领券记录表   t_member_card_code

| 字段 | 类型 | 长度 |  注释 |
| -------- | -------- | -------- |------------|
auto_id	|  | | |	
crm_id	|	varchar	|32	|	实例ID
received_id	|	varchar|	64|		领取ID
card_id	|	varchar	|32	|	卡券ID
member_no	|	varchar|	64	|	会员号
card_code	|	varchar	|64	|	券码
begin_time	|	datetime| |			起始时间
end_time	|	time	|	|	截止时间
discount	|	float	|		|折扣券：折扣率（八折取值0.8）
out_str		|varchar	|	32 |	out_str领取渠道
code_status	|	int	|		|卡券状态，1 可用，2 转赠中，3已核销，4 已过期，5 作废
received_time	|	datetime	|		|领取时间
redeem_time	|	datetime	|		| 核销时间
present_time	|	datetime	|		|转赠时间
expired_time	|	datetime	|		| 过期时间
receive_type	|	smallint	|	|	领取类型： 0直接领取 1转增领取
is_reversed	|	smallint |		|	是否冲正 0未冲正 1已冲正
create_time	|	datetime	|		|添加时间
update_time	|	datetime	|	|	更新时间

4. 用户卡券过期记录表   t_member_card_expired

| 字段 | 类型 | 长度 |  注释 |
| -------- | -------- | -------- |------------|
auto_id	 |int | |
crm_id	|	varchar	|32	|	实例ID
received_id	|	varchar	|64	|	领取ID
member_no	|	varchar|	64	|	会员号
card_code	|	varchar	|64	|	券码
expired_time	|	datetime|		|	过期时间
create_time	|	datetime	|		|添加时间


5. 用户卡券作废记录表   t_member_card_obsoleted

| 字段 | 类型 | 长度 |  注释 |
| -------- | -------- | -------- |------------|
auto_id	 |  int| |				
crm_id	|	varchar|	32	|	实例ID
received_id	|	varchar	|64|		领取ID
member_no	|	varchar |	64	|	会员号
card_code	|	varchar|	64|		券码
obsoleted_time	|	datetime	|	|	作废时间
operator	|	varchar	|32	|	操纵人
create_time	|	datetime	|	|	添加时间

6. 用户卡券核销表 t_member_redeem_card_code

| 字段 | 类型 | 长度 |  注释 |
| -------- | -------- | -------- |------------|
auto_id	| int| | 	
crm_id	|	varchar	|32	|	产品实例id
card_id	|	varchar	| 32	|	卡券ID
member_no	|	varchar	|64	|	会员号
card_code	|	varchar|	64	|	券码
redeem_channel	|	varchar	|64	|	核销渠道
redeem_id	|	varchar|	64	|	核销Id，第三方核销ID，用与幂等性控
redeem_extra	|	text|  |			核销参数
redeem_time	|	datetime	|	|	核销时间
rollback_status	|	int	|		|会滚状态0 未回滚，1 已回滚
rollback_time	|	datetime	|		|回滚时间
create_time	|	datetime	|		|添加时间
update_time	|	datetime	|		|更新时间


7. 用户赠券信息表  t_member_present_record

| 字段 | 类型 | 长度 |  注释 |
| -------- | -------- | -------- |------------|
auto_id	|int | |				
crm_id	|	varchar	|32	|	产品实例id
card_id	|	varchar	| 32	|	卡券ID
from_member_no	|	varchar	|64|		赠券用户ID
to_member_no	|	varchar|	64	|	领券用户ID
card_code	|	varchar	|64	|	券码
present_id	|	varchar	|64	|	自己生成的唯一id 表示转增事件
present_extra	|	text	|	|	转增参数
present_time	|	datetime	|	|	转赠时间
received_time	|	datetime	|	|	领取时间
go_back_time	|	datetime	|		| 回滚时间
create_time	|	datetime	|	|	添加时间
update_time	|	datetime	|	|	更新时间

8. 自制卡券券码生成记录表  t_card_generate

| 字段 | 类型 | 长度 |  注释 |
| -------- | -------- | -------- |------------|
auto_id	| int| |  		
crm_id	|	varchar	|32	|	产品实例id
card_id	|	varchar	|32|		卡券ID
card_num	|	int	|	|	生成的卡券数量
generate_id		|varchar|	64|		生成卡券Id，第三方生成卡券ID，用与幂等性控制
is_generated	|	tinyint	|	|	是否已经生成完成
create_time	|	datetime|	|		添加时间
update_time	|	datetime	|	|	更新时间


