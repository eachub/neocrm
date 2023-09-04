#!/usr/bin/env python3
# -*- coding: utf-8 -*-

if __name__ == '__main__':
    import logging

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s (%(filename)s:%(lineno)d) %(message)s"))
    handler.setLevel("DEBUG")
    logger = logging.getLogger()
    logger.addHandler(handler)

    from argparse import ArgumentParser

    parser = ArgumentParser(prog="InitDB")
    parser.add_argument('--env', dest='env', type=str,
                        required=True, help='env=prod|test|local')
    parser.add_argument('--check', dest='check_flag', default=False, action='store_true')
    cmd_args = parser.parse_args()
    ###
    from sanic.config import Config

    args = Config()
    args.update_config("conf/" + cmd_args.env + ".py")
    ###
    from peewee import MySQLDatabase
    from models import points, member, analyze, base, coupon, ecom
    from models.base import db_eros_crm
    from models.member import UserTags

    param = dict(args.PARAM_FOR_MYSQL)
    param.pop("max_connections", None)
    db = MySQLDatabase(**param)
    db_eros_crm.initialize(db)
    ###
    from mtkext.db import create_all_tables

    if cmd_args.check_flag:
        from mtkext.check_db import check_all_tables

        check_all_tables(base, [])
        check_all_tables(points, [])
        check_all_tables(member, [UserTags])
        check_all_tables(analyze, [])
        check_all_tables(coupon, [])
        check_all_tables(ecom, [])
    else:
        from mtkext.db import create_all_tables

        create_all_tables(base, [])
        create_all_tables(points, [])
        create_all_tables(member, [UserTags])
        create_all_tables(analyze, [])
        create_all_tables(coupon, [])
        create_all_tables(ecom, [])
