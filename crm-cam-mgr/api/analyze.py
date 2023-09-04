from sanic.response import file
from sanic import Blueprint
from sanic.log import logger

from biz.analyze import *
from common.utils.check import date_delta, start_less_end
from common.utils.template import true_template

bp = Blueprint("bp_analyze", url_prefix="/panel")


@bp.post("/<instance_id>/list")
async def panel_list(request, instance_id):
    app = request.app
    obj = request.json or {}
    from_date = obj.get('from_date')
    assert from_date, 'from_date必传'
    to_date = obj.get('to_date')
    assert to_date, 'to_date必传'
    assert date_delta(from_date, to_date) >= 6, '时间范围最小为一周'
    result = await get_panel_list(app, instance_id, from_date, to_date)
    return true_template(result)


@bp.post("/<instance_id>/detail")
async def panel_detail(request, instance_id):
    app = request.app
    obj = request.json or {}
    type = obj.get('type')
    assert type, 'type必传'
    assert type in ('cep', 'nft'), '活动非法'
    activity_id = obj.get('activity_id')
    assert activity_id, 'activity_id必传'
    from_date = obj.get('from_date')
    assert from_date, 'from_date必传'
    to_date = obj.get('to_date')
    assert to_date, 'to_date必传'
    assert start_less_end(from_date, to_date, t='date'), '开始时间应先于结束时间'
    result = await get_panel_detail(app, instance_id, activity_id, type, from_date, to_date)
    return true_template(result)


@bp.post("/<instance_id>/detail_export")
async def panel_export(request, instance_id):
    app = request.app
    obj = request.json or {}
    type = obj.get('type')
    assert type, 'type必传'
    assert type in ('cep', 'nft'), '活动非法'
    activity_id = obj.get('activity_id')
    assert activity_id, 'activity_id必传'
    from_date = obj.get('from_date')
    assert from_date, 'from_date必传'
    to_date = obj.get('to_date')
    assert to_date, 'to_date必传'
    assert start_less_end(from_date, to_date, t='date'), '开始时间应先于结束时间'
    result = await get_panel_detail(app, instance_id, activity_id, type, from_date, to_date)

    sheet_list = []
    name_one = '活动报表-汇总'
    header_one = ['活动访问', '关闭数', '领券数', '活动访客', '参与人数', '领券人数', '分享人数', '注册会员']
    base_field_one = ['expose_times', 'close_times', 'pick_num', 'expose_people', 'click_people', 'pick_people']
    need_field_one = base_field_one + ['share_gift_total', 'register_member_total']
    data_one = result.get('sum_stat_cal', {})
    data_one = [data_one[x] for x in need_field_one]
    sheet_list.append((name_one, header_one, [*(data_one,)]))
    ###
    name_two = '活动报表-趋势'
    header_two = ['日期'] + header_one
    need_field_two = ['tdate'] + base_field_one + ['share_gift_people', 'register_member_people']
    data_two = result.get('trend_stat_cal', [])
    new_data_two = []
    for x in data_two:
        temp = []
        for k in need_field_two: temp.append(x[k])
        new_data_two.append(temp)
    sheet_list.append((name_two, header_two, new_data_two))

    ###
    name_three = '活动报表-地域分布'
    tag = obj.get('tag', 'province')
    if tag == 'province':
        header_three = ['省份', '参与人数']
    else:
        header_three = ['城市', '参与人数']
    data_three = result.get('region_stat_cal', [])
    sheet_list.append((name_three, header_three, [(x['name'], x['value']) for x in data_three]))
    ###
    # name_four = '活动报表-来源分析'
    # header_four = ['场景值', '来源', '参与人数']
    # data_four = result.get('from_stat_cal', [])
    # sheet_list.append((name_four, header_four, [(x['scene'], x['name'], x['numbers']) for x in data_four]))
    ###
    file_name, file_path = gen_excel_fileinfo()
    write_to_excel(file_path, sheet_list)
    return await file(file_path, filename=file_name)


@bp.post("/<instance_id>/merge")
async def panel_merge(request, instance_id):
    app = request.app
    obj = request.json or {}
    from_date = obj.get('from_date')
    assert from_date, 'from_date必传'
    to_date = obj.get('to_date')
    assert to_date, 'to_date必传'
    assert date_delta(from_date, to_date) >= 6, '时间范围最小为一周'
    result = await get_panel_merge(app, instance_id, from_date, to_date)
    return true_template(result)


@bp.get("/<instance_id>/merge_export")
async def panel_merge_export(request, instance_id):
    app = request.app
    obj = request.args or {}
    from_date = obj.get('from_date')
    assert from_date, 'from_date必传'
    to_date = obj.get('to_date')
    assert to_date, 'to_date必传'
    assert date_delta(from_date, to_date) >= 6, '时间范围最小为一周'
    return await get_panel_merge_export(app, instance_id, from_date, to_date)


@bp.post("/<instance_id>/region_top")
async def api_region_top(request, instance_id):
    app = request.app
    obj = request.json or {}
    from_date = obj.get('from_date')
    assert from_date, 'from_date必传'
    to_date = obj.get('to_date')
    assert to_date, 'to_date必传'
    types = obj.get("types")
    assert types in (1, 2),  "传入合法的参数"
    activity_id = obj.get('activity_id')
    assert activity_id, 'activity_id必传'
    data = await handle_region_top(app, activity_id, from_date, to_date, types=int(types))
    return true_template(data=data)