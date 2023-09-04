# -*- coding: utf-8 -*-

if __name__ == '__main__':
    from sanic.log import set_logger

    set_logger(filename="", level="INFO")
    ###
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="InitDB")
    parser.add_argument('--env', dest='env', type=str, required=True, help='env=prod|test|local')
    parser.add_argument('--check', dest='check_flag', default=False, action='store_true')
    cmd_args = parser.parse_args()
    ###
    from sanic.config import Config

    args = Config()
    args.update_config(f"conf/{cmd_args.env}.py")
    ###
    from peewee import MySQLDatabase

    param = dict(args.PARAM_FOR_MYSQL)
    param.pop("max_connections", None)
    db = MySQLDatabase(**param)
    ###
    import models

    models.db_neocrm_adapt.initialize(db)
    if cmd_args.check_flag:
        from mtkext.check_db import check_all_tables

        check_all_tables(models, [])
    else:
        from mtkext.db import create_all_tables

        create_all_tables(models, [])
