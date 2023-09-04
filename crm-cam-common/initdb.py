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
    cmd_args = parser.parse_args()
    ###
    from sanic.config import Config

    args = Config()
    args.update_config("conf/" + cmd_args.env + ".py")
    ###
    from peewee import MySQLDatabase
    from models import cam
    from models.cam import db_neocam
    from models import event

    param = dict(args.PARAM_FOR_MYSQL)
    param.pop("max_connections", None)
    db = MySQLDatabase(**param)
    db_neocam.initialize(db)
    ###
    from mtkext.db import create_all_tables

    create_all_tables(cam, [cam.LotteryRecord])
    create_all_tables(event, [])
