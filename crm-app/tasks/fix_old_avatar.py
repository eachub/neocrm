import binascii
import os
import sys
sys.path.insert(0, "..")
import time

import aiojobs
import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from uuid import uuid4


from mtkext.proc import Processor

from common.models.base import db_eros_crm
from common.models.member import MemberInfo, WechatUserInfo, MemberFamily

logger = logging.getLogger(__name__)

CRM_URL = "http://127.0.0.1:21100/api/crm/member/10080/image_convert"


def encode_multipart_formdata_text(fields):
    """构建multipart/form-data请求包体"""
    boundary = binascii.hexlify(os.urandom(16)).decode('ascii')

    body = (
        "".join("--%s\r\n"
                "Content-Disposition: form-data; name=\"%s\"\r\n"
                "\r\n"
                "%s\r\n" % (boundary, field, value)
                for field, value in fields.items()) +
        "--%s--\r\n" % boundary
    )

    content_type = "multipart/form-data; boundary=%s" % boundary

    return body, content_type


async def update_member_avatart(app, member_no, crm_url, old_avatar):
    # member_info
    await app.mgr.execute(MemberInfo.update(avatar=crm_url).where(MemberInfo.member_no==member_no, MemberInfo.avatar==old_avatar))
    # update member_family
    await app.mgr.execute(MemberFamily.update(avatar=crm_url).where(MemberFamily.member_no==member_no,
                                                                    MemberFamily.relationship==1, MemberFamily.avatar==old_avatar))
    logger.info(f"update one {member_no} {crm_url}, old_avatar={old_avatar}")


class TestProc(Processor):
    async def run(self, i):
        # 获取所有的会员信息
        app = self
        items = await app.mgr.execute(MemberInfo.select().where(MemberInfo.avatar.startswith("https://thirdwx")).limit(10).dicts())
        for item in items:
            await asyncio.sleep(0.01)
            old_avatar = item.get("avatar")
            member_no = item.get("member_no")
            body, content_type = encode_multipart_formdata_text(dict(image_url=old_avatar))
            headers = {
                "content-type": content_type
            }
            result = await app.http.post(CRM_URL, obj=None, data=body, headers=headers)
            logger.info(result)
            crm_url = result.get("data", {}).get("crm_url")
            print(f"crm_url={crm_url}")
            await update_member_avatart(app, member_no, crm_url, old_avatar)

    @classmethod
    async def init(cls, loop, cmd_args):
        await super().init(loop, cmd_args)
        from sanic.config import Config
        cls.conf = args = Config()

        def update_config(args, path):
            if not os.path.exists(path):
                return
            args.from_pyfile(path)

        update_config(args, f"../common/conf/{cmd_args.env}.py")
        update_config(args, f"../conf/{cmd_args.env}.py")
        ###
        from peewee_async import PooledMySQLDatabase, Manager
        db = PooledMySQLDatabase(**args.PARAM_FOR_MYSQL)
        db_eros_crm.initialize(db)
        cls.mgr = Manager(db_eros_crm, loop=loop)

        from mtkext.hcp import HttpClientPool
        cls.http = HttpClientPool(loop=loop)

        logger.info('init finish!')


    @classmethod
    async def release(cls):
        await cls.mgr.close()
        await cls.http.close()
        await super().release()

    @classmethod
    async def start(cls, loop, env):
        from argparse import Namespace
        cmd_args = Namespace(env=env)
        await cls.init(loop, cmd_args)
        await cls().run(0)
        await cls.release()


if __name__ == '__main__':
    from common.utils.misc import init_logger

    init_logger(f"test_peewee.log", level="INFO", count=90)
    ###
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="test_peewee")
    parser.add_argument('--env', dest='env',default='test', type=str, required=True, choices=('prod', 'test'))
    cmd_args = parser.parse_args()
    ###
    loop = asyncio.get_event_loop()
    loop.run_until_complete(TestProc.start(loop, cmd_args.env))
    loop.close()

