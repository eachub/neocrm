#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import hashlib

import sys

sys.path.insert(0, '..')
import time
from datetime import datetime

import ujson
from mtkext.db import peewee_normalize_dict
from peewee import DoesNotExist
from sanic.log import logger
import asyncio

from common.utils.misc import init_logger

sys.path.append('..')
from common.models.helper import add_record_from_dict
from utils.spider import SpiderBase
from mtkext.clients.mall import MallClient

from common.models.ecom import GoodsInfo, SkuInfo, CategoryNode, CategoryBind


async def handle_one_item(app, client, item_dict, mall_id, version):
    """处理这条请求"""
    msg = ujson.dumps(item_dict, ensure_ascii=False)
    logger.info(f"detect-msg: {msg}")
    hashcode = hashlib.md5(msg.encode()).hexdigest()
    if app.cache.get(hashcode, delta=86400): return False, ""
    mall_id = item_dict.get("mall_id")
    ### 保存原始数据
    try:
        # 请求详情页
        goods_id = item_dict.get("goods_id")
        flag, detail = await client.goods.fetch({"goods_id": goods_id}, mall_id=mall_id)
        if flag:
            logger.info(detail)
            one = dict(detail)
            category = one.get("category") or []
            for cat in category:
                cat_id = cat.get('cat_id')
                category_obj = dict(
                    mall_id=mall_id, goods_id=goods_id, cat_id=cat_id
                )
                await add_record_from_dict(app.mgr, CategoryBind, category_obj, on_conflict=3,
                                           target_keys=['goods_id', 'cat_id'])
            cate_ids = [str(i.get('cat_id')) for i in category]
            one.update(dict(version=version, category=','.join(cate_ids)))
            await add_record_from_dict(app.mgr, GoodsInfo, one, excluded=[], on_conflict=3,
                                       target_keys=['goods_id', 'mall_id'])
            sku_list = item_dict.get("sku_list")
            for sku in sku_list:
                sku['mall_id'] = mall_id
                sku['version'] = version
                sku['goods_id'] = item_dict.get("goods_id")
                await add_record_from_dict(app.mgr, SkuInfo, sku, excluded=[], on_conflict=3,
                                       target_keys=['sku_id', 'mall_id'])
    except Exception as ex:
        logger.exception(ex)


class SyncMallGoods(SpiderBase):
    ClientClass = MallClient

    run_methods = [
        1
    ]

    def __init__(self):
        self.fn = "/tmp/.goods_spider.txt"  # eg: 20210815093010
        self.delta = 10

    async def init_client(self):
        # self.conf.INSTANCE_ID = "ALL_INSTANCE_ID"
        client = self.ClientClass(self.http, **self.conf.PARAMS_FOR_MALL_CLIENT)
        return client

    async def fetch(self, client, from_time, to_time, run_method):
        flag = await fetch_data(self, client, from_time, to_time, None)
        return flag


async def fetch_data(app, client, from_time, to_time, run_method):
    logger.info(f'running method {run_method}')
    version = datetime.now().strftime("%y%m%d%H%M%S")
    mall_id = 18000
    page_id, page_size = 1, 50
    time_end = int(time.time())
    # 获取商品类目信息
    cat_flag, cate_data = await client.system.get_category_dict(mall_id=18000)
    if cat_flag:
        for k, v in cate_data.get("categories").items():
            cate_info = v
            cate_info['mall_id'] = mall_id
            await add_record_from_dict(app.mgr, CategoryNode, cate_info, on_conflict=2)
    while True:
        param = {"page_id": page_id, "page_size": page_size,
                 "order_by": "create_time", "order_asc": 1,
                 "time_start": 60760931, "time_end": time_end}
        logger.info(f"PARAM={param}, mall_id={mall_id}")
        flag, result = await client.goods.list(param, mall_id=mall_id)
        logger.info(result)
        if flag:
            goods_list = result['goods_list']
            mall_id = result['mall_id']
            if not goods_list: break
            for item in goods_list:
                await handle_one_item(app, client, item, mall_id, version)
            page_id += 1
            await asyncio.sleep(0.3)
        else:
            logger.error(f"网络错误：{result}")
            break
    ### CLEAR UP and INIT brand_id
    await clear_up_prod_table(app.mgr, GoodsInfo, mall_id, version)
    await clear_up_prod_table(app.mgr, SkuInfo, mall_id, version)
    return True


async def clear_up_prod_table(mgr, ThatModel, mall_id, version):
    await mgr.execute(ThatModel.update({
        ThatModel.removed: 1,
    }).where(
        ThatModel.mall_id == mall_id,
        ThatModel.version.is_null() | (ThatModel.version != version),
    ))


if __name__ == '__main__':
    from argparse import ArgumentParser

    init_logger(f"logs/Goods-spider.log", level="INFO", count=30)
    parser = ArgumentParser(prog="mall_goods_Spider")
    parser.add_argument('--env', dest='env', type=str, required=True, choices=('prod', 'test', 'local'))
    parser.add_argument('--stamp', dest='stamp', type=str, required=True, help='eg.20200529112233 or 1580015800')
    cmd_args = parser.parse_args()
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(SyncMallGoods.init(loop, cmd_args))
    loop.run_until_complete(SyncMallGoods().execute(0))
    loop.close()
