#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

def init_logger(fname, level=logging.DEBUG, count=90):
    import logging.handlers
    _handler = logging.handlers.TimedRotatingFileHandler(
        fname, when="midnight", interval=1, backupCount=count)
    _handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s (%(filename)s:%(lineno)d) %(message)s"))
    _root = logging.getLogger()
    _root.setLevel(level)  # logging.INFO
    del _root.handlers[:]
    _root.addHandler(_handler)
    return _root

